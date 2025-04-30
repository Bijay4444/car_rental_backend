from django.urls import path
from .views import (RegisterView, 
                    LoginView, 
                    LogoutView, 
                    BiometricToggleView,
                    ChangePasswordView,
                    UserProfileView,
                    )
from rest_framework_simplejwt.views import TokenRefreshView
from dj_rest_auth.views import PasswordResetView, PasswordResetConfirmView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Password rest endpoints (dj-rest-auth)
    path('password/reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm_api'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    
    # Biometric toggle endpoint
    path('biometric/toggle/', BiometricToggleView.as_view(), name='biometric_toggle'),
    
    # User profile endpoint
    path('profile/', UserProfileView.as_view(), name='user_profile'),
]
