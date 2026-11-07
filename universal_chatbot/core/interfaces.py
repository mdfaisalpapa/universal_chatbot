"""Domain interfaces and contracts for Universal Chatbot.

Enforces strict separation between core engine logic and storage/frameworks.
Frappe implementations must satisfy these contracts via adapters.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from universal_chatbot.core.protocol import (
    EngineResponse,
    NormalizedIncomingMessage,
    OutgoingMessage,
)


class BaseChannelAdapter(ABC):
    """Channel adapter interface for transforming channel-specific payloads

    to and from the normalized engine protocol.
    """

    channel_type: str

    @abstractmethod
    def normalize_request(self, raw_payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> NormalizedIncomingMessage:
        """Parse raw channel payload into NormalizedIncomingMessage."""
        pass

    @abstractmethod
    def format_response(self, engine_response: EngineResponse) -> Dict[str, Any]:
        """Convert engine response to channel-specific payload."""
        pass


class BaseConnector(ABC):
    """External system connector interface."""

    connector_type: str

    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """Verify connectivity and credentials."""
        pass

    @abstractmethod
    def get_available_actions(self) -> List[Dict[str, Any]]:
        """List discoverable operations/actions this connector supports."""
        pass

    @abstractmethod
    def validate_parameters(self, action_name: str, parameters: Dict[str, Any]) -> bool:
        """Validate action parameters before execution."""
        pass

    @abstractmethod
    def execute(self, action_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action and return standard result payload."""
        pass


class RepositoryAdapterInterface(ABC):
    """Abstract persistence adapter contract for conversation, bot, and execution storage."""

    @abstractmethod
    def get_bot(self, bot_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_deployment(self, deployment_key: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_or_create_conversation(
        self,
        bot_id: str,
        deployment_id: str,
        channel_type: str,
        sender_id: str,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def load_conversation_state(self, conversation_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def save_conversation_state(self, conversation_id: str, state_data: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def append_messages(self, conversation_id: str, messages: List[Dict[str, Any]]) -> None:
        pass

    @abstractmethod
    def record_event(self, conversation_id: str, event_type: str, payload: Dict[str, Any]) -> None:
        pass
