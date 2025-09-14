# core/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from .models import P2PTrade, ChatMessage
from asgiref.sync import sync_to_async

class TradeChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.trade_id = int(self.scope["url_route"]["kwargs"]["trade_id"])
        self.group = f"trade_{self.trade_id}"

        # Cache a "vendor label" for staff messages
        try:
            trade = await sync_to_async(P2PTrade.objects.select_related("vendor").get)(pk=self.trade_id)
            self.vendor_label = trade.vendor.name or "Vendor"
        except Exception:
            self.vendor_label = "Vendor"

        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        try:
            payload = json.loads(text_data or "{}")
        except Exception:
            return

        msg = (payload.get("message") or "").strip()
        if not msg:
            return

        user = self.scope.get("user", AnonymousUser())

        # ⬇️ Staff speak "as the vendor"; normal users speak as their username.
        if getattr(user, "is_staff", False):
            sender = self.vendor_label
        else:
            sender = getattr(user, "username", "User")

        # (Optional) persist messages
        try:
            await sync_to_async(ChatMessage.objects.create)(
                trade_id=self.trade_id, sender=user, message=msg
            )
        except Exception:
            pass

        await self.channel_layer.group_send(
            self.group,
            {"type": "chat.message", "sender": sender, "message": msg}
        )

    async def status_update(self, event):
        # Optional extra event for live status changes
        await self.send(text_data=json.dumps({
            "type": "status",
            "status": event.get("status"),
            "message": event.get("message", "")
        }))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "sender": event["sender"],
            "message": event["message"],
        }))

    # -------- DB helpers ----------
    @database_sync_to_async
    def _user_allowed(self, user_id, trade_id):
        if not user_id:
            return False
        try:
            t = P2PTrade.objects.select_related("user").get(pk=trade_id)
        except P2PTrade.DoesNotExist:
            return False

        if t.user_id == user_id:
            return True

        User = get_user_model()
        try:
            u = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return False
        return bool(u.is_staff)

    @database_sync_to_async
    def _save_message(self, user_id, trade_id, message):
        try:
            t = P2PTrade.objects.get(pk=trade_id)
        except P2PTrade.DoesNotExist:
            return
        User = get_user_model()
        try:
            u = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return
        ChatMessage.objects.create(trade=t, sender=u, message=message)
