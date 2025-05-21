# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from customers.models import TopUpHistory  # ✅ Đúng app

class TopupConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.topup_id = self.scope['url_route']['kwargs']['topup_id']
        self.user = self.scope["user"]

        is_owner = await self.check_ownership()
        if not is_owner:
            await self.close()
            return

        self.group_name = f"topup_{self.topup_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    @database_sync_to_async
    def check_ownership(self):
        try:
            topup = TopUpHistory.objects.get(id=self.topup_id)
            return topup.user == self.user
        except TopUpHistory.DoesNotExist:
            return False

    async def topup_success(self, event):
        await self.send(text_data=json.dumps({
            'status': 'success',
            'new_balance': event.get("new_balance"),
        }))

    async def topup_timeout(self, event):
        await self.send(text_data=json.dumps({
            'status': 'failed',
        }))
class AccessEventConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "access_event"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        print(f"✅ WebSocket client joined group {self.group_name}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def access_event(self, event):
        await self.send(text_data=json.dumps(event))