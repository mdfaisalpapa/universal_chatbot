"""Domain interfaces and contracts for Universal Chatbot.

Enforces strict separation between core engine logic and storage/frameworks.
Frappe implementations must satisfy these contracts via adapters.
Strict Architectural Rule: Do not import `frappe` here.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from universal_chatbot.core.protocol import (
    EngineResponse,
    IncomingMessage,
    NormalizedIncomingMessage,
    OutgoingMessage,
    OutgoingResponse,
)


class BaseChannelAdapter(ABC):
    """Channel adapter interface for transforming channel-specific payloads

    to and from the normalized engine protocol.
    """

    channel_type: str

    @abstractmethod
    def normalize_request(
        self, raw_payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None
    ) -> NormalizedIncomingMessage:
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


class ConversationRepositoryInterface(ABC):
    """Abstract persistence adapter contract for managing contacts,

    identities, conversations, state, messages, and audit events.
    """

    @abstractmethod
    def get_or_create_contact(
        self, display_name: str, contact_status: str = "Active", email: Optional[str] = None, phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create or fetch a contact by ID."""
        pass

    @abstractmethod
    def get_or_create_channel_identity(
        self,
        contact_id: str,
        channel: str,
        external_user_id: str,
        verification_status: str = "Anonymous",
    ) -> Dict[str, Any]:
        """Explicitly map an external channel user ID to an existing contact.

        Identity resolution across channels is strictly explicit.
        """
        pass

    @abstractmethod
    def get_contact_by_channel_identity(
        self, channel: str, external_user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Lookup contact linked to this channel identity."""
        pass

    @abstractmethod
    def create_conversation(
        self,
        bot: str,
        deployment: str,
        contact: str,
        channel: str,
        status: str = "Active",
    ) -> Dict[str, Any]:
        """Create a new conversation session."""
        pass

    @abstractmethod
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve conversation record by ID."""
        pass

    @abstractmethod
    def update_conversation_status(self, conversation_id: str, status: str) -> None:
        """Update conversation status (Active, Paused, Closed, Expired)."""
        pass

    @abstractmethod
    def touch_conversation(self, conversation_id: str) -> None:
        """Update last_activity timestamp for a conversation."""
        pass

    @abstractmethod
    def save_state(
        self,
        conversation_id: str,
        current_node: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        active_flow_version: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Save/upsert flow state for pause and resume."""
        pass

    @abstractmethod
    def get_state(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve current flow state (variables, context, current_node)."""
        pass

    @abstractmethod
    def log_message(
        self,
        conversation_id: str,
        direction: str,
        message_type: str,
        content: str,
        external_message_id: Optional[str] = None,
        status: str = "Sent",
    ) -> Dict[str, Any]:
        """Persist inbound or outbound message."""
        pass

    @abstractmethod
    def get_messages(self, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch chronological message history."""
        pass

    @abstractmethod
    def record_event(
        self,
        conversation_id: str,
        event_type: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Append an audit trail event for analytics or debugging."""
        pass

    @abstractmethod
    def get_events(self, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve conversation audit events."""
        pass
