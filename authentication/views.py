from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.views import APIView

from .models import CustomUser
from .serializers import( 
                         RegisterSerializer,
                         BiometricToggleSerializer,
                         ChangePasswordSerializer,
                         )

from django.contrib.auth import update_session_auth_hash, authenticate, get_user_model
from .serializers import UserProfileSerializer

User = get_user_model()

# Custom Token Serializer 
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom TokenObtainPairSerializer to handle email and password authentication.

    Validates user credentials using email and password, and returns JWT tokens.
    Raises custom error codes for invalid email or password.
    """
    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        # Check if user with this email exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Email not found - raise custom error with code 222
            raise AuthenticationFailed({
                "detail": "No active account found with the given credentials",
                "status_code": int(222)
            })

        # Email exists, check password
        user = authenticate(email=email, password=password)
        if user is None:
            # Password incorrect - raise custom error with code 111
            raise AuthenticationFailed({
                "detail": "Invalid password",
                "status_code": int(111)
            })

        # If authentication successful, proceed with normal flow
        return super().validate(attrs)

#-----Registration 
 
class RegisterView(generics.CreateAPIView):
    """
    API view for user registration.

    Allows new users to register by providing email, full name, password, and optional user image and device info.
    """
    queryset = CustomUser.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        """
        Handle user registration request.

        Returns:
            Response: API response with user data and status message.
        """
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
    """
    API view for user login.

    Authenticates user using email and password, returns JWT tokens on success.
    Handles custom error codes for invalid credentials.
    """
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        """
        Handle user login request.

        Returns:
            Response: API response with JWT tokens and status message.
        """
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except AuthenticationFailed as exc:
            error_detail = exc.detail
            # exc.detail can be dict or string, handle both
            if isinstance(error_detail, dict):
                detail = error_detail.get("detail", "Authentication failed")
                status_code = int(error_detail.get("status_code", 111))
            else:
                detail = str(error_detail)
                status_code = 111

            return Response({
                "data": None,
                "detail": detail,
                "status_code": status_code
            }, status=status.HTTP_401_UNAUTHORIZED)

        token = serializer.validated_data
        return Response({
            "data": token,
            "message": "Login successful",
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)


        
# User Logout View with Blacklist
class LogoutView(APIView):
    """
    API view for user logout and token blacklisting.

    Blacklists the provided refresh token to prevent further use.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Handle user logout request.

        Returns:
            Response: API response with logout status.
        """
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
    """
    API view to enable or disable biometric (fingerprint) authentication for the user.

    Allows authenticated users to update their biometric authentication settings and device info.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = BiometricToggleSerializer

    def get_object(self):
        """
        Return the currently authenticated user.

        Returns:
            CustomUser: The authenticated user instance.
        """
        # Return the currently authenticated user
        return self.request.user

    def update(self, request, *args, **kwargs):
        """
        Handle biometric toggle update request.

        Returns:
            Response: API response with updated settings and status message.
        """
        partial = kwargs.pop('partial', True)  
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
    """
    API view to handle password change for authenticated users.

    Validates old password and ensures new passwords match and meet minimum length requirements.
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Handle password change request.

        Returns:
            Response: API response with status message.
        """
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
    """
    API view to retrieve and update user profile information.

    Allows authenticated users to view and update their profile details, including user image.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        Return the currently authenticated user.

        Returns:
            CustomUser: The authenticated user instance.
        """
        return self.request.user
