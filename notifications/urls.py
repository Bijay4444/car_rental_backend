from django.urls import path
from .views import (
    NotificationPreferenceView, 
    SaveFCMTokenView, 
    TestPushNotificationView,
    ManageUserDevicesView  
)

urlpatterns = [
    path('preferences/', NotificationPreferenceView.as_view(), name='notification-preferences'),
    path('save-fcm-token/', SaveFCMTokenView.as_view(), name='save-fcm-token'),
    path('test-push-notification/', TestPushNotificationView.as_view(), name='test-push-notification'),
    path('devices/', ManageUserDevicesView.as_view(), name='manage-devices'),  
]

