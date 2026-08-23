import uuid
from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class Notification(models.Model):
    class Channel(models.TextChoices):
        IN_APP = "IN_APP", "In-app"
        EMAIL = "EMAIL", "Email"
        SMS = "SMS", "SMS"

    class Category(models.TextChoices):
        WALLET = "WALLET", "Wallet"
        PREMIUM = "PREMIUM", "Premium"
        REFERRAL = "REFERRAL", "Referral"
        SECURITY = "SECURITY", "Security"
        SYSTEM = "SYSTEM", "System"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SENT = "SENT", "Sent"
        FAILED = "FAILED", "Failed"
        # Channel is recognised but its sender isn't wired up yet (email/sms).
        ON_HOLD = "ON_HOLD", "On hold"

    id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, primary_key=True)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.SYSTEM)
    channel = models.CharField(max_length=10, choices=Channel.choices, default=Channel.IN_APP)
    title = models.CharField(max_length=255)
    message = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.channel}] {self.title} -> {self.recipient}"
