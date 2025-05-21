from rest_framework import serializers
from .models import Customer

class CustomerListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for customer list views.

    Returns only key fields for displaying customers in lists.
    """
    class Meta:
        model = Customer
        fields = ['id', 'name', 'status', 'phone_number', 'email']

class CustomerSerializer(serializers.ModelSerializer):
    """
    Full customer serializer with all details.

    Includes fields for images, analytics, and audit information.
    """
    identification_image_url = serializers.SerializerMethodField()
    profile_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Customer
        fields = [
            'id', 'name', 'email', 'phone_number', 'gender', 'date_of_birth', 
            'address', 'status','profile_image', 'profile_image_url', 'identification_image', 'identification_image_url',
            'total_bookings', 'total_spent', 'last_booking_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'total_bookings', 'total_spent', 'last_booking_date',
            'created_at', 'updated_at'
        ]
    
    def get_identification_image_url(self, obj):
        """
        Get the absolute URL for the identification image.

        Args:
            obj (Customer): The customer instance.

        Returns:
            str or None: Absolute URL or None if not available.
        """
        if obj.identification_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.identification_image.url)
        return None

    def get_profile_image_url(self, obj):
        """
        Get the absolute URL for the profile image.

        Args:
            obj (Customer): The customer instance.

        Returns:
            str or None: Absolute URL or None if not available.
        """
        if obj.profile_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_image.url)
        return None
