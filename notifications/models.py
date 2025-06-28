from django.db import models
from django.conf import settings

class NotificationPreference(models.Model):
    """
    Model representing a user's notification preferences.

    Stores which types of notifications the user wants to receive.

    Attributes:
        user (User): The user these preferences belong to.
        booking (bool): Receive booking notifications.
        payment (bool): Receive payment notifications.
        insurance_expiry (bool): Receive insurance expiry notifications.
        car_expiry (bool): Receive car expiry notifications.
        tracker_expiry (bool): Receive tracker expiry notifications.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_preference')
    booking = models.BooleanField(default=True)
    payment = models.BooleanField(default=True)
    insurance_expiry = models.BooleanField(default=True)
    car_expiry = models.BooleanField(default=False)
    tracker_expiry = models.BooleanField(default=False)

    def __str__(self):
        """
        Return a string representation of the user's notification preferences.

        Returns:
            str: Username and preferences.
        """
        return f"{self.user.username}'s notification preferences"


class NotificationToken(models.Model):
    """
    Model for storing a user's FCM (Firebase Cloud Messaging) token.

    Attributes:
        user (User): The user this token belongs to.
        token (str): The FCM token.
        created_at (datetime): When the token was created.
        updated_at (datetime): When the token was last updated.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.TextField()
    device_type = models.CharField(max_length=20, default='mobile')
    platform = models.CharField(max_length=10, default='unknown')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['token']  # Only token needs to be unique globally

    def __str__(self):
        return f"{self.user.email} - {self.device_type} ({self.token[:20]}...)"