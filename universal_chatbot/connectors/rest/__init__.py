"""REST Connectors package."""

from universal_chatbot.connectors.rest.generic import GenericRestConnector
from universal_chatbot.connectors.rest.frappe_connector import FrappeRestConnector

__all__ = ["GenericRestConnector", "FrappeRestConnector"]
