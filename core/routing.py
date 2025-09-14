from django.urls import re_path
from .consumers import TradeChatConsumer

websocket_urlpatterns = [
    # Same path the frontend is using: /ws/chat/<trade_id>/
    re_path(r"^ws/chat/(?P<trade_id>\d+)/$", TradeChatConsumer.as_asgi()),
]