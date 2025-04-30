from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView

from .models import CustomUser
from .serializers import( 
                         RegisterSerializer,
                         BiometricToggleSerializer,
                         ChangePasswordSerializer,
                         )

from django.contrib.auth import update_session_auth_hash
from .serializers import UserProfileSerializer

# Custom Token Serializer 
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims if needed
        token['email'] = user.email
        token['full_name'] = user.full_name
        return token

#-----Registration 
 
class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "data": None,
                "message": "Validation error",
                "status_code": status.HTTP_400_BAD_REQUEST
        

        }, status=status.HTTP_400_BAD_REQUEST)

        self.perform_create(serializer)
        return Response({
            "data": serializer.data,
            "message": "User registered successfully",
            "status_code": status.HTTP_201_CREATED
        }, status=status.HTTP_201_CREATED
                        )

#------Login
class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "data": None,
                "message": "Invalid credentials",
                "status_code": status.HTTP_401_UNAUTHORIZED
            }, status=status.HTTP_401_UNAUTHORIZED)

        token = serializer.validated_data
        return Response({
            "data": token,
            "message": "Login successful",
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)
        
# User Logout View with Blacklist
class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({
                "data": None,
                "message": "Refresh token required for logout.",
                "status_code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({
                "data": None,
                "message": "Logout successful",
                "status_code": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)
        except Exception:
            return Response({
                "data": None,
                "message": "Invalid token.",
                "status_code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)

#------Biometric Toggle           
class BiometricToggleView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BiometricToggleSerializer

    def get_object(self):
        # Return the currently authenticated user
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)  # Allow partial updates
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            "data": serializer.data,
            "message": "Biometric login settings updated successfully",
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)


#-----Change Password
class ChangePasswordView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            old_password = serializer.validated_data['old_password']
            new_password1 = serializer.validated_data['new_password1']
            new_password2 = serializer.validated_data['new_password2']

            if not request.user.check_password(old_password):
                return Response({
                    "data": None,
                    "message": "Incorrect old password.",
                    "status_code": status.HTTP_400_BAD_REQUEST
                }, status=status.HTTP_400_BAD_REQUEST)

            if new_password1 != new_password2:
                return Response({
                    "data": None,
                    "message": "New passwords do not match.",
                    "status_code": status.HTTP_400_BAD_REQUEST
                }, status=status.HTTP_400_BAD_REQUEST)

            request.user.set_password(new_password1)
            request.user.save()

            # Update session to prevent logout after password change
            update_session_auth_hash(request, request.user)

            return Response({
                "data": None,
                "message": "Password changed successfully.",
                "status_code": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#-----User Profile
class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
