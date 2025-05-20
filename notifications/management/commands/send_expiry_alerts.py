from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from cars.models import Car
from notifications.models import NotificationToken
from notifications.firebase import generate_firebase_auth_key, send_push_notification

class Command(BaseCommand):
    help = 'Send expiry alerts for insurance and tracker'

    def handle(self, *args, **kwargs):
        soon = timezone.now().date() + timedelta(days=7)
        cars = Car.objects.all()
        for car in cars:
            user = car.created_by
            if not user:
                continue  # Skip if no responsible user
            try:
                pref = user.notification_preference
                token_obj = NotificationToken.objects.get(user=user)
                auth_token = generate_firebase_auth_key()
                # Insurance expiry
                if (pref.insurance_expiry and car.insurance_expiry_date and
                        car.insurance_expiry_date <= soon):
                    send_push_notification(
                        auth_token,
                        token_obj.token,
                        title="Insurance Expiry Alert",
                        body=f"Insurance for {car.car_name} expires on {car.insurance_expiry_date}!",
                        data={"car_id": str(car.id)}
                    )
                # Tracker expiry
                if (pref.tracker_expiry and car.tracker_expiry_date and
                        car.tracker_expiry_date <= soon):
                    send_push_notification(
                        auth_token,
                        token_obj.token,
                        title="Tracker Expiry Alert",
                        body=f"Tracker for {car.car_name} expires on {car.tracker_expiry_date}!",
                        data={"car_id": str(car.id)}
                    )
                # Car expiry: If you want to add a field, do it here.
            except (NotificationToken.DoesNotExist, AttributeError):
                pass  # User has no token or no preferences
        self.stdout.write(self.style.SUCCESS('Expiry alerts sent!'))
