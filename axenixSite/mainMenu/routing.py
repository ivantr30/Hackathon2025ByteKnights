from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"^room/(?P<room_slug>[^/]+)/$", consumers.ConferenceConsumer.as_asgi()),
]