from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.db import models
from .managers import UserManager
from django.core.exceptions import ValidationError
import uuid


class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        TEACHER = "TEACHER", "Teacher"
        STUDENT = "STUDENT", "Student"
        PREMIUM_STUDENT = "PREMIUM_STUDENT", "Premium Student"
        PREMIUM_TEACHER = "PREMIUM_TEACHER", "Premium Teacher"
        SYS = "SYS", "Sys"

    class AdminType(models.TextChoices):
        MANAGER = "MANAGER", "Manager"
        DEVELOPER = "DEVELOPER", "Developer"

    class DevSpecialization(models.TextChoices):
        FRONTEND = "FRONTEND", "Frontend"
        BACKEND = "BACKEND", "Backend"
        SECURITY = "SECURITY", "Security"

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    first_name = models.CharField(max_length=150, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    username = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    role = models.CharField(max_length=30, choices=Roles.choices, default=Roles.STUDENT)
    admin_type = models.CharField(
        max_length=20,
        choices=AdminType.choices,
        null=True,
        blank=True,
    )

    dev_specialization = models.CharField(
        max_length=20,
        choices=DevSpecialization.choices,
        null=True,
        blank=True,
    )
    date_joined = models.DateTimeField(auto_now_add=True)

    referral_code_used = models.CharField(max_length=20, null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]  # no username required
    objects = UserManager()

    # def is_admin(self):
    #     return self.role == self.Roles.ADMIN

    @property
    def is_student(self):
        return self.role == self.Roles.STUDENT

    @property
    def is_teacher(self):
        return self.role == self.Roles.TEACHER

    @property
    def is_admin(self):
        return self.role == self.Roles.ADMIN

    @property
    def is_manager(self):
        return self.is_admin and self.admin_type == self.AdminType.MANAGER

    @property
    def is_developer(self):
        return self.is_admin and self.admin_type == self.AdminType.DEVELOPER

    @property
    def is_frontend_dev(self):
        return (
            self.is_developer
            and self.dev_specialization == self.DevSpecialization.FRONTEND
        )

    @property
    def is_backend_dev(self):
        return (
            self.is_developer
            and self.dev_specialization == self.DevSpecialization.BACKEND
        )

    @property
    def is_security_dev(self):
        return (
            self.is_developer
            and self.dev_specialization == self.DevSpecialization.SECURITY
        )

    def clean(self):
        # Non-admins must not have admin fields
        if self.role != self.Roles.ADMIN:
            self.admin_type = None
            self.dev_specialization = None

        # Admins must have admin_type
        if self.role == self.Roles.ADMIN and not self.admin_type:
            raise ValidationError("Admin users must have admin_type.")

        # Developer admins must have specialization
        if self.admin_type == self.AdminType.DEVELOPER and not self.dev_specialization:
            raise ValidationError("Developer admins must have dev_specialization.")

        # Managers must NOT have specialization
        if self.admin_type == self.AdminType.MANAGER:
            self.dev_specialization = None

    def save(self, *args, **kwargs):
        # Checking if the account is new or old
        # is_creating = self.pk is None

        # if is_creating and self.is_superuser:
        #     self.role = self.Roles.ADMIN
        #     self.admin_type = self.AdminType.MANAGER
        # self.dev_specialization = self.DevSpecialization.BACKEND
        self.full_clean()
        super().save(*args, **kwargs)
