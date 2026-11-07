"""Channels module for normalizing external platform messaging.

Strict Architectural Rule:
Do not import `frappe` here.
"""
from universal_chatbot.channels.base import BaseChannelAdapter

__all__ = ["BaseChannelAdapter"]
