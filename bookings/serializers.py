from rest_framework import serializers
from .models import Booking, Payment, BookingExtension
from cars.serializers import CarListSerializer
from customers.serializers import CustomerSerializer
from django.utils import timezone

class BookingExtensionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingExtension
        fields = '__all__'
        read_only_fields = ['booking', 'created_at', 'created_by']

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['created_at', 'created_by']

class BookingSerializer(serializers.ModelSerializer):
    customer_details = CustomerSerializer(source='customer', read_only=True)
    car_details = CarListSerializer(source='car', read_only=True)
    original_car_details = CarListSerializer(source='original_car', read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    extensions = BookingExtensionSerializer(many=True, read_only=True)
    duration_days = serializers.IntegerField(source='get_duration_days', read_only=True)
    remaining_balance = serializers.SerializerMethodField()
    
    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ['booking_id', 'created_at', 'created_by', 'updated_at']
    
    def get_remaining_balance(self, obj):
        return obj.total_amount - obj.paid_amount
    
    def validate(self, data):
        # Validate start_date and end_date
        if 'start_date' in data and 'end_date' in data:
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError("End date must be after start date")
            
            # Check if start_date is in the past
            if data['start_date'] < timezone.now().date():
                raise serializers.ValidationError("Start date cannot be in the past")
        
        return data
    
    def create(self, validated_data):
        # Calculate subtotal and total automatically
        if 'start_date' in validated_data and 'end_date' in validated_data and 'car' in validated_data:
            delta = (validated_data['end_date'] - validated_data['start_date']).days
            validated_data['subtotal'] = validated_data['car'].fee * delta
            
            # Calculate total with tax and discount
            tax = validated_data.get('tax', 0)
            discount = validated_data.get('discount', 0)
            validated_data['total_amount'] = validated_data['subtotal'] + tax - discount
        
        return super().create(validated_data)

class BookingListSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    car_name = serializers.CharField(source='car.car_name', read_only=True)
    duration_days = serializers.IntegerField(source='get_duration_days', read_only=True)
    
    class Meta:
        model = Booking
        fields = ['id', 'booking_id', 'customer_name', 'car_name', 'start_date', 
                  'end_date', 'booking_status', 'payment_status', 'total_amount', 
                  'paid_amount', 'duration_days']

class BookingSwapSerializer(serializers.Serializer):
    new_car_id = serializers.IntegerField()
    reason = serializers.CharField(max_length=100)

class BookingExtendSerializer(serializers.Serializer):
    new_end_date = serializers.DateField()
    extension_fee = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True)
    remarks = serializers.CharField(required=False, allow_blank=True)
    
    def validate_new_end_date(self, value):
        booking_id = self.context.get('booking_id')
        if booking_id:
            booking = Booking.objects.get(id=booking_id)
            if value <= booking.end_date:
                raise serializers.ValidationError("New end date must be after current end date")
        return value
