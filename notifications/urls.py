from django.urls import path
from .views import NotificationPreferenceView, SaveFCMTokenView, showFirebaseJS, index

urlpatterns = [
    path('preferences/', NotificationPreferenceView.as_view(), name='notification-preferences'),
    path('save-fcm-token/', SaveFCMTokenView.as_view(), name='save_fcm_token'),
    
    path('firebase-messaging-sw.js',showFirebaseJS,name="show_firebase_js"),
    path('',index),

]

