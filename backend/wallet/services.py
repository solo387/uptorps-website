# wallet/services.py
"""
Payment checkout helpers.

Until Hubtel access is approved, checkout runs in **simulation mode** only
(see ``PAYMENT_SIMULATION_ENABLED`` in settings). Responses are labeled so
they cannot be mistaken for a live gateway.
"""
import logging
import random

from celery import shared_task
from django.conf import settings

from accounts.models import User
from premium.models import PremiumPackage
from .models import Transaction, Wallet

logger = logging.getLogger(__name__)

SIMULATION_MESSAGE = (
    "SIMULATION ONLY — no real money moved. "
    "Replace with Hubtel when API access is approved."
)


def onlineCheckout(packageID, reference, payout_info):
    """
    Create a PENDING premium payment and trigger the (simulated) webhook.

    Returns:
        (ok: bool, checkout_url: str, meta: dict)
    """
    if not settings.PAYMENT_SIMULATION_ENABLED:
        logger.error(
            "onlineCheckout blocked — PAYMENT_SIMULATION_ENABLED is False "
            "and no live gateway is configured yet"
        )
        return (
            False,
            "",
            {
                "simulated": False,
                "message": (
                    "Payment gateway is not configured. "
                    "Enable PAYMENT_SIMULATION_ENABLED for demos, "
                    "or wire Hubtel for live payments."
                ),
            },
        )

    try:
        package = PremiumPackage.objects.get(id=packageID)
        premiumAccount = User.objects.get(email="premium_wallet@uptorps.com")
        wallet = Wallet.objects.get(user=premiumAccount)
    except (PremiumPackage.DoesNotExist, User.DoesNotExist, Wallet.DoesNotExist):
        return False, "", {"simulated": True, "message": "Checkout setup failed."}

    # Mark metadata so ledger/signals know this was not a live gateway
    payout_info["package_id"] = str(package.id)
    payout_info["simulated"] = True
    payout_info["gateway"] = "SIMULATION"

    Transaction.objects.create(
        wallet=wallet,
        type=Transaction.Type.PREMIUM_PAYMENT,
        direction=Transaction.Direction.CREDIT,
        amount=package.price,
        status=Transaction.Status.PENDING,
        reference=reference,
        payout_info=payout_info,
        description=f"[SIMULATION] Premium purchase: {package.name}",
    )

    outcome = _simulation_outcome()
    logger.warning(
        "SIMULATED checkout reference=%s outcome=%s url=%s",
        reference,
        "success" if outcome else "failure",
        settings.SIMULATED_CHECKOUT_URL,
    )
    paymentwebhook.delay(outcome, reference)

    return (
        True,
        settings.SIMULATED_CHECKOUT_URL,
        {
            "simulated": True,
            "message": SIMULATION_MESSAGE,
            "simulation_outcome": "success" if outcome else "failure",
        },
    )


def _simulation_outcome():
    """Resolve success/failure from PAYMENT_SIMULATION_OUTCOME."""
    mode = getattr(settings, "PAYMENT_SIMULATION_OUTCOME", "success")
    if mode == "failure":
        return False
    if mode == "random":
        return random.choice([True, False])
    # default / "success"
    return True


@shared_task
def paymentwebhook(status, reference):
    if status:
        successfulPurchase.delay(reference)
    else:
        failuerPurchase.delay(reference)


@shared_task
def successfulPurchase(reference):
    """Mark PENDING → COMPLETED exactly once (webhook / simulation retries safe)."""
    from django.db import transaction

    with transaction.atomic():
        try:
            transaction_obj = Transaction.objects.select_for_update().get(
                reference=reference
            )
        except Transaction.DoesNotExist:
            logger.error(f"successfulPurchase: reference={reference} not found")
            return

        if transaction_obj.status == Transaction.Status.COMPLETED:
            logger.info(f"successfulPurchase: reference={reference} already COMPLETED")
            return

        if transaction_obj.status != Transaction.Status.PENDING:
            logger.warning(
                f"successfulPurchase: reference={reference} "
                f"status={transaction_obj.status} — expected PENDING"
            )
            return

        transaction_obj.status = Transaction.Status.COMPLETED
        transaction_obj.save(update_fields=["status", "updated_at"])


@shared_task
def failuerPurchase(reference):
    from django.db import transaction

    with transaction.atomic():
        try:
            transaction_obj = Transaction.objects.select_for_update().get(
                reference=reference
            )
        except Transaction.DoesNotExist:
            logger.error(f"failuerPurchase: reference={reference} not found")
            return

        if transaction_obj.status in (
            Transaction.Status.FAILED,
            Transaction.Status.COMPLETED,
        ):
            logger.info(
                f"failuerPurchase: reference={reference} "
                f"already {transaction_obj.status}"
            )
            return

        transaction_obj.status = Transaction.Status.FAILED
        transaction_obj.save(update_fields=["status", "updated_at"])
