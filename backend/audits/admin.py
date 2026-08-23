from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "action",
        "actor",
        "actor_email",
        "target_user",
        "target_email",
        "ip_address",
        "created_at",
    )
    search_fields = (
    "action",
    "actor__email",
    "target_user__email",
    "ip_address",
) # Search fields for the audit

    list_filter = ("created_at",)
    readonly_fields = [field.name for field in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
