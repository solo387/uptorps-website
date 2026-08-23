from django.shortcuts import get_object_or_404
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView, RetrieveUpdateAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

#####################
# Account components#
from .serializers import (
    RegisterSerializer, 
    AdminCreateSerializer, 
    CustomTokenObtainPairSerializer,
    EmailVerificationSerializer,
    ResendVerificationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    UserDetailSerializer,
    UserUpdateSerializer,
)
from .permissions import IsAdmin, IsBackendDev, IsSelfOrAdmin
from .models import User
from .throttles import RoleBasedLoginThrottle, ResendVerificationThrottle, PasswordResetThrottle
from .utils import verify_email_token, generate_email_verification_token, generate_password_reset_token, verify_password_reset_token
from .emails import send_verify_email, send_password_reset_email

###################
# Audit components#

from audits.models import AuditLog
from audits.utils import get_client_ip
from audits.signals import admin_created, user_deleted

# Regular user register
class RegisterView(APIView):
    throttle_scope = "register"
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "User created"}, status=201)

# Admin user register
class CreateAdminView(APIView):
    throttle_scope = "admin_register"
    permission_classes = [IsAuthenticated, IsBackendDev]

    def post(self, request):
        serializer = AdminCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        new_admin= serializer.save()

        admin_created.send(
            sender= self.__class__,
            actor= request.user,
            target= new_admin,
            request= request
        )

        return Response(
            {"message": "Admin account created"},
            status=status.HTTP_201_CREATED
        )
    
# Delete user
class DeleteUserView(APIView):
    throttle_scope = "delete_user"
    permission_classes = [IsAuthenticated, IsAdmin]

    def delete(self, request, uuid):
        user = get_object_or_404(User, uuid=uuid)

        # Prevent admin deleting themselves (important)
        if user == request.user:
            return Response(
                {"detail": "You cannot delete your own account."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user_deleted.send(
            sender=self.__class__,
            actor=request.user,
            target=user,
            request=request,
        )

        user.delete()

        return Response(
            {"message": "User deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )
    
# Refresh active tokens
class CustomTokenRefreshView(TokenRefreshView):
    permission_classes= [AllowAny]
    throttle_scope = "token_refresh"

# Login Api
class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes= [AllowAny]
    throttle_classes= [RoleBasedLoginThrottle]
    serializer_class = CustomTokenObtainPairSerializer

# Request email verification 
class ResendVerificationEmailView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ResendVerificationThrottle]

    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        user = User.objects.filter(email=email).first()

        # Security: always return same response
        if not user or user.email_verified:
            # if user.email_verified:
            #     return Response(
            #         {"detail":"You have already verified your email"},
            #         status=status.HTTP_400_BAD_REQUEST
            #     )
            return Response(
                {"detail": "If the email exists, a verification link was sent."},
                status=status.HTTP_200_OK,
            )

        token = generate_email_verification_token(user)
        verify_url = f"{settings.HOST_DOMAIN_URL}/verify-email/?token={token}"
        send_verify_email.delay(f'{user.uuid}', verify_url)

        return Response(
            {"detail": "If the email exists, a verification link was sent."},
            status=status.HTTP_200_OK,
        )

# Verify email
class VerifyEmailView(APIView):
    permission_classes= [AllowAny]
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]
        email = verify_email_token(token)

        if not email:
            return Response(
                {"detail": "Invalid or expired token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.filter(email=email).first()

        if not user:
            return Response(
                {"detail": "User not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.email_verified:
            return Response(
                {"detail": "Email already verified"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.email_verified = True
        user.is_active = True
        user.save(update_fields=["email_verified", "is_active"])

        return Response(
            {"detail": "Email verified successfully"},
            status=status.HTTP_200_OK,
        )

# Request password reset
class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [PasswordResetThrottle]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        user = User.objects.filter(email=email).first()

        # Always same response (anti-enumeration)
        if user:
            token = generate_password_reset_token(user)
            reset_url = f"{settings.HOST_DOMAIN_URL}/reset-password/?token={token}"
            duration = settings.TOKEN_VERIFICATION_DURATION

            send_password_reset_email.delay(f'{user.uuid}', reset_url, duration)

        return Response(
            {"detail": "If the email exists, a reset link was sent."},
            status=status.HTTP_200_OK,
        )

# Confirm password reset
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        email = verify_password_reset_token(token)
        if not email:
            return Response(
                {"detail": "Invalid or expired token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.filter(email=email).first()
        if not user:
            return Response(
                {"detail": "Invalid token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save(update_fields=["password"])

        return Response(
            {"detail": "Password reset successful"},
            status=status.HTTP_200_OK,
        )

# Getting user info
# class UserDetailView(RetrieveAPIView):
#     permission_classes = [IsAuthenticated, IsSelfOrAdmin]
#     queryset = User.objects.all()
#     serializer_class = UserDetailSerializer
#     lookup_field = "uuid"

# Updating user info
class UserDetailUpdateView(RetrieveUpdateAPIView):
    queryset = User.objects.all()
    lookup_field = "uuid"
    permission_classes = [IsAuthenticated, IsSelfOrAdmin]

    def get_serializer_class(self):
        if self.request.method in ["PATCH", "PUT"]:
            return UserUpdateSerializer
        return UserDetailSerializer