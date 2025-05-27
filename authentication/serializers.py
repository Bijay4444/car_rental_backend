from rest_framework import serializers
from .models import CustomUser
import base64
import uuid
from django.core.files.base import ContentFile
from drf_extra_fields.fields import Base64ImageField 

class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.

    Handles creation of a new user with email, full name, password, optional user image,
    fingerprint authentication toggle, and device info.
    """
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = CustomUser
        fields = ['email', 'full_name', 'password', 'user_image_url', 'is_fingerprint_enabled', 'login_device_info']

    def validate_email(self, value):
        """
        Always return a lowercased email.
        """
        return value.lower()
    
    def create(self, validated_data):
        """
        Create and return a new CustomUser instance.

        Args:
            validated_data (dict): Validated user data.

        Returns:
            CustomUser: The created user instance.
        """
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            full_name=validated_data['full_name'],
            password=validated_data['password'],
            user_image_url=validated_data.get('user_image_url'),
            is_fingerprint_enabled=validated_data.get('is_fingerprint_enabled', False),
            login_device_info=validated_data.get('login_device_info')
        )
        return user

class BiometricToggleSerializer(serializers.ModelSerializer):
    """
    Serializer for toggling biometric (fingerprint) authentication and updating device info.
    """
    class Meta:
        model = CustomUser
        fields = ['is_fingerprint_enabled', 'login_device_info']

class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing user password.

    Validates old password and ensures new passwords match and meet minimum length requirements.
    """
    old_password = serializers.CharField(required=True)
    new_password1 = serializers.CharField(required=True, min_length=8)  # Minimum password length
    new_password2 = serializers.CharField(required=True, min_length=8)
    
class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving and updating user profile information.

    Includes support for base64-encoded user images.
    """
    user_image_url = Base64ImageField(
    required=False,
    allow_null=True,
    max_length=None  # Allow long filenames
    )
     
    class Meta:
        model = CustomUser
        fields = ['email', 'full_name', 'user_image_url']
        read_only_fields = ['email']  

#--------serializer to handle base64 image

class Base64ImageField(serializers.ImageField):
    """
    Custom field to handle base64-encoded image data.
    """
    def to_internal_value(self, data):
        """
        Convert base64 image data to a Django ContentFile.

        Args:
            data (str): Base64-encoded image data.

        Returns:
            ContentFile: Decoded image file.
        """
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')  # Split the data URI
            ext = format.split('/')[-1]  # Extract extension (e.g., 'png')
            
            # Decode the Base64 string
            decoded_file = base64.b64decode(imgstr)
            
            # Generate a unique filename
            file_name = f"{uuid.uuid4()}.{ext}"
            
            # Create a Django ContentFile
            data = ContentFile(decoded_file, name=file_name)
        
        return super().to_internal_value(data)
