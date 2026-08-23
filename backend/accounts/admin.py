from audits.signals import user_deleted, admin_created
from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("uuid","username", "email", "role", "is_staff")
    readonly_fields = ("uuid",)
    search_fields = ("email", "username")

    def save_model(self, request, obj, form, change):
        is_new = not change
        is_admin = obj.is_staff

        if is_new and is_admin:
            admin_created.send(
                sender=self.__class__,
                actor=request.user,
                target=obj,
                request=request,
            )

        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        # Emit audit signal
        user_deleted.send(
            sender=self.__class__,
            actor=request.user,
            target=obj,
            request=request,
        )
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            user_deleted.send(
                sender=self.__class__,
                actor=request.user,
                target=obj,
                request=request,
            )
        super().delete_queryset(request, queryset)

