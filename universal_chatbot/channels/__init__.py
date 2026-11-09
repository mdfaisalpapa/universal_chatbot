"""Channels module for normalizing external platform messaging.

Strict Architectural Rule:
Do not import `frappe` here.
"""

from universal_chatbot.channels.base import BaseChannelAdapter
from universal_chatbot.channels.gateway import ChannelGateway, get_channel_gateway
from universal_chatbot.channels.web.adapter import WebChannelAdapter
from universal_chatbot.channels.telegram.adapter import TelegramChannelAdapter
from universal_chatbot.channels.whatsapp.adapter import WhatsAppChannelAdapter

__all__ = [
    "BaseChannelAdapter",
    "ChannelGateway",
    "get_channel_gateway",
    "WebChannelAdapter",
    "TelegramChannelAdapter",
    "WhatsAppChannelAdapter",
]
