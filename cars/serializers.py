# from rest_framework import serializers
# from .models import Car, Booking

# class CarListSerializer(serializers.ModelSerializer):
#     """Simplified serializer for car listings and filters."""
#     car_image = serializers.ImageField(read_only=True)

#     class Meta:
#         model = Car
#         fields = [
#             'id', 'car_image', 'car_name', 'fee', 'status', 'availability', 'type'
#         ]

# class CarSerializer(serializers.ModelSerializer):
#     """Full serializer for car details, add, and update."""
#     car_image = serializers.ImageField(required=False, allow_null=True)

#     class Meta:
#         model = Car
#         fields = '__all__'

#     def validate_tracker_expiry_date(self, value):
#         from django.utils import timezone
#         if value < timezone.now().date():
#             raise serializers.ValidationError("Tracker expiry date cannot be in the past.")
#         return value

#     def validate_insurance_expiry_date(self, value):
#         from django.utils import timezone
#         if value < timezone.now().date():
#             raise serializers.ValidationError("Insurance expiry date cannot be in the past.")
#         return value

# class CarDeleteSerializer(serializers.Serializer):
#     REASON_CHOICES = [
#         ('Accident', 'Accident'),
#         ('Maintenance', 'Maintenance'),
#         ('Expired Insurance', 'Expired Insurance'),
#         ('Others', 'Others'),
#     ]
#     reason = serializers.ChoiceField(choices=REASON_CHOICES)

# class CarBulkDeleteSerializer(serializers.Serializer):
#     car_ids = serializers.ListField(child=serializers.IntegerField())
#     reason = serializers.ChoiceField(choices=CarDeleteSerializer.REASON_CHOICES)

# class CarSwapSerializer(serializers.Serializer):
#     """For swapping bookings to another car before deletion."""
#     swap_to_car_id = serializers.IntegerField()
#     booking_ids = serializers.ListField(child=serializers.IntegerField())

# class BookingSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Booking
#         fields = '__all__'

#     def validate(self, data):
#         if data['end_date'] < data['start_date']:
#             raise serializers.ValidationError("End date must be after start date.")
#         car = data['car']
#         if car.availability != 'Available':
#             raise serializers.ValidationError(f"Car is not available. Current status: {car.availability}")
#         return data
