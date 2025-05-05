from rest_framework import serializers
from .models import Car, CarDeleteReason

class CarSerializer(serializers.ModelSerializer):
    created_by_name = serializers.ReadOnlyField(source='created_by.full_name')
    
    class Meta:
        model = Car
        fields = '__all__'
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['insurance_info'] = {
            'collision_damage_waiver': instance.collision_damage_waiver,
            'third_party_liability_insurance': instance.third_party_liability_insurance,
            'optional_insurance_add_ons': instance.optional_insurance_add_ons,
            'insurance_expiry_date': instance.insurance_expiry_date,
        }
        representation['specifications'] = {
            'color': instance.color,
            'seats': instance.seats,
            'mileage': instance.mileage,
            'type': instance.type,
            'gearbox': instance.gearbox,
            'max_speed': instance.max_speed,
        }
        return representation


class CarListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list view"""
    class Meta:
        model = Car
        fields = ['id', 'car_name', 'car_image', 'fee', 'type', 'status', 'availability']


class CarDeleteReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarDeleteReason
        fields = '__all__'
        read_only_fields = ['car', 'deleted_at', 'deleted_by']
