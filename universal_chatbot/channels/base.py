"""Base channel adapter contract.

Pure Python, decoupled from Frappe.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union
from universal_chatbot.core.protocol import (
    EngineResponse,
    IncomingMessage,
    NormalizedIncomingMessage,
    OutgoingResponse,
)


class BaseChannelAdapter(ABC):
    """Abstract adapter to decouple external communication protocols

    from the internal engine.
    """

    channel_type: str = "base"

    @abstractmethod
    def normalize_message(
        self, raw_payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None
    ) -> IncomingMessage:
        """Parse raw incoming HTTP payload into the standardized IncomingMessage protocol."""
        pass

    @abstractmethod
    def format_response(
        self, response: Union[OutgoingResponse, EngineResponse, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Convert standard response into the channel-specific delivery format."""
        pass

    def normalize_request(
        self, raw_payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None
    ) -> NormalizedIncomingMessage:
        """Compatibility wrapper for NormalizedIncomingMessage."""
        msg = self.normalize_message(raw_payload, headers)
        return NormalizedIncomingMessage(
            sender_id=msg.external_user_id,
            channel_type=self.channel_type,
            content=msg.message.get("text", ""),
            bot_id=msg.bot_id,
            deployment_key=msg.deployment_id,
            conversation_id=msg.conversation_id,
            tenant_id=msg.tenant_id,
            metadata=msg.metadata,
        )
