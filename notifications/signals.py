from django.db.models.signals import post_save
from django.dispatch import receiver
from bookings.models import Booking, Payment
from notifications.models import NotificationToken
from notifications.firebase import generate_firebase_auth_key, send_push_notification

# for booking notification
@receiver(post_save, sender=Booking)
def notify_on_booking(sender, instance, created, **kwargs):
    """
    Signal handler to send notifications on booking creation or status change.

    Notifies the user when a booking is confirmed, returned, or overdue, based on their preferences.
    """
    print(f"🔔 Booking signal triggered for {instance.booking_id}, created={created}")
    
    try:
        # Get the user who created the booking (authenticated user)
        user = instance.created_by  
        print(f"📱 Found user: {user.email}")  
        
        # Get user preferences
        try:
            from notifications.models import NotificationPreference
            pref, _ = NotificationPreference.objects.get_or_create(user=user)
        except Exception as e:
            print(f"❌ Error getting preferences: {e}")
            return
        
        # Get FCM token
        try:
            token_obj = NotificationToken.objects.get(user=user)
            print(f"📱 Found FCM token: {token_obj.token[:20]}...")
        except NotificationToken.DoesNotExist:
            print(f"❌ No FCM token found for user {user.email}")  
            return
        
        # Generate Firebase auth token
        auth_token = generate_firebase_auth_key()
        if not auth_token:
            print("❌ Failed to generate Firebase auth token")
            return
        
        print(f"✅ Firebase auth token generated")
        
        # Send notification for new booking
        if created and pref.booking:
            print(f"📤 Sending booking confirmation notification...")
            
            status_code, response = send_push_notification(
                auth_token,
                token_obj.token,
                title="🚗 Booking Confirmed!",
                body=f"Your booking {instance.booking_id} for {instance.car.car_name} is confirmed!",
                data={
                    "booking_id": instance.booking_id,
                    "action": "booking_created",
                    "car_name": instance.car.car_name,
                    "customer_name": instance.customer.name,
                    "user_email": user.email  
                }
            )
            
            print(f"🔥 Firebase response - Status: {status_code}")
            if status_code == 200:
                print(f"✅ Notification sent successfully to {user.email}")  
            else:
                print(f"❌ Notification failed: {response}")
        
        # Handle status changes (fix the field name)
        elif not created:
            if instance.booking_status == 'Returned' and pref.booking:  
                send_push_notification(
                    auth_token,
                    token_obj.token,
                    title="✅ Car Returned",
                    body=f"Your booking {instance.booking_id} is marked as returned.",
                    data={"booking_id": instance.booking_id, "action": "booking_returned"}
                )
            elif instance.booking_status == 'Cancelled' and pref.booking:  
                send_push_notification(
                    auth_token,
                    token_obj.token,
                    title="❌ Booking Cancelled",
                    body=f"Your booking {instance.booking_id} has been cancelled.",
                    data={"booking_id": instance.booking_id, "action": "booking_cancelled"}
                )
                
    except Exception as e:
        print(f"💥 Error in booking notification: {str(e)}")
        import traceback
        traceback.print_exc()

#for payment notification
@receiver(post_save, sender=Payment)
def notify_on_payment(sender, instance, created, **kwargs):
    """
    Signal handler to send notifications on payment creation.

    Notifies the user when a payment is received, based on their preferences.
    """
    print(f"💰 Payment signal triggered for booking {instance.booking.booking_id}, created={created}")
    
    try:
        # Use the same pattern as booking notification
        user = instance.booking.created_by  
        print(f"📱 Found user: {user.email}") 
        
        # Get user preferences
        try:
            from notifications.models import NotificationPreference
            pref, _ = NotificationPreference.objects.get_or_create(user=user)
        except Exception as e:
            print(f"❌ Error getting preferences: {e}")
            return
        
        # Get FCM token
        try:
            token_obj = NotificationToken.objects.get(user=user)
            print(f"📱 Found FCM token: {token_obj.token[:20]}...")
        except NotificationToken.DoesNotExist:
            print(f"❌ No FCM token found for user {user.email}")  
            return
        
        # Generate Firebase auth token
        auth_token = generate_firebase_auth_key()
        if not auth_token:
            print("❌ Failed to generate Firebase auth token")
            return
        
        # Send notification for new payment
        if created and pref.payment:
            print(f"💳 Sending payment confirmation notification...")
            
            status_code, response = send_push_notification(
                auth_token,
                token_obj.token,
                title="💰 Payment Received!",
                body=f"Payment of Rs.{instance.amount} for booking {instance.booking.booking_id} received successfully!",
                data={
                    "booking_id": instance.booking.booking_id,
                    "payment_id": str(instance.id),
                    "action": "payment_received",
                    "amount": str(instance.amount),
                    "user_email": user.email  
                }
            )
            
            print(f"🔥 Firebase response - Status: {status_code}")
            if status_code == 200:
                print(f"✅ Payment notification sent successfully to {user.email}")  
            else:
                print(f"❌ Payment notification failed: {response}")
                
    except Exception as e:
        print(f"💥 Error in payment notification: {str(e)}")
        import traceback
        traceback.print_exc()
        
# Debug: Print when signals are loaded
print("🔔 Booking notification signal registered")
print("💰 Payment notification signal registered")

# Test signal connection
from django.db.models.signals import post_save
print(f"🔍 Post-save receivers for Booking: {post_save._live_receivers(sender=Booking)}")
print(f"🔍 Post-save receivers for Payment: {post_save._live_receivers(sender=Payment)}")
