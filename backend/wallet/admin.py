# wallets/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Wallet, Transaction, Withdrawal


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "balance",
        "reserved",
        "total_earned",
        "currency",
        "status",
        "created_at",
    ]
    list_filter = ["status", "currency", "created_at"]
    search_fields = ["user__username", "user__email", "user__phone"]
    readonly_fields = [
        "id",
        "user",
        "balance",
        "reserved",
        "total_earned",
        "created_at",
        "updated_at",
    ]

    # def has_delete_permission(self, request, obj=None):
    #     return False

    def delete_model(self, request, obj):
        pass

    def get_readonly_fields(self, request, obj=None):
        """All fields readonly EXCEPT reverse relations"""
        readonly = []
        for field in self.model._meta.get_fields():
            if field.related_model is None:  # Skip reverse relations (transactions)
                readonly.append(field.name)
        return readonly


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        "wallet",
        "type",
        "direction",
        "amount",
        "status",
        "reference",
        "created_at",
    ]
    list_filter = ["type", "direction", "status", "created_at"]
    search_fields = ["wallet__user__username", "wallet__user__email", "reference"]
    readonly_fields = [
        "id",
        "wallet",
        "type",
        "direction",
        "amount",
        "status",
        "reference",
        "description",
        "created_at",
    ]
    ordering = ["-created_at"]

    # def has_delete_permission(self, request, obj=None):
    #     return False

    def delete_model(self, request, obj):
        pass

    def get_readonly_fields(self, request, obj=None):
        """All fields readonly EXCEPT reverse relations"""
        readonly = []
        for field in self.model._meta.get_fields():
            if field.related_model is None:  # Skip reverse relations (transactions)
                readonly.append(field.name)
        return readonly


@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = [
        "wallet",
        "amount",
        "status",
        "payout_method_display",
        "processor",
        "created_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = [
        "wallet__user__username",
        "wallet__user__email",
        "processor__username",
    ]
    readonly_fields = [
        "id",
        "wallet",
        "amount",
        "payout_info",
        "status",
        "created_at",
        "updated_at",
    ]
    actions = ["approve_withdrawals", "reject_withdrawals"]
    ordering = ["-created_at"]

    # Custom display payment in the admin panel
    def payout_method_display(self, obj):
        return obj.payout_info.get("method", "N/A")  # get method from json data

    payout_method_display.short_description = (
        "Payout Method"  # Column header for the display method
    )

    ############### Bulk Actions - Signal Compatible #################################
    def approve_withdrawals(self, request, queryset):
        """Approve withdrawals with .save() to trigger signals"""
        count = 0
        for withdrawal in queryset.filter(
            status=Withdrawal.Status.PENDING
        ):  # Bulk updated field
            withdrawal.status = Withdrawal.Status.APPROVED
            withdrawal.save()  # Triggers post_save signal!
            count += 1

        self.message_user(
            request, f"{count} withdrawals approved."
        )  # Message for admin

    approve_withdrawals.short_description = (
        "Approve selected withdrawals"  # Dropdown Text
    )

    def reject_withdrawals(self, request, queryset):
        """Reject withdrawals with .save() to trigger signals"""
        count = 0
        for withdrawal in queryset.filter(status=Withdrawal.Status.PENDING):
            withdrawal.status = Withdrawal.Status.REJECTED
            withdrawal.save()  # Triggers post_save signal!
            count += 1

        self.message_user(request, f"{count} withdrawals rejected.")

    reject_withdrawals.short_description = "Reject selected withdrawals"
    ############### End of Bulk Actions #################################

    def has_delete_permission(self, request, obj=None):
        return False

    def delete_model(self, request, obj):
        pass

    def get_readonly_fields(self, request, obj=None):
        # Allow processor to be set
        if obj and obj.status != Withdrawal.Status.PENDING:
            return self.readonly_fields + ["processor"]
        return self.readonly_fields
