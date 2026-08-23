from django.db import models
from django.conf import settings


class PendingReferral(models.Model):
    referred_user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pending_referral",
    )
    referrer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pending_referrals",
    )
    referral_code = models.CharField(max_length=20)
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Pending Referral"
        verbose_name_plural = "Pending Referrals"

    def __str__(self):
        return (
            f"{self.referred_user} referred by {self.referrer} ({self.referral_code})"
        )


class ReferralNode(models.Model):

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="referral_node"
    )
    parent_node = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True, related_name="children"
    )
    left_child = models.OneToOneField(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="as_left_child",
    )
    right_child = models.OneToOneField(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="as_right_child",
    )
    root_node = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="tree_members",
    )
    referral_code = models.CharField(max_length=20, unique=True)
    depth = models.PositiveIntegerField()
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.ACTIVE
    )
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Referral Node"
        verbose_name_plural = "Referral Nodes"

    def __str__(self):
        return f"Node({self.user}) depth={self.depth} status={self.status}"

    @property
    def is_full(self):
        return self.left_child is not None and self.right_child is not None

    @property
    def available_side(self):
        if self.left_child is None:
            return "LEFT"
        if self.right_child is None:
            return "RIGHT"
        return None


class PlacementQueue(models.Model):

    class Side(models.TextChoices):
        LEFT = "LEFT", "Left"
        RIGHT = "RIGHT", "Right"

    root_node = models.OneToOneField(
        ReferralNode, on_delete=models.PROTECT, related_name="placement_queue"
    )
    next_available_node = models.ForeignKey(
        ReferralNode, on_delete=models.PROTECT, related_name="queued_as_next"
    )
    side = models.CharField(max_length=5, choices=Side.choices, default=Side.LEFT)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Placement Queue"
        verbose_name_plural = "Placement Queues"

    def __str__(self):
        return f"Queue(tree={self.root_node}) → node={self.next_available_node} side={self.side}"

    def place(self, new_node):
        """
        Attaches new_node to the current bookmarked slot
        then advances the bookmark to the next available slot.
        Must be called inside a transaction.atomic() block.
        """
        target_node = self.next_available_node
        side = self.side

        # attach new node to the target
        if side == self.Side.LEFT:
            target_node.left_child = new_node
        else:
            target_node.right_child = new_node

        target_node.save(
            update_fields=["left_child" if side == self.Side.LEFT else "right_child"]
        )

        # advance the bookmark
        next_node, next_side = self._find_next_available(target_node)
        self.next_available_node = next_node
        self.side = next_side
        self.save(update_fields=["next_available_node", "side", "updated_at"])

    def _find_next_available(self, just_filled_node):
        """
        Finds the next BFS slot after just_filled_node was filled.
        Checks the other side of just_filled_node first,
        then walks up and across the tree.
        """
        # check if the other side of the same node is still open
        if just_filled_node.left_child is None:
            return just_filled_node, self.Side.LEFT
        if just_filled_node.right_child is None:
            return just_filled_node, self.Side.RIGHT

        # both sides of just_filled_node are now full
        # walk up the tree BFS style to find the next open slot
        from collections import deque

        queue = deque()
        queue.append(self.root_node)

        while queue:
            node = queue.popleft()

            if node.left_child is None:
                return node, self.Side.LEFT
            else:
                queue.append(node.left_child)

            if node.right_child is None:
                return node, self.Side.RIGHT
            else:
                queue.append(node.right_child)


class ReferralReward(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    beneficiary = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="referral_rewards_received",
    )
    source_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="referral_rewards_triggered",
    )
    purchase_event_id = models.CharField(max_length=100)
    percentage_applied = models.PositiveIntegerField()
    depth_difference = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    wallet_transaction = models.OneToOneField(
        "wallet.Transaction",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="referral_reward",
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Referral Reward"
        verbose_name_plural = "Referral Rewards"
        constraints = [
            models.UniqueConstraint(
                fields=["source_user", "beneficiary", "purchase_event_id"],
                name="unique_reward_per_purchase_per_ancestor",
            )
        ]

    def __str__(self):
        return (
            f"Reward({self.beneficiary} ← {self.source_user} "
            f"{self.percentage_applied}% = {self.amount})"
        )
