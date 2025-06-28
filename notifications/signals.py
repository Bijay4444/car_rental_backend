from django.db.models.signals import post_save
from django.dispatch import receiver
from bookings.models import Booking, Payment
from notifications.models import NotificationToken, NotificationPreference
from notifications.firebase import generate_firebase_auth_key, send_push_notification

@receiver(post_save, sender=Booking)
def notify_all_staff_on_booking(sender, instance, created, **kwargs):
    """
    Send notifications to ALL staff when booking is created or updated
    """
    print(f"🔔 Booking signal triggered for {instance.booking_id}, created={created}")
    
    try:
        # Get ALL active FCM tokens
        tokens = NotificationToken.objects.all()
        print(f"📱 Found {tokens.count()} staff tokens to notify")
        
        if tokens.count() == 0:
            print("⚠️ No FCM tokens found - no notifications will be sent")
            return
        
        # Generate Firebase auth token once
        auth_token = generate_firebase_auth_key()
        if not auth_token:
            print("❌ Failed to generate Firebase auth token")
            return
        
        success_count = 0
        failure_count = 0
        
        if created:
            # New booking created
            title = "🚗 New Booking Created!"
            body = f"Booking {instance.booking_id} for {instance.car.car_name} by {instance.customer.name}"
            action = "booking_created"
            
        elif instance.booking_status == 'Cancelled':
            # Booking cancelled
            title = "❌ Booking Cancelled"
            body = f"Booking {instance.booking_id} has been cancelled"
            action = "booking_cancelled"
            
        elif instance.booking_status == 'Returned':
            # Car returned
            title = "✅ Car Returned"
            body = f"Car returned for booking {instance.booking_id}"
            action = "booking_returned"
            
        else:
            # Other updates - skip notification
            return
        
        # Send to ALL staff tokens
        for token_obj in tokens:
            try:
                # Check user preferences (optional - can be removed if not needed)
                try:
                    pref, _ = NotificationPreference.objects.get_or_create(user=token_obj.user)
                    if not pref.booking:
                        print(f"⏭️ Booking notifications disabled for {token_obj.user.email}")
                        continue
                except:
                    # If preferences fail, send anyway
                    pass
                
                status_code, response = send_push_notification(
                    auth_token=auth_token,
                    fcm_token=token_obj.token,
                    title=title,
                    body=body,
                    data={
                        "booking_id": instance.booking_id,
                        "action": action,
                        "car_name": instance.car.car_name,
                        "customer_name": instance.customer.name,
                        "start_date": str(instance.start_date),
                        "end_date": str(instance.end_date),
                        "total_amount": str(instance.total_amount),
                        "staff_email": token_obj.user.email
                    }
                )
                
                if status_code == 200:
                    success_count += 1
                    print(f"✅ Notification sent to {token_obj.user.email}")
                else:
                    failure_count += 1
                    print(f"❌ Failed to send to {token_obj.user.email}: {response}")
                    
            except Exception as e:
                failure_count += 1
                print(f"💥 Exception sending to {token_obj.user.email}: {str(e)}")
        
        print(f"📊 Booking notification results: {success_count} success, {failure_count} failed out of {tokens.count()} total")
        
    except Exception as e:
        print(f"💥 Error in booking notification: {str(e)}")
        import traceback
        traceback.print_exc()


@receiver(post_save, sender=Payment)
def notify_all_staff_on_payment(sender, instance, created, **kwargs):
    """
    Send notifications to ALL staff when payment is received
    """
    print(f"💰 Payment signal triggered for booking {instance.booking.booking_id}, created={created}")
    
    try:
        if not created:
            return  # Only notify on new payments
            
        # Get ALL active FCM tokens
        tokens = NotificationToken.objects.all()
        print(f"📱 Found {tokens.count()} staff tokens to notify")
        
        if tokens.count() == 0:
            print("⚠️ No FCM tokens found - no notifications will be sent")
            return
        
        # Generate Firebase auth token once
        auth_token = generate_firebase_auth_key()
        if not auth_token:
            print("❌ Failed to generate Firebase auth token")
            return
        
        success_count = 0
        failure_count = 0
        
        title = "💰 Payment Received!"
        body = f"Payment of Rs.{instance.amount} received for booking {instance.booking.booking_id}"
        
        # Send to ALL staff tokens
        for token_obj in tokens:
            try:
                # Check user preferences (optional)
                try:
                    pref, _ = NotificationPreference.objects.get_or_create(user=token_obj.user)
                    if not pref.payment:
                        print(f"⏭️ Payment notifications disabled for {token_obj.user.email}")
                        continue
                except:
                    # If preferences fail, send anyway
                    pass
                
                status_code, response = send_push_notification(
                    auth_token=auth_token,
                    fcm_token=token_obj.token,
                    title=title,
                    body=body,
                    data={
                        "booking_id": instance.booking.booking_id,
                        "payment_id": str(instance.id),
                        "action": "payment_received",
                        "amount": str(instance.amount),
                        "payment_method": instance.payment_method or "Not specified",
                        "customer_name": instance.booking.customer.name,
                        "staff_email": token_obj.user.email
                    }
                )
                
                if status_code == 200:
                    success_count += 1
                    print(f"✅ Payment notification sent to {token_obj.user.email}")
                else:
                    failure_count += 1
                    print(f"❌ Failed to send to {token_obj.user.email}: {response}")
                    
            except Exception as e:
                failure_count += 1
                print(f"💥 Exception sending to {token_obj.user.email}: {str(e)}")
        
        print(f"📊 Payment notification results: {success_count} success, {failure_count} failed out of {tokens.count()} total")
        
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
