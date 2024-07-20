from django.db import models
from accounts.models import User
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.URLField(max_length=500, null=True, blank=True)
    send_time = models.DateTimeField(default=timezone.now)
    sent = models.BooleanField(default=False)
    seen = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    tags = models.CharField(max_length=255, null=True, blank=True)  # E.g., '@all, @random, @random 100'
    type = models.CharField(max_length=50, null=True, blank=True)  # New field for type

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        channel_layer = get_channel_layer()
        data = {
            "type": self.type,
            "title": self.title,
            "message": self.message,
            "link": self.link,
            "send_time": self.send_time.isoformat(),
            "tags": self.tags,
            "user_id": self.user.id if self.user else None
        }

        # Send to specific user if user exists
        if self.user:
            async_to_sync(channel_layer.group_send)(
                f"notifications_{self.user.id}",
                {"type": "send_notification", "message": json.dumps(data)}
            )
        # Handle tags
        if self.tags:
            if '@all' in self.tags:
                async_to_sync(channel_layer.group_send)(
                    "notifications",
                    {"type": "send_notification", "message": json.dumps(data)}
                )
            if '@random100' in self.tags:
                # Fetch 100 random users
                random_users = User.objects.order_by('?')[:100]
                for user in random_users:
                    async_to_sync(channel_layer.group_send)(
                        f"notifications_{user.id}",
                        {"type": "send_notification", "message": json.dumps(data)}
                    )

        super(Notification, self).save(*args, **kwargs)