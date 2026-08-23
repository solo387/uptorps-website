import logging
from celery import shared_task
from django.db import transaction, IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from wallet.models import Transaction, Wallet
from referral.models import ReferralNode, ReferralReward
from referral.utils import get_reward_percentage
from decimal import Decimal

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def distribute_referral_bonuses(
    self, buyer_node_id, purchase_event_id, purchase_amount
):
    """
    Walks up the ancestor chain of the buyer and credits
    each active ancestor's wallet with the appropriate reward.

    Called after a premium purchase is confirmed.
    Runs asynchronously — decoupled from the purchase transaction.
    """
    logger.info(
        f"Starting bonus distribution for buyer_node={buyer_node_id} "
        f"purchase_event={purchase_event_id} amount={purchase_amount}"
    )

    try:
        buyer_node = ReferralNode.objects.select_related("parent_node").get(
            id=buyer_node_id
        )
    except ObjectDoesNotExist:
        logger.error(f"ReferralNode {buyer_node_id} not found — aborting task")
        return

    current_node = buyer_node.parent_node

    while current_node is not None:
        try:
            _process_ancestor_reward(
                ancestor=current_node,
                buyer_node=buyer_node,
                purchase_event_id=purchase_event_id,
                purchase_amount=purchase_amount,
            )
        except Exception as exc:
            logger.error(
                f"Ancestor reward failed ancestor={current_node.user_id} "
                f"error={exc} — will retry whole task"
            )
            raise self.retry(exc=exc)

        current_node = (
            ReferralNode.objects.select_related("parent_node")
            .get(id=current_node.id)
            .parent_node
        )

    logger.info(f"Bonus distribution completed for purchase_event={purchase_event_id}")


def _process_ancestor_reward(ancestor, buyer_node, purchase_event_id, purchase_amount):
    """
    Handles the reward logic for a single ancestor.
    Idempotent via unique (source, beneficiary, purchase_event) + ledger reference.
    """
    from wallet.utils import post_transaction

    depth_difference = buyer_node.depth - ancestor.depth
    percentage = get_reward_percentage(depth_difference)
    amount = round(
        Decimal(str(purchase_amount)) * (Decimal(percentage) / Decimal(100)), 2
    )

    logger.info(
        f"Processing ancestor={ancestor.user_id} "
        f"depth_diff={depth_difference} "
        f"percentage={percentage}% amount={amount}"
    )

    if ancestor.status == ReferralNode.Status.INACTIVE:
        logger.info(f"Ancestor {ancestor.user_id} is INACTIVE — skipping payment")
        return

    try:
        with transaction.atomic():
            try:
                reward = ReferralReward.objects.select_for_update().get(
                    source_user=buyer_node.user,
                    beneficiary=ancestor.user,
                    purchase_event_id=purchase_event_id,
                )
                created = False
            except ReferralReward.DoesNotExist:
                try:
                    reward = ReferralReward.objects.create(
                        source_user=buyer_node.user,
                        beneficiary=ancestor.user,
                        purchase_event_id=purchase_event_id,
                        percentage_applied=percentage,
                        depth_difference=depth_difference,
                        amount=amount,
                        status=ReferralReward.Status.PENDING,
                    )
                    created = True
                except IntegrityError:
                    reward = ReferralReward.objects.select_for_update().get(
                        source_user=buyer_node.user,
                        beneficiary=ancestor.user,
                        purchase_event_id=purchase_event_id,
                    )
                    created = False

            if not created and reward.status == ReferralReward.Status.COMPLETED:
                logger.info(
                    f"Reward already COMPLETED for ancestor={ancestor.user_id} "
                    f"purchase={purchase_event_id} — skipping"
                )
                return

            if not created:
                reward = ReferralReward.objects.select_for_update().get(pk=reward.pk)

            try:
                wallet = Wallet.objects.select_for_update().get(user=ancestor.user)
            except Wallet.DoesNotExist:
                logger.error(
                    f"No wallet for ancestor={ancestor.user_id} — marking FAILED"
                )
                reward.status = ReferralReward.Status.FAILED
                reward.save(update_fields=["status"])
                return

            if reward.wallet_transaction_id:
                if reward.status != ReferralReward.Status.COMPLETED:
                    reward.status = ReferralReward.Status.COMPLETED
                    reward.save(update_fields=["status"])
                return

            ledger = post_transaction(
                wallet_id=wallet.id,
                amount=amount,
                direction=Transaction.Direction.CREDIT,
                type=Transaction.Type.REFERRAL_BONUS,
                reference=f"referral_reward_{reward.id}",
                description=(
                    f"Referral bonus — {percentage}% from "
                    f"{buyer_node.user.get_full_name()}'s premium purchase"
                ),
                payout_info={"email": ancestor.user.email},
            )

            reward.wallet_transaction = ledger
            reward.status = ReferralReward.Status.COMPLETED
            reward.save(update_fields=["wallet_transaction", "status"])

            logger.info(
                f"Reward COMPLETED for ancestor={ancestor.user_id} amount={amount}"
            )

    except Exception as exc:
        try:
            ReferralReward.objects.filter(
                source_user=buyer_node.user,
                beneficiary=ancestor.user,
                purchase_event_id=purchase_event_id,
            ).exclude(status=ReferralReward.Status.COMPLETED).update(
                status=ReferralReward.Status.FAILED
            )
        except Exception:
            pass

        logger.error(
            f"Failed to process reward for ancestor={ancestor.user_id} "
            f"error={str(exc)}"
        )
        raise
