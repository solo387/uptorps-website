# notifications/views.py
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(APIView):
    """In-app notification feed for the current user. EMAIL/SMS rows are
    delivery bookkeeping only and are not shown here."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(
            recipient=request.user, channel=Notification.Channel.IN_APP
        )
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)


class NotificationUnreadCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(
            recipient=request.user,
            channel=Notification.Channel.IN_APP,
            is_read=False,
        ).count()
        return Response({"unread_count": count})


class NotificationMarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        notification = get_object_or_404(
            Notification, id=id, recipient=request.user
        )
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=["is_read", "read_at"])
        return Response(NotificationSerializer(notification).data)


class NotificationMarkAllReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        updated = Notification.objects.filter(
            recipient=request.user,
            channel=Notification.Channel.IN_APP,
            is_read=False,
        ).update(is_read=True, read_at=timezone.now())
        return Response({"marked_read": updated})
