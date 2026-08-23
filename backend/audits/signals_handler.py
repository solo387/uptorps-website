from .models import AuditLog
from .utils import get_client_ip
from accounts.models import User

def handle_admin_created(sender, actor, target, request, **kwargs):
    AuditLog.objects.create(
        actor=actor,
        action=AuditLog.Action.CREATE_ADMIN,
        target_user=target,
        ip_address=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )


def handle_user_deleted(sender, actor, target, request, **kwargs):
    action_triggered= AuditLog.Action.DELETE_USER
    try:
        user = User.objects.get(email=target.email, is_staff=True)
        action_triggered= AuditLog.Action.DELETE_ADMIN
    except User.DoesNotExist:
        pass

    AuditLog.objects.create(
        actor=actor,
        actor_email=actor.email if actor else None,
        action=action_triggered,
        target_user=target,
        target_email= target.email if target else None,
        ip_address=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )


def handle_failed_admin_login(sender, email, request, **kwargs):

    try:
        user = User.objects.get(email=email, is_staff=True)
    except User.DoesNotExist:
        return  # Not an admin → do nothing

    AuditLog.objects.create(
        actor=None,  # not authenticated
        action=AuditLog.Action.FAILED_ADMIN_LOGIN,
        target_user=user,
        ip_address=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )
def handle_success_admin_login(sender, email, request, **kwargs):

    try:
        user = User.objects.get(email=email, is_staff=True)
    except User.DoesNotExist:
        return  # Not an admin → do nothing

    AuditLog.objects.create(
        actor=user,  # not authenticated
        action=AuditLog.Action.SUCCESS_ADMIN_LOGIN,
        target_user=user,
        ip_address=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )
