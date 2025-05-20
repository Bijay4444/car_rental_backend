from django.db import models
from django.conf import settings

class NotificationPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_preference')
    booking = models.BooleanField(default=True)
    payment = models.BooleanField(default=True)
    insurance_expiry = models.BooleanField(default=True)
    car_expiry = models.BooleanField(default=False)
    tracker_expiry = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s notification preferences"


class NotificationToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)