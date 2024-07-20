# import json
# from channels.generic.websocket import AsyncWebsocketConsumer

# class NotificationConsumer(AsyncWebsocketConsumer):

#     async def connect(self):
#         self.room_group_name = "notifications"
#         await self.channel_layer.group_add(self.room_group_name, self.channel_name)
#         await self.accept()

#     async def disconnect(self, close_code):
#         await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

#     async def receive(self, text_data):
#         data = json.loads(text_data)
#         await self.send(text_data=json.dumps({
#             'message': 'received'
#         }))

#     async def send_notification(self, event):
#         message = event['message']
#         await self.send(text_data=json.dumps({
#             'message': message
#         }))
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = await self.get_user_from_token()
        if self.user:
            self.room_group_name = f"notifications_{self.user.id}"
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            # Add user to the common "notifications" group
            await self.channel_layer.group_add("notifications", self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if self.user:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            await self.channel_layer.group_discard("notifications", self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        await self.send(text_data=json.dumps({
            'message': 'received'
        }))

    async def send_notification(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'message': message
        }))

    async def get_user_from_token(self):
        try:
            token = self.scope['query_string'].decode().split('=')[1]
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            User = get_user_model()
            return await sync_to_async(User.objects.get)(id=user_id)
        except Exception as e:
            print(f"Failed to authenticate WebSocket connection: {e}")
            return None
