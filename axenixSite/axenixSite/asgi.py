
import os
from django.core.asgi import get_asgi_application

# Сначала настраиваем переменную окружения
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'axenixSite.settings')

# Сначала получаем стандартное Django ASGI-приложение
django_asgi_app = get_asgi_application()

# ТЕПЕРЬ, после этого, импортируем все для Channels
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import mainMenu.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(mainMenu.routing.websocket_urlpatterns)
    ),
})