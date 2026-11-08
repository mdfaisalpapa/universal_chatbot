"""External system connectors module.

Strict Architectural Rule:
Do not import `frappe` here.
"""
from universal_chatbot.connectors.base import BaseConnector
from universal_chatbot.connectors.rest.generic import GenericRestConnector
from universal_chatbot.connectors.rest.frappe_connector import FrappeRestConnector

__all__ = ["BaseConnector", "GenericRestConnector", "FrappeRestConnector"]
