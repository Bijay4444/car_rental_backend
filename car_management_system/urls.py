"""
URL configuration for car_management_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static

from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Authentication App
    path('api/authentication/', include('authentication.urls')),# handles custom auth endpoints
    path('api/authentication/', include('dj_rest_auth.urls')),# dj-rest-auth endpoints(password reset, etc.)
    path('api/authentication/', include('django.contrib.auth.urls')),# provides standard auth URLs(password rest confirm, etc.)
    
    # Cars App
    path('api/cars/', include('cars.urls')), 
    
    # Bookings App
    path('api/bookings/', include('bookings.urls')),
    
    # Customers App
    path('api/customers/', include('customers.urls')),
]

# Serve static and media files in development
# This is only for development purposes. In production, we will use a proper web server to serve static files.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
