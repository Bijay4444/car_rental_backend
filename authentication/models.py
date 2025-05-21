from django.db import models
from django.contrib.auth.models import AbstractUser
from .managers import CustomUserManager  

# Create your models here.
class CustomUser(AbstractUser):
    """
    Custom user model for authentication.

    Extends Django's AbstractUser to use email as the unique identifier instead of username.
    Adds fields for full name, user image, fingerprint authentication, and device info.

    Attributes:
        email (str): Unique email address for the user.
        full_name (str): Full name of the user.
        user_image_url (ImageField): Optional user profile image.
        is_fingerprint_enabled (bool): Whether fingerprint authentication is enabled.
        login_device_info (JSONField): Device information for login (optional).
    """
    username = None  # Remove username, use email instead
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150)
    user_image_url = models.ImageField(upload_to='user_images/', blank=True, null=True)
    is_fingerprint_enabled = models.BooleanField(default=False)
    login_device_info = models.JSONField(blank=True, null=True)  # Requires PostgreSQL or Django 3.1+
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']
    
    objects = CustomUserManager()  # From manager defined in managers.py

    def __str__(self):
        """
        Return the string representation of the user.

        Returns:
            str: The user's email address.
        """
        return self.email
