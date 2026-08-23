from django.apps import AppConfig


class AuditsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "audits"

    def ready(self):
        from audits.signals import (
            admin_created, 
            user_deleted,
            failed_admin_login,
            success_admin_login,
        )
        from audits.signals_handler import (
            handle_admin_created,
            handle_user_deleted,
            handle_failed_admin_login,
            handle_success_admin_login,
        )

        admin_created.connect(handle_admin_created)
        user_deleted.connect(handle_user_deleted)
        failed_admin_login.connect(handle_failed_admin_login)
        success_admin_login.connect(handle_success_admin_login)