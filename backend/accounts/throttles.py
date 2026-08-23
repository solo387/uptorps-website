# This is a custom throttle on how we want to handle the identity of the incoming request by not using only the ip but username/email

from rest_framework.throttling import SimpleRateThrottle
from audits.models import AuditLog

from django.contrib.auth import get_user_model

User = get_user_model()

class RoleBasedLoginThrottle(SimpleRateThrottle):
    """
    Throttle login attempts differently for admins vs users.
    This is a two in one throttle and actions a made base on the account model

    Note: this extends SimpleRateThrottle, not ScopedRateThrottle.
    ScopedRateThrottle.allow_request() only ever reads a static
    `view.throttle_scope` attribute and never calls get_scope() — so a
    per-request, role-dependent scope has to be resolved here instead,
    the same way ScopedRateThrottle defers rate resolution until the
    request is known.
    """

    def __init__(self):
        # Scope (and therefore rate) depends on the request body, so it
        # can't be resolved until allow_request() runs.
        pass

    def get_scope(self, request):
        identifier = (
            request.data.get("email")
            or request.data.get("username")
        )

        if not identifier:
            return "login_user"

        try:
            user = User.objects.get(
                email__iexact=identifier
            )
        except User.DoesNotExist:
            return "login_user"

        if user.is_staff or user.is_superuser:
            return "login_admin"

        return "login_user"

    def allow_request(self, request, view):
        if request.method != "POST":
            return True

        self.request = request
        self.scope = self.get_scope(request)
        self.rate = self.get_rate()
        self.num_requests, self.duration = self.parse_rate(self.rate)

        return super().allow_request(request, view)

    def get_cache_key(self, request, view):
        identifier = (
            request.data.get("email")
            or request.data.get("username")
        )

        if not identifier:
            return None

        return self.cache_format % {
            "scope": self.scope,
            "ident": identifier.lower(),
        }

    def throttle_failure(self):
        request = self.request

        identifier = (
            request.data.get("email")
            or request.data.get("username")
        )

        try:
            user = User.objects.get(email__iexact=identifier)
        except User.DoesNotExist:
            return False

        if user.is_staff or user.is_superuser:
            AuditLog.objects.create(
                action=AuditLog.Action.LOGIN_THROTTLED,
                target_user=user,
                ip_address=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )

        return False

class ResendVerificationThrottle(SimpleRateThrottle):
    scope = "resend_verification"

    def get_cache_key(self, request, view):
        email = request.data.get("email")
        if not email:
            return None
        return f"resend-verification:{email.lower()}"

    
class PasswordResetThrottle(SimpleRateThrottle):
    scope = "password_reset"

    def get_cache_key(self, request, view):
        email = request.data.get("email")
        if not email:
            return None
        return f"password-reset:{email.lower()}"
