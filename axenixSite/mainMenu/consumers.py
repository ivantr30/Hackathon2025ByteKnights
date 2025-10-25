# mainMenu/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer

rooms = {}

class ConferenceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get('user')
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return
            
        self.room_slug = self.scope['url_route']['kwargs']['room_slug']
        self.room_group_name = f'conference_{self.room_slug}'

        if self.room_slug not in rooms:
            rooms[self.room_slug] = {}

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        
        await self.send(text_data=json.dumps({
            'type': 'welcome',
            'peer_id': self.channel_name
        }))

    async def disconnect(self, close_code):
        if not hasattr(self, 'room_slug'): return
        if self.room_slug in rooms and self.channel_name in rooms[self.room_slug]:
            del rooms[self.room_slug][self.channel_name]
            if not rooms[self.room_slug]: del rooms[self.room_slug]
        await self.channel_layer.group_send(self.room_group_name, {'type': 'user.disconnect', 'peer_id': self.channel_name})
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'chat_message':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat.message', 
                    'message': data['message'],
                    'username': self.user.username,
                    'sender_channel': self.channel_name 
                }
            )
            return

        if message_type == 'user_ready':
            existing_peers = rooms.get(self.room_slug, {})
            await self.send(text_data=json.dumps({'type': 'get_ready_users', 'peers': existing_peers}))
            rooms[self.room_slug][self.channel_name] = {'username': self.user.username}
            await self.channel_layer.group_send(self.room_group_name, {'type': 'new.user.announce', 'peer_id': self.channel_name, 'username': self.user.username})
            return

        target_peer_id = data.get('target_peer_id')
        if target_peer_id:
            data['peer_id'] = self.channel_name
            await self.channel_layer.send(target_peer_id, {'type': 'webrtc.signal', 'data': data})


    async def chat_message(self, event):
        """
        Рассылает сообщение чата всем, КРОМЕ отправителя.
        """
        
        if self.channel_name == event['sender_channel']:
            return

        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'username': event['username'],
            'peer_id': event['sender_channel'] 
        }))

    async def new_user_announce(self, event):
        if self.channel_name != event['peer_id']:
            await self.send(text_data=json.dumps(event))

    async def user_disconnect(self, event):
        await self.send(text_data=json.dumps(event))

    async def webrtc_signal(self, event):
        await self.send(text_data=json.dumps(event['data']))
