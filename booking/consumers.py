# booking/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope['user'].is_staff:
            self.room_group_name = 'admin_notifications'
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()

    async def disconnect(self, close_code):
        if self.scope['user'].is_staff:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def send_notification(self, event):
        await self.send(text_data=json.dumps({'message': event['message']}))