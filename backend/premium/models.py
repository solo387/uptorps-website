# premium/models.py
import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class PremiumPackage(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    id = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False, primary_key=True
    )
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField()
    max_referrals = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.ACTIVE
    )

    # the balance at which premium expires and user must withdraw
    withdrawal_threshold = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Balance at which premium expires and earnings are frozen",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Premium Packages"

    def __str__(self):
        return f"{self.name} - GH₵{self.price}"


class UserPremiumSubscription(models.Model):

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        EXPIRED = "EXPIRED", "Expired"

    id = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False, primary_key=True
    )
    user = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="premium_subscriptions"
    )
    package = models.ForeignKey(
        PremiumPackage, on_delete=models.PROTECT, related_name="subscriptions"
    )
    transaction = models.OneToOneField(
        "wallet.Transaction",
        on_delete=models.PROTECT,
        related_name="premium_subscription",
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.ACTIVE
    )
    purchased_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Set when duration_days lapses or threshold is hit",
    )

    class Meta:
        verbose_name = "Premium Subscription"
        verbose_name_plural = "Premium Subscriptions"
        ordering = ["-purchased_at"]

    def __str__(self):
        return f"{self.user} — {self.package.name} " f"({self.status})"

    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE

    @property
    def version(self):
        # how many times this user has been premium
        return UserPremiumSubscription.objects.filter(user=self.user).count()
