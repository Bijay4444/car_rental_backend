from rest_framework import serializers
from .models import NotificationPreference

class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for user notification preferences.

    Allows retrieving and updating notification settings for bookings, payments, and expiries.
    """
    class Meta:
        model = NotificationPreference
        fields = ['booking', 'payment', 'insurance_expiry', 'car_expiry', 'tracker_expiry']
