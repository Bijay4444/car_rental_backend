from rest_framework import serializers
from .models import Car, CarDeleteReason

class CarSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed car representation.

    Includes all fields and a read-only field for the creator's name.
    """
    created_by_name = serializers.ReadOnlyField(source='created_by.full_name')
    
    class Meta:
        model = Car
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'deleted_at', 'deleted_by']

class CarListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing cars.

    Returns only key fields for list views.
    """
    class Meta:
        model = Car
        fields = ['id', 'car_name', 'car_image', 'fee', 'type', 'status', 'availability']


class CarDeleteReasonSerializer(serializers.ModelSerializer):
    """
    Serializer for car deletion reasons.

    Used to record and display reasons for car deletions.
    """
    class Meta:
        model = CarDeleteReason
        fields = '__all__'
        read_only_fields = ['car', 'deleted_at', 'deleted_by']
