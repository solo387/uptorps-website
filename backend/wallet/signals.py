# wallets/signals.py
import logging
from decimal import Decimal

from celery import shared_task
from django.db import transaction
from django.db.models import F, Max
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from accounts.models import User
from notifications.models import Notification
from notifications.services import notify
from premium.models import PremiumPackage, UserPremiumSubscription
from referral.models import PendingReferral
from referral.task import distribute_referral_bonuses
from referral.utils import place_new_node

from .models import Transaction, Wallet, Withdrawal
from .utils import check_withdrawal_threshold, post_transaction

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Transaction)
def cache_transaction_previous_status(sender, instance, **kwargs):
    """Stash prior status so post_save only applies balance once per completion."""
    if not instance.pk:
        instance._previous_status = None
        return
    try:
        instance._previous_status = (
            Transaction.objects.filter(pk=instance.pk)
            .values_list("status", flat=True)
            .get()
        )
    except Transaction.DoesNotExist:
        instance._previous_status = None


@receiver(post_save, sender=Transaction)
def sync_wallet_balance(sender, instance, created, **kwargs):
    """
    Apply COMPLETED ledger rows to the cached wallet balance exactly once.

    Uses row locks + F() updates so concurrent credits/debits cannot clobber
    each other. Skips if the row was already COMPLETED before this save.
    """
    if instance.status != Transaction.Status.COMPLETED:
        return

    previous = getattr(instance, "_previous_status", None)
    if previous == Transaction.Status.COMPLETED:
        # Re-save of an already-completed txn — do not double-apply
        return

    try:
        user = User.objects.get(email=instance.payout_info["email"])
    except (KeyError, TypeError, User.DoesNotExist):
        user = None

    amount = Decimal(str(instance.amount))

    with transaction.atomic():
        wallet = Wallet.objects.select_for_update().get(pk=instance.wallet_id)

        if instance.direction == Transaction.Direction.CREDIT:
            Wallet.objects.filter(pk=wallet.pk).update(
                balance=F("balance") + amount,
                total_earned=F("total_earned") + amount,
            )
            logger.info(f"Credited {amount} to wallet {wallet.id}")

            if instance.type == Transaction.Type.REFERRAL_BONUS and user is not None:
                notify(
                    user,
                    title="Referral bonus received",
                    message=f"You earned {amount} {wallet.currency} in referral bonus.",
                    category=Notification.Category.REFERRAL,
                    channels=[Notification.Channel.IN_APP, Notification.Channel.EMAIL],
                )
        else:
            Wallet.objects.filter(pk=wallet.pk).update(
                balance=F("balance") - amount,
            )
            logger.info(f"Debited {amount} from wallet {wallet.id}")

        roleUpdate_createWallet(instance, user)

    # Threshold check after commit — use id so we see fresh aggregates
    if instance.direction == Transaction.Direction.CREDIT:
        wallet_id = instance.wallet_id

        def _check():
            check_withdrawal_threshold(wallet_id)

        transaction.on_commit(_check)


