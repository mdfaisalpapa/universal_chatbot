"""Frappe integration adapters module.

Encapsulates all Frappe-specific DB operations, session handling,
and caching logic to isolate the core engine.
"""

from universal_chatbot.adapters.frappe_repository import FrappeConversationRepository

__all__ = ["FrappeConversationRepository"]
