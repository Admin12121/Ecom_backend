from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.contrib.auth.models import User
from .models import Notification
from .serializers import NotificationSerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework import viewsets, permissions
from rest_framework.permissions import IsAuthenticated , IsAuthenticatedOrReadOnly, AllowAny

def send_notifications():
    notifications = Notification.objects.filter(sent=False, send_time__lte=timezone.now())
    for notification in notifications:
        if '@all' in notification.tags:
            users = User.objects.all()
        elif '@random' in notification.tags:
            count = int(notification.tags.split(' ')[-1])
            users = User.objects.order_by('?')[:count]
        else:
            users = notification.user.all()

        for user in users:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"user_{user.id}",
                {
                    'type': 'send_notification',
                    'message': {
                        'title': notification.title,
                        'message': notification.message,
                        'link': notification.link,
                    }
                }
            )
        
        notification.sent = True
        notification.save()

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]