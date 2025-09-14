import os

# 1) Point to your settings BEFORE anything Django-related
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "brokerage_backend.settings")

# 2) Initialize Django so apps are loaded
import django
django.setup()

# 3) Now it's safe to import the rest
from django.conf import settings
from django.core.asgi import get_asgi_application
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

import core.routing  # defines websocket_urlpatterns

# Standard Django ASGI app (HTTP)
django_asgi_app = get_asgi_application()

# Protocol router for HTTP + WebSocket
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(core.routing.websocket_urlpatterns)
    ),
})

# Serve static files under Daphne in DEBUG so /admin renders correctly
if getattr(settings, "DEBUG", False):
    application = ASGIStaticFilesHandler(application)
