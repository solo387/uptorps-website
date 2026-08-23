from django.db.models import Sum, Case, When, F, DecimalField
from django.db import transaction
from decimal import Decimal
import logging

from wallet.models import Wallet, Transaction

logger = logging.getLogger(__name__)


def reconcile_wallet(wallet_id):
    """
    Recalculates wallet balance from the ledger and corrects
    the cached balance if they differ. Locks the wallet row.
    """
    with transaction.atomic():
        wallet = Wallet.objects.select_for_update().get(id=wallet_id)

        result = Transaction.objects.filter(
            wallet_id=wallet_id, status=Transaction.Status.COMPLETED
        ).aggregate(
            ledger_balance=Sum(
                Case(
                    When(direction=Transaction.Direction.CREDIT, then=F("amount")),
                    When(direction=Transaction.Direction.DEBIT, then=-F("amount")),
                    output_field=DecimalField(),
                )
            )
        )

        ledger_balance = result["ledger_balance"] or Decimal("0")

        if wallet.balance != ledger_balance:
            logger.warning(
                f"Balance mismatch on wallet {wallet_id} — "
                f"cached={wallet.balance} ledger={ledger_balance} — correcting"
            )
            wallet.balance = ledger_balance
            wallet.save(update_fields=["balance", "updated_at"])

        return ledger_balance


def check_withdrawal_threshold(wallet_id):
    """
    Called after credit ledger entries commit.
    Uses wallet_id (not a stale instance) and is safe to call more than once —
    ``trigger_premium_expiry`` itself is idempotent.
    """
    try:
        wallet = Wallet.objects.select_related("user").get(id=wallet_id)
    except Wallet.DoesNotExist:
        return

    if wallet.status != Wallet.Status.ACTIVE:
        return

    user = wallet.user
    from accounts.models import User

    premium_roles = [User.Roles.PREMIUM_STUDENT, User.Roles.PREMIUM_TEACHER]
    if user.role not in premium_roles:
        return

    from premium.models import UserPremiumSubscription

    subscription = (
        UserPremiumSubscription.objects.filter(
            user=user, status=UserPremiumSubscription.Status.ACTIVE
        )
        .select_related("package")
        .first()
    )

    if not subscription:
        logger.warning(
            f"No active subscription found for premium user={user.id} "
            f"wallet={wallet.id} — skipping threshold check"
        )
        return

    threshold = subscription.package.withdrawal_threshold

    total_credit = (
        Transaction.objects.filter(
            wallet=wallet,
            status=Transaction.Status.COMPLETED,
            direction=Transaction.Direction.CREDIT,
        ).aggregate(total=Sum("amount"))["total"]
        or 0
    )

    logger.info(
        f"Threshold check — wallet={wallet.id} "
        f"total_credit={total_credit} threshold={threshold}"
    )

    if total_credit >= threshold:
        logger.info(
            f"Threshold hit — wallet={wallet.id} "
            f"total_credit={total_credit} threshold={threshold} "
            f"firing expiry task"
        )
        from wallet.tasks import trigger_premium_expiry

        trigger_premium_expiry.delay(str(wallet.id), subscription.id)


def post_transaction(
    wallet_id,
    amount,
    direction,
    type,
    reference,
    description="",
    payout_info=None,
    against_reservation=False,
):
    """
    Single entry point for financial movements.

    - Locks the wallet with ``select_for_update``
    - Idempotent on ``reference`` (returns existing row if already posted)
    - ``against_reservation=True`` for completing a reserved withdrawal:
      allows debiting funds that are already in ``reserved`` and reduces
      ``reserved`` in the same atomic block
    """
    if payout_info is None:
        payout_info = {}

    amount = Decimal(str(amount))

    with transaction.atomic():
        wallet = Wallet.objects.select_for_update().get(id=wallet_id)

        existing = Transaction.objects.filter(reference=reference).first()
        if existing:
            logger.info(
                f"Transaction reference={reference} already exists — idempotent skip"
            )
            return existing

        if direction == Transaction.Direction.DEBIT:
            if against_reservation:
                if amount > wallet.balance or amount > wallet.reserved:
                    raise ValueError(
                        f"Insufficient reserved funds on wallet {wallet_id} — "
                        f"balance={wallet.balance} reserved={wallet.reserved} "
                        f"requested={amount}"
                    )
            else:
                available = wallet.balance - wallet.reserved
                if amount > available:
                    raise ValueError(
                        f"Insufficient balance on wallet {wallet_id} — "
                        f"available={available} requested={amount}"
                    )

        ledger = Transaction.objects.create(
            wallet=wallet,
            type=type,
            direction=direction,
            amount=amount,
            status=Transaction.Status.COMPLETED,
            reference=reference,
            description=description,
            payout_info=payout_info,
        )

        if against_reservation and direction == Transaction.Direction.DEBIT:
            from django.utils import timezone

            Wallet.objects.filter(pk=wallet.pk).update(
                reserved=F("reserved") - amount,
                updated_at=timezone.now(),
            )

        logger.info(
            f"Transaction posted — wallet={wallet_id} "
            f"type={type} direction={direction} amount={amount} "
            f"reference={reference} against_reservation={against_reservation}"
        )

    return ledger
