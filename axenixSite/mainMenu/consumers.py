# mainMenu/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache
from .models import ChatMessage, Room
from datetime import datetime
from django.conf import settings
import os

@database_sync_to_async
def delete_room_from_db(slug):
    try:
        room_to_delete = Room.objects.prefetch_related('messages').get(slug=slug)
        
        messages = room_to_delete.messages.all()

        if messages:
            timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            log_filename = f"{slug}_{timestamp_str}.txt"
            log_filepath = os.path.join(settings.CHAT_LOGS_DIR, log_filename)
            
            print(f"--- [LOG] Сохраняю историю чата комнаты '{slug}' в файл: {log_filepath} ---")

            try:
                with open(log_filepath, 'w', encoding='utf-8') as log_file:
                    log_file.write(f"История чата для комнаты: {room_to_delete.name} ({slug})\n")
                    log_file.write(f"Комната создана: {room_to_delete.created_at.strftime('%Y-%m-%d %H:%M')}\n")
                    log_file.write(f"История сохранена: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
                    log_file.write("=" * 40 + "\n\n")
                    
                    for msg in messages:
                        msg_time = msg.timestamp.strftime('%H:%M:%S')
                        log_file.write(f"[{msg_time}] {msg.username_at_time}: {msg.text}\n")
                
                print(f"--- [LOG] История чата успешно сохранена. ---")
            except IOError as e:
                print(f"!!! [ERROR] Не удалось записать лог чата: {e} !!!")

        room_to_delete.delete()
        print(f"--- [DB] Комната '{slug}' и ее сообщения удалены из базы данных. ---")
        
        return True
        
    except Room.DoesNotExist:
        return False
@database_sync_to_async
def save_chat_message(room_slug, user, message_text):
    try:
        room = Room.objects.get(slug=room_slug)
        ChatMessage.objects.create(
            room=room,
            author=user,
            username_at_time=user.username,
            text=message_text
        )
    except Room.DoesNotExist:
        print(f"Ошибка сохранения сообщения: комната {room_slug} не найдена.")

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

        if message_type == 'chat_message':
            message = data['message']
            
            await save_chat_message(self.room_slug, self.user, message)

        
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
