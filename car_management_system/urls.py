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
from django.views.generic import TemplateView
from django.views.static import serve
import os
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

# Swagger/OpenAPI schema view for API documentation
schema_view = get_schema_view(
   openapi.Info(
      title="Car Rental API",
      default_version='v1',
      description="API documentation for Car Rental project",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
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

    # Menu App
    path('api/menu/', include('menu.urls')),

    # Dashboard App
    path('api/dashboard/', include('dashboard.urls')),
    
    # Notifications App
    path('api/notifications/', include('notifications.urls')), 
    
    # Swagger/OpenAPI documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),   
]

# Serve static and media files in development
# This is only for development purposes. In production, we will use a proper web server to serve static files.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Serve the Firebase messaging service worker file
# This is only for development purposes. In production, we will use a proper web server to serve static files.
from django.views.static import serve
import os

urlpatterns += [
    path(
        'firebase-messaging-sw.js',
        serve,
        {
            'document_root': os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'path': 'firebase-messaging-sw.js'
        }
    ),
]
