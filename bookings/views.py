from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q
from .models import Booking, Payment, BookingExtension
from .serializers import (
    BookingSerializer, BookingListSerializer, PaymentSerializer,
    BookingExtensionSerializer, BookingSwapSerializer, BookingExtendSerializer,
    AccidentReportSerializer
)
from cars.models import Car
from core.utils import extract_error_message

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all().select_related('customer', 'car', 'original_car', 'created_by')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['booking_status', 'payment_status', 'car_returned']
    search_fields = ['booking_id', 'customer__name', 'car__car_name']
    ordering_fields = ['start_date', 'end_date', 'created_at', 'total_amount']
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return BookingListSerializer
        return BookingSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date and end_date:
            queryset = queryset.filter(
                Q(start_date__lte=end_date) & Q(end_date__gte=start_date)
            )
        
        # Filter by customer if provided
        customer_id = self.request.query_params.get('customer_id')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        
        # Filter by car if provided
        car_id = self.request.query_params.get('car_id')
        if car_id:
            queryset = queryset.filter(car_id=car_id)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "data": serializer.data,
            "message": "Bookings fetched successfully",
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "data": serializer.data,
            "message": "Booking details fetched successfully",
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as exc:
            return Response({
                "data": None,
                "message": extract_error_message(exc.detail),
                "status_code": 409
            }, status=409)
        booking = serializer.save(created_by=self.request.user)

        # Only update car if it exists
        if booking.car:
            car = booking.car
            car.availability = 'Booked'
            car.status = 'Booked'
            car.save(update_fields=['availability', 'status'])

        return Response({
            "data": serializer.data,
            "message": "Booking created successfully",
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
            "message": "Booking updated successfully",
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def swap_car(self, request, pk=None):
        booking = self.get_object()
        serializer = BookingSwapSerializer(data=request.data)
        
        if serializer.is_valid():
            new_car_id = serializer.validated_data['new_car_id']
            reason = serializer.validated_data['reason']
            
            try:
                new_car = Car.objects.get(id=new_car_id, is_deleted=False, availability='Available')
            except Car.DoesNotExist:
                return Response({
                    "data": None,
                    "message": "Replacement car not found or not available",
                    "status_code": status.HTTP_400_BAD_REQUEST
                }, status=status.HTTP_400_BAD_REQUEST)
                
            booking.swap_car(new_car, reason)
            
            return Response({
                "data": BookingSerializer(booking).data,
                "message": f"Car swapped successfully to {new_car.car_name}",
                "status_code": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)
            
        return Response({
            "data": None,
            "message": "Invalid data",
            "status_code": status.HTTP_400_BAD_REQUEST
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def extend_booking(self, request, pk=None):
        booking = self.get_object()
        serializer = BookingExtendSerializer(
            data=request.data, 
            context={'booking_id': booking.id}
        )
        
        if serializer.is_valid():
            new_end_date = serializer.validated_data['new_end_date']
            extension_fee = serializer.validated_data['extension_fee']
            reason = serializer.validated_data.get('reason', '')
            remarks = serializer.validated_data.get('remarks', '')
            
            booking.extend(
                new_end_date=new_end_date,
                extension_fee=extension_fee,
                reason=reason,
                remarks=remarks,
                user=request.user
            )
            
            return Response({
                "data": BookingSerializer(booking).data,
                "message": "Booking extended successfully",
                "status_code": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)
            
        return Response({
            "data": None,
            "message": "Invalid data",
            "status_code": status.HTTP_400_BAD_REQUEST
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def mark_as_returned(self, request, pk=None):
        booking = self.get_object()
        actual_return_date = request.data.get('actual_return_date', timezone.now().date())
        
        if booking.car_returned:
            return Response({
                "data": None,
                "message": "Car was already marked as returned",
                "status_code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)
            
        booking.car_returned = True
        booking.booking_status = 'Returned'
        booking.actual_return_date = actual_return_date
        booking.save()
        
        # Update car availability
        car = booking.car
        car.availability = 'Available'
        car.status = 'Active'
        car.save()
        
        return Response({
            "data": BookingSerializer(booking).data,
            "message": "Car marked as returned successfully",
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        queryset = self.filter_queryset(
            self.get_queryset().filter(booking_status='Active')
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "data": serializer.data,
            "message": "Active bookings fetched successfully",
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)
        
    @action(detail=False, methods=['get'], url_path='reserved')
    def reserved(self, request):
        # Filter for reserved bookings
        bookings = self.get_queryset().filter(booking_status='Reserved')
        serializer = self.get_serializer(bookings, many=True)
        return Response({
            "data": serializer.data,
            "message": "Reserved bookings fetched successfully",
            "status_code": status.HTTP_200_OK
        })
    
    @action(detail=False, methods=['get'])
    def today_pickups(self, request):
        today = timezone.now().date()
        queryset = self.filter_queryset(
            self.get_queryset().filter(start_date=today, booking_status='Active')
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "data": serializer.data,
            "message": "Today's pickups fetched successfully",
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def today_returns(self, request):
        today = timezone.now().date()
        queryset = self.filter_queryset(
            self.get_queryset().filter(end_date=today, booking_status='Active', car_returned=False)
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "data": serializer.data,
            "message": "Today's returns fetched successfully",
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)

    # report_accident action
    @action(detail=True, methods=['post'])
    def report_accident(self, request, pk=None):
        booking = self.get_object()
        serializer = AccidentReportSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                "data": None,
                "message": serializer.errors,
                "status_code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)

        # Update accident fields
        booking.has_accident = serializer.validated_data['has_accident']
        booking.accident_description = serializer.validated_data['accident_description']
        booking.accident_date = serializer.validated_data['accident_date']
        booking.accident_charges = serializer.validated_data['accident_charges']
        booking.save()

        # Handle car swap if requested
        new_car_id = serializer.validated_data.get('new_car_id')
        if new_car_id:
            try:
                new_car = Car.objects.get(
                    id=new_car_id, 
                    is_deleted=False, 
                    availability='Available'
                )
                booking.swap_car(new_car, "Accident replacement")
            except Car.DoesNotExist:
                return Response({
                    "data": None,
                    "message": "Replacement car not found or not available",
                    "status_code": status.HTTP_400_BAD_REQUEST
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "data": BookingSerializer(booking).data,
            "message": "Accident reported successfully",
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)
        

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        if booking.booking_status == 'Cancelled':
            return Response({
                "data": None,
                "message": "Booking is already cancelled",
                "status_code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Optionally: Only allow cancel if not already returned or cancelled
        if booking.booking_status in ['Returned', 'Cancelled']:
            return Response({
                "data": None,
                "message": f"Cannot cancel a booking with status '{booking.booking_status}'",
                "status_code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)

        booking.booking_status = 'Cancelled'
        booking.save(update_fields=['booking_status'])

        # If there is a car assigned and it's not returned, make it available again
        if booking.car and not booking.car_returned:
            car = booking.car
            car.availability = 'Available'
            car.status = 'Active'
            car.save(update_fields=['availability', 'status'])

        return Response({
            "data": BookingSerializer(booking).data,
            "message": "Booking cancelled successfully",
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)



class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all().select_related('booking', 'created_by')
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['booking', 'payment_method', 'is_successful']
    ordering_fields = ['payment_date', 'amount']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
        
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "data": serializer.data,
            "message": "Payments fetched successfully",
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "data": serializer.data,
            "message": "Payment details fetched successfully",
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            "data": serializer.data,
            "message": "Payment recorded successfully",
            "status_code": status.HTTP_201_CREATED
        }, status=status.HTTP_201_CREATED)

class BookingExtensionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BookingExtension.objects.all().select_related('booking', 'created_by')
    serializer_class = BookingExtensionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['booking']
    ordering_fields = ['created_at']
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "data": serializer.data,
            "message": "Booking extensions fetched successfully",
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "data": serializer.data,
            "message": "Booking extension details fetched successfully",
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)
        
    
