"""Base channel adapter contract.

Pure Python, decoupled from Frappe.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from universal_chatbot.core.protocol import (
    EngineResponse,
    NormalizedIncomingMessage,
)


class BaseChannelAdapter(ABC):
    """Abstract adapter to decouple external communication protocols

    from the internal engine.
    """

    channel_type: str = "base"

    @abstractmethod
    def normalize_request(
        self, raw_payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None
    ) -> NormalizedIncomingMessage:
        """Parse raw incoming HTTP payload/events into a standardized NormalizedIncomingMessage."""
        pass

    @abstractmethod
    def format_response(self, engine_response: EngineResponse) -> Dict[str, Any]:
        """Convert standard EngineResponse to the channel-specific delivery format."""
        pass
