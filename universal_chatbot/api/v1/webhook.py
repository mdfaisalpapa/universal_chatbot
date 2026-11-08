"""Webhook endpoint router for external channels and widgets."""

from universal_chatbot.api.v1.chat import init_chat, send_message

__all__ = ["init_chat", "send_message"]
