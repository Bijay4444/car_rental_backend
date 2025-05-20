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

def index(request):
    context = {
        "apiKey": os.getenv('apiKey'),
        "authDomain": os.getenv('authDomain'),
        "databaseURL": os.getenv('databaseURL'),
        "projectId": os.getenv('projectId'),
        "storageBucket": os.getenv('storageBucket'),
        "messagingSenderId": os.getenv('messagingSenderId'),
        "appId": os.getenv('appId'),
        "measurementId": os.getenv('measurementId'),
    }
    return render(request, 'notifications/notifications.html', context)


def showFirebaseJS(request):
    data=f"""
    importScripts("https://www.gstatic.com/firebasejs/8.2.0/firebase-app.js");
    importScripts("https://www.gstatic.com/firebasejs/8.2.0/firebase-messaging.js");
    var firebaseConfig = {{
        apiKey: "{os.getenv('apiKey')}",
        authDomain: "{os.getenv('authDomain')}",
        databaseURL: "{os.getenv('databaseURL')}",
        projectId: "{os.getenv('projectId')}",
        storageBucket: "{os.getenv('storageBucket')}",
        messagingSenderId: "{os.getenv('messagingSenderId')}",
        appId: "{os.getenv('appId')}",
        measurementId: "{os.getenv('measurementId')}"
    }};
    firebase.initializeApp(firebaseConfig);
    const messaging = firebase.messaging();
    messaging.setBackgroundMessageHandler(function (payload) {{
        console.log(payload);
        const notification = payload.notification;
        const notificationOptions = {{
            body: notification.body,
            icon: notification.icon
        }};
        return self.registration.showNotification(payload.notification.title, notificationOptions);
    }});
    """

    return HttpResponse(data,content_type="text/javascript")


class NotificationPreferenceView(generics.RetrieveUpdateAPIView):
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        obj, created = NotificationPreference.objects.get_or_create(user=self.request.user)
        return obj


class SaveFCMTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = request.data.get("token")
        if not token:
            return Response({"error": "Token is required"}, status=400)
        NotificationToken.objects.update_or_create(
            user=request.user, defaults={"token": token}
        )
        return Response({"message": "Token saved successfully"})
    
