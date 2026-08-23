"""
Single entry point for sending notifications.

Only IN_APP is actually delivered right now — it's just a database row the
frontend can poll/list. EMAIL and SMS are recorded with status=ON_HOLD so
every call site is already wired for them; once real senders exist, flipping
them into ACTIVE_CHANNELS below is the only change needed.
"""
import logging

from .models import Notification

logger = logging.getLogger(__name__)

ACTIVE_CHANNELS = {Notification.Channel.IN_APP}
ON_HOLD_CHANNELS = {Notification.Channel.EMAIL, Notification.Channel.SMS}


def notify(
    recipient,
    title,
    message,
    category=Notification.Category.SYSTEM,
    channels=None,
    metadata=None,
):
    """Create a Notification row for `recipient` on each requested channel."""
    channels = channels or [Notification.Channel.IN_APP]
    created = []

    for channel in channels:
        if channel in ACTIVE_CHANNELS:
            status = Notification.Status.SENT
        elif channel in ON_HOLD_CHANNELS:
            status = Notification.Status.ON_HOLD
            logger.info(
                f"Notification channel={channel} is on hold — recorded only, "
                f"not delivered (recipient={recipient.id})"
            )
        else:
            logger.warning(f"Unknown notification channel={channel} — skipping")
            continue

        created.append(
            Notification.objects.create(
                recipient=recipient,
                category=category,
                channel=channel,
                title=title,
                message=message,
                status=status,
                metadata=metadata or {},
            )
        )

    return created
