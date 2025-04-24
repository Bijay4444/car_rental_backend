from rest_framework import serializers
from .models import CustomUser

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = CustomUser
        fields = ['email', 'full_name', 'password', 'user_image_url', 'is_fingerprint_enabled', 'login_device_info']

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            full_name=validated_data['full_name'],
            password=validated_data['password'],
            user_image_url=validated_data.get('user_image_url'),
            is_fingerprint_enabled=validated_data.get('is_fingerprint_enabled', False),
            login_device_info=validated_data.get('login_device_info')
        )
        return user
