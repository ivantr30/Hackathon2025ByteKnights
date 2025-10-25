# mainMenu/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache
from .models import Room

@database_sync_to_async
def delete_room_from_db(slug):
    try:
        room = Room.objects.get(slug=slug)
        room.delete()
        print(f"--- [DB] Комната '{slug}' удалена из базы данных, так как опустела. ---")
        return True
    except Room.DoesNotExist:
        return False

class ConferenceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get('user')
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return
            
        self.room_slug = self.scope['url_route']['kwargs']['room_slug']
        self.room_group_name = f'conference_{self.room_slug}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        self.cache_key = f'room_{self.room_slug}_user_count'
        new_count = cache.get(self.cache_key, 0) + 1
        cache.set(self.cache_key, new_count)
        print(f"--- [CONNECT] Пользователь вошел. Участников в комнате: {new_count}")

    async def disconnect(self, close_code):
        if not hasattr(self, 'room_slug'): return

        user_count = cache.get(self.cache_key, 1) - 1
        if user_count > 0:
            cache.set(self.cache_key, user_count)
        else:
            cache.delete(self.cache_key)
        
        print(f"--- [DISCONNECT] Пользователь вышел. Осталось участников: {user_count}")
        
        if user_count <= 0:
            await delete_room_from_db(self.room_slug)

        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'user.disconnect', 'peer_id': self.channel_name}
        )
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        data['sender_channel'] = self.channel_name
        data['username'] = self.user.username
        
        target_peer_id = data.get('target_peer_id')

        if target_peer_id:
            await self.channel_layer.send(
                target_peer_id,
                {'type': 'webrtc.signal', 'data': data}
            )
        else:
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'broadcast.message', 'data': data}
            )

    async def broadcast_message(self, event):
        if self.channel_name != event['data']['sender_channel']:
            await self.send(text_data=json.dumps(event['data']))

    async def webrtc_signal(self, event):
        await self.send(text_data=json.dumps(event['data']))
        
    async def user_disconnect(self, event):
        await self.send(text_data=json.dumps(event))
