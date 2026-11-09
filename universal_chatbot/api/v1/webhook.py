"""Webhook endpoint router for external channels and widgets."""

from typing import Any, Dict, Optional
import frappe
from universal_chatbot.api.v1.chat import init_chat, send_message
from universal_chatbot.channels.gateway import get_channel_gateway
from universal_chatbot.channels.telegram.adapter import telegram_webhook
from universal_chatbot.channels.whatsapp.adapter import whatsapp_webhook


@frappe.whitelist(allow_guest=True)
def channel_webhook(
    channel: str, deployment_key: Optional[str] = None
) -> Any:
    """Unified webhook gateway router supporting any registered channel (web, telegram, whatsapp)."""
    channel_key = (channel or "").lower().strip()
    if channel_key in ("whatsapp", "wa"):
        return whatsapp_webhook(deployment_key=deployment_key)
    elif channel_key in ("telegram", "tg"):
        return telegram_webhook(deployment_key=deployment_key)

    gateway = get_channel_gateway()
    headers = dict(getattr(frappe.local, "request", None) and frappe.local.request.headers or {})
    raw_payload = frappe.request.get_json(force=True, silent=True) or dict(frappe.form_dict)

    result = gateway.process_and_execute(
        channel_type=channel_key,
        raw_payload=raw_payload,
        headers=headers,
        deployment_key=deployment_key,
    )
    return {"status": "ok", "conversation_id": result.get("conversation_id")}


__all__ = [
    "init_chat",
    "send_message",
    "telegram_webhook",
    "whatsapp_webhook",
    "channel_webhook",
]
