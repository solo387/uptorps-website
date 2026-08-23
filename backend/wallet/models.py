from django.db import models
from accounts.models import User
import uuid

# Create your models here.
class Wallet(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"    # Value first (uppercase), label second
        FROZEN = "FROZEN", "Frozen"
        SUSPENDED = "SUSPENDED", "Suspended"
    id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, primary_key=True)
    user = models.OneToOneField(User, on_delete=models.PROTECT, related_name="wallet")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reserved = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_earned = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(default="GHS", max_length=3)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE) 
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)

    def delete(self, *args, **kwargs):
        raise ValueError("Wallet records cannot be deleted")

    def __str__(self):
        return f"{self.user.email} ---- {self.currency} {self.balance}"

    class Meta:
        permissions = [
            ("view_any_wallet", "Can view any wallet"),
            ("reconcile_wallet", "Can reconcile wallet balances"),
        ]


class Transaction(models.Model):
    class Type(models.TextChoices):
        REFERRAL_BONUS = "REFERRAL_BONUS", "Referral Bonus"
        WITHDRAWAL = "WITHDRAWAL", "Withdrawal"
        PREMIUM_PAYMENT = "PREMIUM_PAYMENT", "Premium Payment"

    class Direction(models.TextChoices):
        CREDIT = "CREDIT", "Credit"
        DEBIT = "DEBIT", "Debit"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"
        REVERSED = "REVERSED", "Reversed"
    
    id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, primary_key=True)
    wallet = models.ForeignKey('Wallet', on_delete=models.PROTECT, related_name='transactions')
    type = models.CharField(max_length=20, choices=Type.choices)
    direction = models.CharField(max_length=10, choices=Direction.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING)
    reference = models.CharField(max_length=50, unique=True, editable=False, blank=False)
    payout_info = models.JSONField()  
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def delete(self, *args, **kwargs):
        """Prevent deletion of transaction records"""
        raise ValueError("Transaction records cannot be deleted for audit purposes")
    
    class Meta:
        verbose_name_plural = "Transactions"
        permissions = [
            ("view_any_transaction", "Can view any wallet transaction"),
        ]


class Withdrawal(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved" 
        REJECTED = "REJECTED", "Rejected"
        PROCESSED = "PROCESSED", "Processed"
    
    id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, primary_key=True)
    wallet = models.ForeignKey('Wallet', on_delete=models.PROTECT, related_name='withdrawals')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING)
    
    # Flexible payout info
    payout_info = models.JSONField()  # {"method": "Mobile Money", "detail": "0123457545"}
    processor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_withdrawals',verbose_name='Processed by')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def delete(self, *args, **kwargs):
        raise ValueError("Withdrawal records cannot be deleted")
    
    class Meta:
        verbose_name_plural = "Withdrawals"
        permissions = [
            ("view_any_withdrawal", "Can view any withdrawal"),
            ("approve_withdrawal", "Can approve or reject withdrawals"),
            ("process_withdrawal", "Can process approved withdrawals"),
        ]
