# from rest_framework import viewsets, status, filters
# from rest_framework.response import Response
# from rest_framework.decorators import action
# from rest_framework.permissions import IsAuthenticated
# from django_filters.rest_framework import DjangoFilterBackend

# from .models import Car, Booking
# from .serializers import (
#     CarSerializer, CarListSerializer, CarDeleteSerializer,
#     CarBulkDeleteSerializer, CarSwapSerializer, BookingSerializer
# )

# class CarViewSet(viewsets.ModelViewSet):
#     queryset = Car.objects.all()
#     permission_classes = [IsAuthenticated]
#     filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
#     filterset_fields = ['status', 'availability', 'type', 'gearbox']
#     search_fields = ['car_name', 'color']
#     ordering_fields = ['fee', 'car_name']

#     def get_serializer_class(self):
#         if self.action == 'list':
#             return CarListSerializer
#         return CarSerializer

#     def list(self, request, *args, **kwargs):
#         queryset = self.filter_queryset(self.get_queryset())
#         page = self.paginate_queryset(queryset)
#         serializer = self.get_serializer(page if page is not None else queryset, many=True)
#         response = self.get_paginated_response(serializer.data) if page is not None else Response({
#             "data": serializer.data,
#             "message": "Cars retrieved successfully",
#             "status_code": status.HTTP_200_OK
#         })
#         return response

#     def retrieve(self, request, *args, **kwargs):
#         instance = self.get_object()
#         serializer = self.get_serializer(instance)
#         return Response({
#             "data": serializer.data,
#             "message": "Car details retrieved successfully",
#             "status_code": status.HTTP_200_OK
#         })

#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         self.perform_create(serializer)
#         return Response({
#             "data": serializer.data,
#             "message": "Car added successfully",
#             "status_code": status.HTTP_201_CREATED
#         }, status=status.HTTP_201_CREATED)

#     def update(self, request, *args, **kwargs):
#         partial = kwargs.pop('partial', False)
#         instance = self.get_object()
#         serializer = self.get_serializer(instance, data=request.data, partial=partial)
#         serializer.is_valid(raise_exception=True)
#         self.perform_update(serializer)
#         return Response({
#             "data": serializer.data,
#             "message": "Car updated successfully",
#             "status_code": status.HTTP_200_OK
#         })

#     def destroy(self, request, *args, **kwargs):
#         """Delete a car with reason and handle bookings if necessary."""
#         instance = self.get_object()
#         reason_serializer = CarDeleteSerializer(data=request.data)
#         reason_serializer.is_valid(raise_exception=True)
#         # If there are active bookings, prevent deletion or require swap
#         active_bookings = Booking.objects.filter(car=instance, end_date__gte='today')
#         if active_bookings.exists():
#             return Response({
#                 "data": None,
#                 "message": "Car has active/future bookings. Please swap bookings before deleting.",
#                 "status_code": status.HTTP_400_BAD_REQUEST
#             }, status=status.HTTP_400_BAD_REQUEST)
#         self.perform_destroy(instance)
#         return Response({
#             "data": None,
#             "message": f"Car deleted successfully. Reason: {reason_serializer.validated_data['reason']}",
#             "status_code": status.HTTP_200_OK
#         })

#     @action(detail=False, methods=['post'])
#     def bulk_delete(self, request):
#         serializer = CarBulkDeleteSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         car_ids = serializer.validated_data['car_ids']
#         reason = serializer.validated_data['reason']
#         cars = Car.objects.filter(id__in=car_ids)
#         if cars.count() != len(car_ids):
#             return Response({
#                 "data": None,
#                 "message": "One or more cars not found.",
#                 "status_code": status.HTTP_404_NOT_FOUND
#             }, status=status.HTTP_404_NOT_FOUND)
#         # Check for bookings
#         booked_cars = cars.filter(status='Booked')
#         if booked_cars.exists():
#             return Response({
#                 "data": None,
#                 "message": "Cannot delete cars that are currently booked.",
#                 "status_code": status.HTTP_400_BAD_REQUEST
#             }, status=status.HTTP_400_BAD_REQUEST)
#         count = cars.delete()[0]
#         return Response({
#             "data": {"deletion_count": count},
#             "message": f"{count} cars deleted successfully. Reason: {reason}",
#             "status_code": status.HTTP_200_OK
#         })

#     @action(detail=True, methods=['post'])
#     def swap_bookings(self, request, pk=None):
#         """Swap bookings to another car before deletion."""
#         car = self.get_object()
#         serializer = CarSwapSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         swap_to_car_id = serializer.validated_data['swap_to_car_id']
#         booking_ids = serializer.validated_data['booking_ids']
#         try:
#             swap_car = Car.objects.get(id=swap_to_car_id, availability='Available')
#         except Car.DoesNotExist:
#             return Response({
#                 "data": None,
#                 "message": "Swap-to car not found or not available.",
#                 "status_code": status.HTTP_404_NOT_FOUND
#             }, status=status.HTTP_404_NOT_FOUND)
#         # Update bookings
#         updated = Booking.objects.filter(id__in=booking_ids, car=car).update(car=swap_car)
#         return Response({
#             "data": {"updated_bookings": updated},
#             "message": f"{updated} bookings swapped to car {swap_car.car_name}.",
#             "status_code": status.HTTP_200_OK
#         })

# class BookingViewSet(viewsets.ModelViewSet):
#     queryset = Booking.objects.all()
#     serializer_class = BookingSerializer
#     permission_classes = [IsAuthenticated]
#     filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
#     filterset_fields = ['customer', 'car', 'payment_status']
#     ordering_fields = ['start_date', 'end_date']

#     def perform_create(self, serializer):
#         booking = serializer.save()
#         car = booking.car
#         car.availability = 'Booked'
#         car.status = 'Booked'
#         car.save()

#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         self.perform_create(serializer)
#         return Response({
#             "data": serializer.data,
#             "message": "Booking created successfully",
#             "status_code": status.HTTP_201_CREATED
#         }, status=status.HTTP_201_CREATED)
