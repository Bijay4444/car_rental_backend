from rest_framework import generics, permissions
from .models import NotificationPreference
from .serializers import NotificationPreferenceSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import NotificationToken
from django.shortcuts import render, HttpResponse
from django.http import HttpResponse
import os
from .firebase import generate_firebase_auth_key, send_push_notification

class NotificationPreferenceView(generics.RetrieveUpdateAPIView):
    """
    API view to retrieve and update the current user's notification preferences.
    """
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """
        Get or create the notification preferences for the current user.

        Returns:
            NotificationPreference: The user's notification preferences.
        """
        obj, created = NotificationPreference.objects.get_or_create(user=self.request.user)
        return obj


class SaveFCMTokenView(APIView):
    """
    API view to save the current user's FCM (Firebase Cloud Messaging) token.

    Expects:
        token (str): The FCM token in the request data.

    Returns:
        Response: Success or error message.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Save or update the user's FCM token.

        Args:
            request (Request): The API request.

        Returns:
            Response: Success or error message.
        """
        token = request.data.get("token")
        if not token:
            return Response({"error": "Token is required"}, status=400)
        NotificationToken.objects.update_or_create(
            user=request.user, defaults={"token": token}
        )
        return Response({"message": "Token saved successfully"})
    
class TestPushNotificationView(APIView):
    """
    Test endpoint to send push notifications via Postman
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Send test push notification - supports both individual and global sending
        """
        try:
            # Check if this is a global notification test
            send_global = request.data.get('send_global', False)
            
            if send_global:
                # Send to ALL staff - FIXED: Remove is_active filter
                tokens = NotificationToken.objects.all()  # ← Changed from filter(is_active=True)
                
                if tokens.count() == 0:
                    return Response({
                        "error": "No FCM tokens found"
                    }, status=400)
                
                # Generate Firebase auth token
                auth_token = generate_firebase_auth_key()
                if not auth_token:
                    return Response({
                        "error": "Failed to generate Firebase auth token"
                    }, status=500)
                
                title = request.data.get('title', 'Global Test Notification')
                body = request.data.get('body', 'Testing global notification to all staff')
                data = request.data.get('data', {"test": "global", "from": "django_backend"})
                
                success_count = 0
                failure_count = 0
                results = []
                
                for token_obj in tokens:
                    try:
                        status_code, response = send_push_notification(
                            auth_token=auth_token,
                            fcm_token=token_obj.token,
                            title=title,
                            body=body,
                            data={
                                **data,
                                "recipient_email": token_obj.user.email
                            }
                        )
                        
                        if status_code == 200:
                            success_count += 1
                            results.append(f"✅ Sent to {token_obj.user.email}")
                        else:
                            failure_count += 1
                            results.append(f"❌ Failed to {token_obj.user.email}: {response}")
                            
                    except Exception as e:
                        failure_count += 1
                        results.append(f"💥 Exception for {token_obj.user.email}: {str(e)}")
                
                return Response({
                    "message": "Global notification completed",
                    "total_tokens": tokens.count(),
                    "success_count": success_count,
                    "failure_count": failure_count,
                    "results": results
                })
            
            else:
                # Individual notification (your existing code)
                fcm_token = request.data.get('fcm_token')
                
                if not fcm_token:
                    try:
                        token_obj = NotificationToken.objects.get(user=request.user)
                        fcm_token = token_obj.token
                    except NotificationToken.DoesNotExist:
                        return Response({
                            "error": "No FCM token found. Please provide fcm_token or save one first."
                        }, status=400)
                
                auth_token = generate_firebase_auth_key()
                if not auth_token:
                    return Response({
                        "error": "Failed to generate Firebase auth token"
                    }, status=500)
                
                title = request.data.get('title', 'Test Notification from Django')
                body = request.data.get('body', 'Your Django backend is working perfectly!')
                data = request.data.get('data', {"test": "true", "from": "django_backend"})
                
                status_code, response_text = send_push_notification(
                    auth_token=auth_token,
                    fcm_token=fcm_token,
                    title=title,
                    body=body,
                    data=data
                )
                
                return Response({
                    "status_code": status_code,
                    "firebase_response": response_text,
                    "message": "Notification sent successfully" if status_code == 200 else "Failed to send notification",
                    "fcm_token_used": fcm_token[:20] + "..." if fcm_token else None
                })
            
        except Exception as e:
            return Response({
                "error": str(e)
            }, status=500)