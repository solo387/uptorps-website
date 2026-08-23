from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL

class AuditLog(models.Model):
    class Action(models.TextChoices):
        CREATE_ADMIN = "CREATE_ADMIN", "Create Admin"
        DELETE_ADMIN = "DELETE_ADMIN", "Delete Admin"
        DELETE_USER = "DELETE_USER", "Delete User"
        FAILED_ADMIN_LOGIN = "FAILED_ADMIN_LOGIN", "Failed Admin Login"
        SUCCESS_ADMIN_LOGIN = "SUCCESS_ADMIN_LOGIN", "Success Admin Login"
        LOGIN_THROTTLED = "LOGIN_THROTTLED", "Login Throttled"

    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank= True,
        related_name="actor_audit_logs"
    )
    actor_email= models.EmailField(blank=True)

    action = models.CharField(
        max_length=50,
        choices=Action.choices
    )

    target_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="target_audit_logs"
    )
    target_email= models.EmailField(blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} by {self.actor} at {self.created_at}"
