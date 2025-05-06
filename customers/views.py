from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Customer
from .serializers import CustomerSerializer, CustomerListSerializer

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['name', 'email', 'phone_number']
    ordering_fields = ['name', 'created_at', 'total_bookings', 'total_spent']
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CustomerListSerializer
        return CustomerSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "data": serializer.data,
            "message": "Customers fetched successfully",
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "data": serializer.data,
            "message": "Customer details fetched successfully",
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            "data": serializer.data,
            "message": "Customer added successfully",
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
            "message": "Customer updated successfully",
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            "data": None,
            "message": "Customer deleted successfully",
            "status_code": status.HTTP_204_NO_CONTENT
        }, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'])
    def block(self, request, pk=None):
        customer = self.get_object()
        customer.status = 'Blocked'
        customer.save()
        
        return Response({
            "data": CustomerSerializer(customer, context={'request': request}).data,
            "message": "Customer blocked successfully",
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def unblock(self, request, pk=None):
        customer = self.get_object()
        customer.status = 'Active'
        customer.save()
        
        return Response({
            "data": CustomerSerializer(customer, context={'request': request}).data,
            "message": "Customer unblocked successfully",
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        queryset = self.filter_queryset(
            self.get_queryset().filter(status='Active')
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "data": serializer.data,
            "message": "Active customers fetched successfully",
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def blocked(self, request):
        queryset = self.filter_queryset(
            self.get_queryset().filter(status='Blocked')
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "data": serializer.data,
            "message": "Blocked customers fetched successfully",
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def bookings(self, request, pk=None):
        from bookings.models import Booking
        from bookings.serializers import BookingListSerializer
        
        customer = self.get_object()
        bookings = Booking.objects.filter(customer=customer)
        serializer = BookingListSerializer(bookings, many=True)
        
        return Response({
            "data": serializer.data,
            "message": f"Bookings for {customer.name} fetched successfully",
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get customer booking history and stats"""
        customer = self.get_object()
        customer.update_booking_stats()  # Update stats before returning
        
        from bookings.models import Booking
        from bookings.serializers import BookingListSerializer
        
        # Get recent bookings
        recent_bookings = Booking.objects.filter(customer=customer).order_by('-created_at')[:5]
        booking_serializer = BookingListSerializer(recent_bookings, many=True)
        
        # Customer details with updated stats
        customer_serializer = self.get_serializer(customer)
        
        return Response({
            "data": {
                "customer": customer_serializer.data,
                "recent_bookings": booking_serializer.data,
                "stats": {
                    "total_bookings": customer.total_bookings,
                    "total_spent": float(customer.total_spent),
                    "last_booking_date": customer.last_booking_date
                }
            },
            "message": "Customer history fetched successfully",
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)
