"""Common Message Protocol and Domain Entities.

Decoupled pure Python representations of messages, payloads, sessions, and events.
Zero external framework dependencies.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class MessageRole(str, Enum):
    USER = "user"
    BOT = "bot"
    SYSTEM = "system"


class MessageType(str, Enum):
    TEXT = "text"
    OPTIONS = "options"
    QUICK_REPLIES = "quick_replies"
    CARD = "card"
    FORM = "form"
    TYPING = "typing"
    ERROR = "error"


class EventType(str, Enum):
    CONVERSATION_STARTED = "conversation_started"
    CONVERSATION_ENDED = "conversation_ended"
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"
    FLOW_TRANSITION = "flow_transition"
    NODE_ENTERED = "node_entered"
    NODE_EXITED = "node_exited"
    VARIABLE_SET = "variable_set"
    ACTION_CALLED = "action_called"
    ACTION_COMPLETED = "action_completed"
    ACTION_FAILED = "action_failed"


@dataclass
class OptionItem:
    label: str
    value: str
    description: Optional[str] = None
    icon: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NormalizedIncomingMessage:
    """Incoming message normalized by a channel adapter before engine processing."""

    sender_id: str
    channel_type: str
    content: str
    bot_id: str
    deployment_key: str
    conversation_id: Optional[str] = None
    tenant_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    payload: Optional[Dict[str, Any]] = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class OutgoingMessage:
    """Standard engine response message before translation by a channel adapter."""

    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    role: MessageRole = MessageRole.BOT
    message_type: MessageType = MessageType.TEXT
    content: str = ""
    options: List[OptionItem] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "role": self.role.value if isinstance(self.role, MessageRole) else self.role,
            "message_type": self.message_type.value if isinstance(self.message_type, MessageType) else self.message_type,
            "content": self.content,
            "options": [opt.to_dict() if isinstance(opt, OptionItem) else opt for opt in self.options],
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


@dataclass
class EngineResponse:
    """Complete response returned by the flow/conversation engine."""

    conversation_id: str
    messages: List[OutgoingMessage] = field(default_factory=list)
    state_updates: Dict[str, Any] = field(default_factory=dict)
    current_node_id: Optional[str] = None
    is_completed: bool = False
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "messages": [msg.to_dict() for msg in self.messages],
            "state_updates": self.state_updates,
            "current_node_id": self.current_node_id,
            "is_completed": self.is_completed,
            "error": self.error,
        }
