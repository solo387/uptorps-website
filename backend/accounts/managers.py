from django.contrib.auth.base_user import BaseUserManager

class UserManager(BaseUserManager):
    # def create_user(self, email,username=None, password=None, first_name=None, last_name=None,  **extra_fields):
    def create_user(self, email,username=None, password=None,  **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)# first_name=first_name, last_name=last_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("email_verified", True)
        extra_fields.setdefault("role", self.model.Roles.ADMIN)
        extra_fields.setdefault("admin_type", self.model.AdminType.DEVELOPER)
        extra_fields.setdefault(
            "dev_specialization",
            self.model.DevSpecialization.BACKEND
        )

        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must be staff")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must be superuser")

        return self.create_user(email, username, password, **extra_fields)
