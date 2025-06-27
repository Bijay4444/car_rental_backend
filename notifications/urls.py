from django.urls import path
from .views import NotificationPreferenceView, SaveFCMTokenView, TestPushNotificationView

urlpatterns = [
    path('preferences/', NotificationPreferenceView.as_view(), name='notification-preferences'),
    path('save-fcm-token/', SaveFCMTokenView.as_view(), name='save_fcm_token'),
    path('test-push-notification/', TestPushNotificationView.as_view(), name='test_push_notification'),
]

