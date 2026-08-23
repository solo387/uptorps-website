import uuid
from django.db import transaction
from referral.models import ReferralNode, PlacementQueue

def validate_referral_code(code):
    """
    Validates a referral code at the point of user registration.

    Returns the ReferralNode if the code is valid and active.
    Returns None if the code does not exist or belongs to an inactive node.
    """
    if not code:
        return None

    try:
        node = ReferralNode.objects.select_related("user").get(
            referral_code=code, status=ReferralNode.Status.ACTIVE
        )
        return node

    except ReferralNode.DoesNotExist:
        return None


def generate_referral_code(user):
    """
    Generates a unique referral code for a user.
    Format: first 4 characters of username + 6 random characters
    Example: JOHN2X9K3P
    Checks for collisions before returning.
    """
    while True:
        prefix = user.username[:4].upper()
        random_part = uuid.uuid4().hex[:6].upper()
        code = f"{prefix}{random_part}"

        # check it does not already exist
        if not ReferralNode.objects.filter(referral_code=code).exists():
            return code


def get_reward_percentage(depth_difference):
    """
    Returns the reward percentage based on how many levels
    above the buyer the ancestor is.
    """
    percentages = {
        1: 20,
        2: 10,
        3: 5,
        4: 3,
    }
    # level 5 and beyond locks at 1%
    return percentages.get(depth_difference, 1)


def find_next_available(root_node):
    from referral.models import PlacementQueue
    from collections import deque

    bfs_queue = deque()
    bfs_queue.append(root_node.id)  # store ID not object

    while bfs_queue:
        node_id = bfs_queue.popleft()
        node    = ReferralNode.objects.get(id=node_id)  # fresh from DB every time

        if node.left_child_id is None:
            return node, PlacementQueue.Side.LEFT

        bfs_queue.append(node.left_child_id)  # store ID not object

        if node.right_child_id is None:
            return node, PlacementQueue.Side.RIGHT

        bfs_queue.append(node.right_child_id)  # store ID not object

def place_new_node(user, referral_code=None, version=1):
    """
    Places a new premium user into the referral tree.

    If referral_code is None — creates a new independent tree (root node).
    If referral_code is provided — places the user inside the referrer's tree
    using the BFS placement queue.

    Returns the newly created ReferralNode.
    """
    with transaction.atomic():

        if referral_code is None:
            # ── CASE 1: ROOT USER ──────────────────────────────────────
            # no referral code means this user starts their own tree

            # step 1 — create the node (root_node temporarily null)
            node = ReferralNode.objects.create(
                user=user,
                parent_node=None,
                left_child=None,
                right_child=None,
                root_node=None,
                depth=1,
                referral_code=generate_referral_code(user),
                status=ReferralNode.Status.ACTIVE,
                version= version,
            )

            # step 2 — point root_node to itself now that it has an ID
            node.root_node = node
            node.save(update_fields=["root_node"])

            # step 3 — create the placement queue for this new tree
            # bookmark starts pointing at the root's left slot
            PlacementQueue.objects.create(
                root_node=node, next_available_node=node, side=PlacementQueue.Side.LEFT
            )

        else:
            # ── CASE 2: REFERRED USER ──────────────────────────────────
            # find the referrer's node to get their tree's root
            referrer_node = ReferralNode.objects.select_related("root_node").get(
                referral_code=referral_code, status=ReferralNode.Status.ACTIVE
            )

            root_node = referrer_node.root_node

            # lock the placement queue for this tree
            # prevents two simultaneous placements corrupting the bookmark
            queue = PlacementQueue.objects.select_for_update().get(root_node=root_node)

            # check referral code owner's slots first
            # they should benefit directly from people using their code
            referrer_node.refresh_from_db()

            # check referral code owner's slots first
            if referrer_node.left_child_id is None:
                parent_node = referrer_node
                side = PlacementQueue.Side.LEFT

            elif referrer_node.right_child_id is None:
                parent_node = referrer_node
                side = PlacementQueue.Side.RIGHT

            else:
                parent_node = queue.next_available_node
                side = queue.side

            # step 1 — create the new node
            node = ReferralNode.objects.create(
                user=user,
                parent_node=parent_node,
                left_child=None,
                right_child=None,
                root_node=root_node,
                depth=parent_node.depth + 1,
                referral_code=generate_referral_code(user),
                status=ReferralNode.Status.ACTIVE,
                version=version,
            )

            # step 2 — attach node to parent's correct slot
            if side == PlacementQueue.Side.LEFT:
                parent_node.left_child = node
            else:
                parent_node.right_child = node

            parent_node.save(
                update_fields=[
                    "left_child" if side == PlacementQueue.Side.LEFT else "right_child"
                ]
            )

            # step 3 — advance the placement queue bookmark
            # refresh parent to clear Django's cache before checking slots
            # parent_node.refresh_from_db()

            if parent_node.id == queue.next_available_node_id:
                # we used the BFS slot — advance the bookmark
                parent_node.refresh_from_db()

                if side == PlacementQueue.Side.LEFT and parent_node.right_child_id is None:
                    # fast path — other side of same node still open
                    next_node = parent_node
                    next_side = PlacementQueue.Side.RIGHT
                else:
                    # both sides full — BFS scan for next slot
                    root_node.refresh_from_db()
                    next_node, next_side = find_next_available(root_node)

                queue.next_available_node = next_node
                queue.side = next_side
                queue.save(update_fields=['next_available_node', 'side', 'updated_at'])

    return node

def deactivate_referral_node(user):
    from django.utils import timezone
    user_node = ReferralNode.objects.get(user= user)
    user_node.status = ReferralNode.Status.INACTIVE
    user_node.deactivated_at = timezone.now()
    user_node.save()