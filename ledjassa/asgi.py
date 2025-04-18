import os
import django

# 👉 Étape 1 : configure Django d'abord
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ledjassa.settings')
django.setup()

# 👉 Étape 2 : maintenant que Django est prêt, fais les imports liés au projet
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from djassa import consumers
import djassa.routing

# 👉 Étape 3 : configuration de l'application ASGI
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("ws/likes/<int:publication_id>/", consumers.LikeConsumer.as_asgi()),
            *djassa.routing.websocket_urlpatterns
        ])
    ),
})
