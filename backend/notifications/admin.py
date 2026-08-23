from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        "recipient",
        "category",
        "channel",
        "title",
        "status",
        "is_read",
        "created_at",
    ]
    list_filter = ["category", "channel", "status", "is_read", "created_at"]
    search_fields = ["recipient__email", "title", "message"]
    readonly_fields = [field.name for field in Notification._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
