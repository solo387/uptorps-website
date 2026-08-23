from django.urls import path
from .views import (
    RegisterView,
    CreateAdminView,
    DeleteUserView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    VerifyEmailView,
    ResendVerificationEmailView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    # UserDetailView,
    UserDetailUpdateView
)
# from rest_framework_simplejwt.views import (
    # TokenObtainPairView,
    # TokenRefreshView,
# )


urlpatterns = [
    path("register/", RegisterView.as_view(), name="token_register"),
    path("verify-email/", VerifyEmailView.as_view(), name="email-verify"),
    path("resend-verification/", ResendVerificationEmailView.as_view()),
    # path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("login/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    # path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("create-admin/", CreateAdminView.as_view()), #Docs not written
    path("users/<uuid:uuid>/delete/", DeleteUserView.as_view()), #Docs not written
    path("password-reset/", PasswordResetRequestView.as_view()),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view()),
    path("users/info/<uuid:uuid>/", UserDetailUpdateView.as_view(), name="user-detail"),
    # path("users/update/<uuid:uuid>/", UserDetailUpdateView.as_view(), name="user-detail-update")

]


