# wallet/permissions.py
from rest_framework.permissions import BasePermission

from .models import Wallet


class IsWalletOwnerOrAdmin(BasePermission):
    """
    Object-level access to a Wallet.

    Allowed if:
    - user owns the wallet (wallet.user_id == request.user.id), or
    - user is an admin, or
    - user has the custom ``wallet.view_any_wallet`` permission.

    Username query params are irrelevant here — ownership is by user PK,
    so matching/colliding usernames cannot grant access to another wallet.
    """

    message = "You do not have permission to access this wallet."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        wallet = self._resolve_wallet(obj)
        if wallet is None:
            return False

        user = request.user

        if user.is_admin or user.has_perm("wallet.view_any_wallet"):
            return True

        return wallet.user_id == user.id

    @staticmethod
    def _resolve_wallet(obj):
        if isinstance(obj, Wallet):
            return obj
        # Transaction / Withdrawal — related wallet
        return getattr(obj, "wallet", None)


class CanApproveWithdrawal(BasePermission):
    """Admin or users with ``wallet.approve_withdrawal``."""

    message = "You do not have permission to approve withdrawals."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.is_admin or user.has_perm("wallet.approve_withdrawal"))
        )


class CanProcessWithdrawal(BasePermission):
    """Admin or users with ``wallet.process_withdrawal``."""

    message = "You do not have permission to process withdrawals."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.is_admin or user.has_perm("wallet.process_withdrawal"))
        )


class CanReconcileWallet(BasePermission):
    """Admin or users with ``wallet.reconcile_wallet``."""

    message = "You do not have permission to reconcile wallets."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.is_admin or user.has_perm("wallet.reconcile_wallet"))
        )
