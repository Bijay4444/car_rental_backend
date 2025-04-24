from django.db import models
from django.contrib.auth.models import AbstractUser
from .managers import CustomUserManager  

# Create your models here.
class CustomUser(AbstractUser):
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
        return self.email
