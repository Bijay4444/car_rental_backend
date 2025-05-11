from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Car, CarDeleteReason
from .serializers import CarSerializer, CarListSerializer, CarDeleteReasonSerializer
from .filters import CarFilter
from django.utils import timezone
from bookings.models import Booking

class CarViewSet(viewsets.ModelViewSet):
    queryset = Car.objects.filter(is_deleted=False)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CarFilter
    search_fields = ['car_name', 'type', 'color']
    ordering_fields = ['car_name', 'fee', 'created_at']
    permission_classes = [IsAuthenticated]  # Require login for all car actions

    def get_serializer_class(self):
        if self.action == 'list':
            return CarListSerializer
        return CarSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "data": serializer.data,
            "message": "Car list fetched successfully",
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        car = self.get_object()
        serializer = self.get_serializer(car)
        return Response({
            "data": serializer.data,
            "message": "Car detail fetched successfully",
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            "data": serializer.data,
            "message": "Car created successfully",
            "status_code": status.HTTP_201_CREATED
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            "data": serializer.data,
            "message": "Car updated successfully",
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        car = self.get_object()
        car.soft_delete(user=request.user)
        return Response({
            "data": None,
            "message": "Car deleted successfully",
            "status_code": status.HTTP_204_NO_CONTENT
        }, status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=['post'])
    def delete_with_reason(self, request, pk=None):
        car = self.get_object()
        serializer = CarDeleteReasonSerializer(data=request.data)
        if serializer.is_valid():
            reason = serializer.validated_data.get('reason')
            description = serializer.validated_data.get('description')
            car.soft_delete(
                user=request.user,
                reason=reason,
                description=description
            )
            return Response({
                "data": None,
                "message": f"Car {car.car_name} has been deleted.",
                "status_code": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)
        return Response({
            "data": None,
            "message": "Invalid data",
            "status_code": status.HTTP_400_BAD_REQUEST
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def deleted(self, request):
        queryset = Car.objects.filter(is_deleted=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "data": serializer.data,
            "message": "Deleted cars fetched successfully",
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def available(self, request):
        queryset = self.filter_queryset(
            Car.objects.filter(availability='Available', status='Active')
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "data": serializer.data,
            "message": "Available cars fetched successfully",
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], url_path='swap_and_delete')
    def swap_and_delete(self, request, pk=None):
        """
        Swap this car out of all active bookings and soft-delete it.
        Expects: { "new_car_id": <int>, "reason": <str>, "description": <str> }
        """
        car = self.get_object()
        new_car_id = request.data.get('new_car_id')
        reason = request.data.get('reason')
        description = request.data.get('description', '')

        # Validate new_car_id
        if not new_car_id:
            return Response({
                "data": None,
                "message": "new_car_id is required.",
                "status_code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            new_car = Car.objects.get(id=new_car_id, is_deleted=False, availability='Available', status='Active')
        except Car.DoesNotExist:
            return Response({
                "data": None,
                "message": "Replacement car not found or not available.",
                "status_code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)

        # Find all active bookings for this car
        affected_bookings = Booking.objects.filter(car=car, booking_status='Active')

        # Swap car in all bookings
        for booking in affected_bookings:
            booking.original_car = booking.car
            booking.car = new_car
            booking.has_been_swapped = True
            booking.swap_date = timezone.now().date()
            booking.swap_reason = f"Car swapped due to: {reason}"
            booking.save()

        # Soft-delete the old car and record the reason
        car.soft_delete(user=request.user, reason=reason, description=description)

        # Optionally, update new car's status/availability
        new_car.status = 'Booked'
        new_car.availability = 'Booked'
        new_car.save()

        return Response({
            "data": {
                "swapped_bookings": [b.id for b in affected_bookings],
                "deleted_car_id": car.id,
                "replacement_car_id": new_car.id
            },
            "message": f"Car {car.car_name} has been swapped out from {affected_bookings.count()} bookings and deleted.",
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)
