from rest_framework import serializers
from .models import Booking, Payment, BookingExtension
from cars.serializers import CarListSerializer
from customers.serializers import CustomerSerializer
from django.utils import timezone

class BookingExtensionSerializer(serializers.ModelSerializer):
    """
    Serializer for booking extensions.

    Includes all fields and marks booking, created_at, and created_by as read-only.
    """
    class Meta:
        model = BookingExtension
        fields = '__all__'
        read_only_fields = ['booking', 'created_at', 'created_by']

class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for booking payments.

    Includes all fields and marks created_at and created_by as read-only.
    """
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['created_at', 'created_by']

class BookingSerializer(serializers.ModelSerializer):
    """
    Full serializer for booking details.

    Includes related customer, car, payments, extensions, and calculated fields.
    """
    customer_details = CustomerSerializer(source='customer', read_only=True)
    car_details = CarListSerializer(source='car', read_only=True)
    original_car_details = CarListSerializer(source='original_car', read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    extensions = BookingExtensionSerializer(many=True, read_only=True)
    duration_days = serializers.IntegerField(source='get_duration_days', read_only=True)
    remaining_balance = serializers.SerializerMethodField()
    has_accident = serializers.BooleanField(required=False)
    accident_description = serializers.CharField(required=False, allow_blank=True)
    accident_date = serializers.DateField(required=False)
    accident_charges = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False
    )
    
    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ['booking_id', 'created_at', 'created_by', 'updated_at']
        extra_kwargs = {
            'car': {'required': False},
            'pickup_time': {'required': False, 'allow_null': True},
            'dropoff_time': {'required': False, 'allow_null': True},
            'subtotal': {'required': False, 'allow_null': True},
            'total_amount': {'required': False, 'allow_null': True},
        }

    def get_remaining_balance(self, obj):
        """
        Calculate the remaining balance for the booking.

        Returns:
            Decimal: Remaining amount to be paid.
        """
        return obj.total_amount - obj.paid_amount
    
    def validate(self, data):
        """
        Validate booking dates and prevent double-booking.

        Raises:
            ValidationError: If dates are invalid or car is double-booked.
        """
        # Validate start_date and end_date
        if 'start_date' in data and 'end_date' in data:
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError("End date must be after start date")
            
            # Check if start_date is in the past
            if data['start_date'] < timezone.now().date():
                raise serializers.ValidationError("Start date cannot be in the past")
        
        
        # --- Double-booking validation ---
        car = data.get('car') or getattr(self.instance, 'car', None)
        start_date = data.get('start_date') or getattr(self.instance, 'start_date', None)
        end_date = data.get('end_date') or getattr(self.instance, 'end_date', None)
        booking_id = self.instance.id if self.instance else None

        if car and start_date and end_date:
            overlapping = Booking.objects.filter(
                car=car,
                start_date__lt=end_date,
                end_date__gt=start_date,
            ).exclude(id=booking_id)
            
            if overlapping.exists():
                raise serializers.ValidationError("Car is already booked for the selected dates.")
        return data
    
    def create(self, validated_data):
        """
        Create a new booking instance.

        Calculates subtotal and total amount based on car and dates.
        """
        car = validated_data.get('car')
        if car:
            delta = (validated_data['end_date'] - validated_data['start_date']).days
            validated_data['subtotal'] = car.fee * delta
            tax = validated_data.get('tax', 0)
            discount = validated_data.get('discount', 0)
            validated_data['total_amount'] = validated_data['subtotal'] + tax - discount
        else:
            # Set defaults for reserved bookings
            validated_data['subtotal'] = 0
            validated_data['total_amount'] = 0
            validated_data['booking_status'] = 'Reserved'
            validated_data['pickup_time'] = validated_data.get('pickup_time', None)
            validated_data['dropoff_time'] = validated_data.get('dropoff_time', None)
        
        return super().create(validated_data)

class BookingListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing bookings.

    Returns only key fields for list views, including customer and car info.
    """
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_address = serializers.CharField(source='customer.address', read_only=True)
    duration_days = serializers.IntegerField(source='get_duration_days', read_only=True)
    car_name = serializers.SerializerMethodField(read_only=True)
    car_image = serializers.SerializerMethodField(read_only=True)
    pickup_time = serializers.TimeField(read_only=True)
    dropoff_time = serializers.TimeField(read_only=True)

    def get_car_name(self, obj):
        """
        Get the car name for the booking.

        Returns:
            str or None: Car name or None if not available.
        """
        return obj.car.car_name if obj.car else None
    
    def get_car_image(self, obj):
        """
        Get the car image URL for the booking.

        Returns:
            str or None: Absolute URL or None if not available.
        """
        if obj.car and obj.car.car_image:
            request = self.context.get('request')
            url = obj.car.car_image.url
            if request is not None:
                return request.build_absolute_uri(url)
            return url
        return None

    class Meta:
        model = Booking
        fields = ['id', 'booking_id', 'customer_name', 'customer_address', 'car_name',
                  'car_image', 'start_date', 'end_date', 'pickup_time',
                   'dropoff_time', 'booking_status','payment_status', 
                  'total_amount', 'paid_amount', 'duration_days']

class BookingSwapSerializer(serializers.Serializer):
    """
    Serializer for swapping cars in a booking.

    Fields:
        new_car_id (int): ID of the replacement car.
        reason (str): Reason for swapping.
    """
    new_car_id = serializers.IntegerField()
    reason = serializers.CharField(max_length=100)

class BookingExtendSerializer(serializers.Serializer):
    """
    Serializer for extending a booking.

    Fields:
        new_end_date (date): New end date.
        extension_fee (Decimal): Fee for extension.
        reason (str): Reason for extension.
        remarks (str): Additional remarks.
    """
    new_end_date = serializers.DateField()
    extension_fee = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True)
    remarks = serializers.CharField(required=False, allow_blank=True)
    
    def validate_new_end_date(self, value):
        """
        Validate that the new end date is after the current end date.

        Raises:
            ValidationError: If new end date is not after current.
        """
        booking_id = self.context.get('booking_id')
        if booking_id:
            booking = Booking.objects.get(id=booking_id)
            if value <= booking.end_date:
                raise serializers.ValidationError("New end date must be after current end date")
        return value

class AccidentReportSerializer(serializers.Serializer):
    """
    Serializer for reporting an accident during a booking.

    Fields:
        has_accident (bool): Whether an accident occurred.
        accident_description (str): Description of the accident.
        accident_date (date): Date of the accident.
        accident_charges (Decimal): Charges due to accident.
        new_car_id (int, optional): ID of replacement car if needed.
    """
    has_accident = serializers.BooleanField(required=True)
    accident_description = serializers.CharField(required=True)
    accident_date = serializers.DateField(required=True)
    accident_charges = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=True
    )
    new_car_id = serializers.IntegerField(required=False)