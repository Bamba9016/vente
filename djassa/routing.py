from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<user_id>\d+)/$', consumers.PrivateChatConsumer.as_asgi()),
    re_path(r'ws/likes/$', consumers.LikeConsumer.as_asgi()),
    re_path(r'ws/publication/(?P<publication_id>\d+)/comments/$', consumers.CommentConsumer.as_asgi()),
    re_path(r'ws/navigation/$', consumers.NavigationConsumer.as_asgi()),

]
