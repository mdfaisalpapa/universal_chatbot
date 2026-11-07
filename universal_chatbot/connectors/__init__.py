"""External system connectors module.

Strict Architectural Rule:
Do not import `frappe` here.
"""
from universal_chatbot.connectors.base import BaseConnector

__all__ = ["BaseConnector"]