def roleUpdate_createWallet(instance, user):
    if (
        user is None
        or user.role == User.Roles.SYS
        or instance.type != Transaction.Type.PREMIUM_PAYMENT
    ):
        return

    premium_roles = {
        User.Roles.STUDENT: User.Roles.PREMIUM_STUDENT,
        User.Roles.TEACHER: User.Roles.PREMIUM_TEACHER,
    }

    # Role update
    new_role = premium_roles.get(user.role)

    if new_role:
        user.role = new_role
        user.save(update_fields=["role"])

    # Wallet creation and if wallet exist unfreeze the account
    version = 1 #This will be passed down to the node creation
    wallet, created = Wallet.objects.get_or_create(user=user)
    if not created:
        wallet.status = Wallet.Status.ACTIVE
        wallet.save(update_fields=["status"])

        from referral.models import ReferralNode
        max_version = (
            ReferralNode.objects.filter(
                user=user,
                status=ReferralNode.Status.INACTIVE,
            ).aggregate(max_version=Max("version"))["max_version"]
        )

        version = (max_version + 1) if max_version is not None else version


    # create subscription (idempotent on OneToOne transaction link)
    package_id = instance.payout_info.get("package_id")
    if package_id:
        package = PremiumPackage.objects.get(id=package_id)

        UserPremiumSubscription.objects.get_or_create(
            transaction=instance,
            defaults={
                "user": user,
                "package": package,
                "status": UserPremiumSubscription.Status.ACTIVE,
            },
        )

    # place user in referral tree only once
    from referral.models import ReferralNode

    existing_node = ReferralNode.objects.filter(
        user=user, status=ReferralNode.Status.ACTIVE
    ).first()
    if existing_node:
        logger.info(
            f"Active referral node already exists for user={user.id} — "
            f"skipping placement"
        )
        return

    pending = PendingReferral.objects.filter(referred_user=user).first()
    referral_code = pending.referral_code if pending else None

    node = place_new_node(user, referral_code=referral_code, version=version)

    # clean up pending referral
    if pending:
        pending.delete()

    logger.info(
        f"Node created for user={user.id} "
        f"node={node.id} referral_code={referral_code}"
    )

    notify(
        user,
        title="Premium activated",
        message="Your premium subscription is now active.",
        category=Notification.Category.PREMIUM,
        channels=[Notification.Channel.IN_APP, Notification.Channel.EMAIL],
    )

    # fire bonus chain only if referred
    # on_commit ensures this only fires after everything above commits
    if referral_code:
        purchase_reference = instance.reference
        purchase_amount = instance.amount
        node_id = node.id

        transaction.on_commit(
            lambda: distribute_referral_bonuses.delay(
                buyer_node_id=node_id,
                purchase_event_id=purchase_reference,
                purchase_amount=purchase_amount,
            )
        )


@receiver(post_save, sender=Withdrawal)
def handle_withdrawal_status_change(sender, instance, **kwargs):
    """Trigger background jobs only when status itself changes."""
    update_fields = kwargs.get("update_fields")
    # If update_fields is set and status was not part of the write, skip
    if update_fields is not None and "status" not in update_fields:
        return

    if instance.status == Withdrawal.Status.APPROVED:
        process_approved_withdrawal.delay(instance.id)
        logger.info(
            f"Withdrawal {instance.id} approved - queued for payment processing"
        )
    elif instance.status == Withdrawal.Status.REJECTED:
        handle_rejected_withdrawal.delay(instance.id)
        logger.info(f"Withdrawal {instance.id} rejected - queued for notification")


