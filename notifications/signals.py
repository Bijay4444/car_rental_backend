from django.db.models.signals import post_save
from django.dispatch import receiver
from bookings.models import Booking
from notifications.models import NotificationToken
from notifications.firebase import generate_firebase_auth_key, send_push_notification
from payments.models import Payment

# for booking notification
@receiver(post_save, sender=Booking)
def notify_on_booking(sender, instance, created, **kwargs):
    user = instance.customer.user
    try:
        pref = user.notification_preference
        token_obj = NotificationToken.objects.get(user=user)
        auth_token = generate_firebase_auth_key()
        if created and pref.booking:
            send_push_notification(
                auth_token,
                token_obj.token,
                title="Booking Confirmed",
                body=f"Your booking for {instance.car} is confirmed!",
                data={"booking_id": str(instance.id)}
            )
        # Notify on status changes
        elif not created:
            if instance.status == 'Returned' and pref.booking:
                send_push_notification(
                    auth_token,
                    token_obj.token,
                    title="Car Returned",
                    body=f"Your booking for {instance.car} is marked as returned.",
                    data={"booking_id": str(instance.id)}
                )
            elif instance.status == 'Overdue' and pref.booking:
                send_push_notification(
                    auth_token,
                    token_obj.token,
                    title="Booking Overdue",
                    body=f"Your booking for {instance.car} is overdue!",
                    data={"booking_id": str(instance.id)}
                )
    except (NotificationToken.DoesNotExist, NotificationPreference.DoesNotExist):
        pass

#for payment notification
@receiver(post_save, sender=Payment)
def notify_on_payment(sender, instance, created, **kwargs):
    user = instance.booking.customer.user  # adjust as per your model
    try:
        pref = user.notification_preference
        token_obj = NotificationToken.objects.get(user=user)
        auth_token = generate_firebase_auth_key()
        if created and pref.payment:
            send_push_notification(
                auth_token,
                token_obj.token,
                title="Payment Received",
                body=f"Payment for booking {instance.booking.id} received.",
                data={"booking_id": str(instance.booking.id)}
            )
    except (NotificationToken.DoesNotExist, NotificationPreference.DoesNotExist):
        pass
