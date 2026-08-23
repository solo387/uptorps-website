from celery import shared_task

from notifications.models import Notification
from notifications.services import notify
from premium.models import UserPremiumSubscription
from wallet.models import Wallet
from wallet.utils import reconcile_wallet
import logging

logger = logging.getLogger(__name__)


@shared_task
def reconcile_all_wallets():
    """
    Runs periodically to catch and fix any balance drift
    across all wallets.
    """
    wallets = Wallet.objects.all().values_list("id", flat=True)

    for wallet_id in wallets:
        try:
            reconcile_wallet(wallet_id)
        except Exception as e:
            logger.error(f"Reconciliation failed for wallet {wallet_id}: {e}")
            continue  # do not stop — process remaining wallets

    logger.info(f"Reconciliation complete — {len(wallets)} wallets checked")


@shared_task
def trigger_premium_expiry(wallet_id, subscription_id):
    from django.db import transaction
    from referral.utils import deactivate_referral_node
    from accounts.models import User
    from django.utils import timezone

    with transaction.atomic():
        wallet = Wallet.objects.select_for_update().get(id=wallet_id)

        # Idempotent — already frozen / expired
        if wallet.status == Wallet.Status.FROZEN:
            logger.info(f"Wallet {wallet_id} already FROZEN — skip expiry")
            return

        try:
            subscription = UserPremiumSubscription.objects.select_for_update().get(
                id=subscription_id
            )
        except UserPremiumSubscription.DoesNotExist:
            logger.error(f"Subscription {subscription_id} not found — abort expiry")
            return

        if subscription.status == UserPremiumSubscription.Status.EXPIRED:
            logger.info(
                f"Subscription {subscription_id} already EXPIRED — skip expiry"
            )
            return

        user = User.objects.select_for_update().get(pk=wallet.user_id)

        # Move spendable balance into reserved (keep existing reservations)
        wallet.reserved += wallet.balance
        wallet.balance = 0
        wallet.status = Wallet.Status.FROZEN
        wallet.save(update_fields=["balance", "reserved", "status", "updated_at"])

        deactivate_referral_node(user)

        downgrade_roles = {
            User.Roles.PREMIUM_STUDENT: User.Roles.STUDENT,
            User.Roles.PREMIUM_TEACHER: User.Roles.TEACHER,
        }
        new_role = downgrade_roles.get(user.role)
        if new_role:
            user.role = new_role
            user.save(update_fields=["role"])

        subscription.status = UserPremiumSubscription.Status.EXPIRED
        subscription.expires_at = timezone.now()
        subscription.save(update_fields=["status", "expires_at"])

        notify(
            user,
            title="Premium expired",
            message=(
                "Your premium subscription has expired and your wallet has "
                "been frozen pending withdrawal."
            ),
            category=Notification.Category.PREMIUM,
            channels=[Notification.Channel.IN_APP, Notification.Channel.EMAIL],
        )

    logger.info(
        f"Premium expiry complete — wallet={wallet_id} "
        f"subscription={subscription_id}"
    )