# Background tasks
@shared_task(bind=True)
def process_approved_withdrawal(self, withdrawal_id):
    """
    On APPROVED:
      1. Reserve funds on the wallet (idempotent).
      2. If payment simulation is on — simulate provider success, debit ledger,
         mark PROCESSED, and stamp payout_info as simulated.
      3. If simulation is off — leave status APPROVED with funds reserved
         until Hubtel/MoMo confirms a real payout. Never mark PROCESSED
         without a provider (or an explicit simulation).
    """
    from django.conf import settings

    try:
        with transaction.atomic():
            withdrawal = Withdrawal.objects.select_for_update().get(id=withdrawal_id)

            if withdrawal.status == Withdrawal.Status.PROCESSED:
                logger.info(f"Withdrawal {withdrawal_id} already processed — skip")
                return

            if withdrawal.status != Withdrawal.Status.APPROVED:
                logger.warning(
                    f"Withdrawal {withdrawal_id} status={withdrawal.status} "
                    f"— expected APPROVED, skip"
                )
                return

            # Idempotency: already reserved for payout dispatch
            payout_info = dict(withdrawal.payout_info or {})
            already_reserved = payout_info.get("payout_reserved") is True

            wallet = Wallet.objects.select_for_update().get(id=withdrawal.wallet_id)

            if not already_reserved:
                available = wallet.balance - wallet.reserved
                if withdrawal.amount > available:
                    logger.error(
                        f"Insufficient balance for withdrawal {withdrawal_id} "
                        f"available={available} requested={withdrawal.amount}"
                    )
                    withdrawal.status = Withdrawal.Status.REJECTED
                    withdrawal.save(update_fields=["status"])
                    return

                wallet.reserved += withdrawal.amount
                wallet.save(update_fields=["reserved", "updated_at"])

                payout_info["payout_reserved"] = True
                withdrawal.payout_info = payout_info
                withdrawal.save(update_fields=["payout_info", "updated_at"])
                logger.info(
                    f"Withdrawal {withdrawal_id} funds reserved "
                    f"amount={withdrawal.amount}"
                )

            # Live gateway not wired yet — do not pretend money left the platform
            if not settings.PAYMENT_SIMULATION_ENABLED:
                logger.warning(
                    f"Withdrawal {withdrawal_id} APPROVED and reserved — "
                    f"awaiting real payout provider (Hubtel). "
                    f"Not marking PROCESSED."
                )
                notify(
                    wallet.user,
                    title="Withdrawal approved",
                    message=(
                        f"Your withdrawal of {withdrawal.amount} {wallet.currency} "
                        f"has been approved and is awaiting payout."
                    ),
                    category=Notification.Category.WALLET,
                    channels=[Notification.Channel.IN_APP, Notification.Channel.SMS],
                )
                return

            # --- SIMULATION PATH (demo only) ---
            if Transaction.objects.filter(reference=f"WD_{withdrawal.id}").exists():
                logger.info(
                    f"Withdrawal {withdrawal_id} ledger debit already exists — skip"
                )
                return

            payout_info["simulated"] = True
            payout_info["gateway"] = "SIMULATION"
            withdrawal.payout_info = payout_info
            withdrawal.save(update_fields=["payout_info", "updated_at"])

            logger.warning(
                f"SIMULATED withdrawal payout for {withdrawal_id} — "
                f"no real money moved"
            )

            post_transaction(
                wallet_id=withdrawal.wallet_id,
                amount=withdrawal.amount,
                direction=Transaction.Direction.DEBIT,
                type=Transaction.Type.WITHDRAWAL,
                reference=f"WD_{withdrawal.id}",
                description=(
                    f"[SIMULATION] Withdrawal via "
                    f"{payout_info.get('method')}"
                ),
                payout_info=payout_info,
                against_reservation=True,
            )

            withdrawal.status = Withdrawal.Status.PROCESSED
            withdrawal.save(update_fields=["status", "updated_at"])

            notify(
                wallet.user,
                title="Withdrawal processed",
                message=(
                    f"Your withdrawal of {withdrawal.amount} {wallet.currency} "
                    f"has been processed."
                ),
                category=Notification.Category.WALLET,
                channels=[Notification.Channel.IN_APP, Notification.Channel.SMS],
            )

        logger.info(f"Withdrawal {withdrawal_id} processed (simulation)")

    except Exception as e:
        logger.error(f"Withdrawal processing failed: {e}")
        raise self.retry(countdown=60 * 5)


@shared_task
def handle_rejected_withdrawal(withdrawal_id):
    """Notify user about rejection"""
    withdrawal = Withdrawal.objects.get(id=withdrawal_id)
    notify(
        withdrawal.wallet.user,
        title="Withdrawal rejected",
        message=(
            f"Your withdrawal request of {withdrawal.amount} "
            f"{withdrawal.wallet.currency} was rejected. Contact support."
        ),
        category=Notification.Category.WALLET,
        channels=[
            Notification.Channel.IN_APP,
            Notification.Channel.EMAIL,
            Notification.Channel.SMS,
        ],
    )
    logger.info(f"Rejection notification sent for withdrawal {withdrawal_id}")
