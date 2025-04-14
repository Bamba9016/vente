import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import djassa.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ledjassa.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            djassa.routing.websocket_urlpatterns
        )
    ),
})
