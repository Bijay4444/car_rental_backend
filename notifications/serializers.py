from rest_framework import serializers
from .models import NotificationPreference

class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = ['booking', 'payment', 'insurance_expiry', 'car_expiry', 'tracker_expiry']
