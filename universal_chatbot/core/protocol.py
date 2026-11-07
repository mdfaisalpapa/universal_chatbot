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


class SessionStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"
    COMPLETED = "completed"
    EXPIRED = "expired"


class EventType(str, Enum):
    CONVERSATION_STARTED = "conversation_started"
    CONVERSATION_ENDED = "conversation_ended"
    FLOW_STARTED = "flow_started"
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"
    FLOW_TRANSITION = "flow_transition"
    NODE_ENTERED = "node_entered"
    NODE_EXITED = "node_exited"
    NODE_EXECUTION = "node_execution"
    VARIABLE_SET = "variable_set"
    ACTION_CALLED = "action_called"
    ACTION_COMPLETED = "action_completed"
    ACTION_FAILED = "action_failed"
    ERROR = "error"


@dataclass
class OptionItem:
    label: str
    value: str
    description: Optional[str] = None
    icon: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class IncomingMessage:
    """Core protocol representation of an incoming message from any channel.

    Channel adapters normalize channel-specific payloads into this structure.
    Strictly excludes channel-specific payloads.
    """

    bot_id: str
    deployment_id: str
    channel: str
    external_user_id: str
    message: Dict[str, Any]
    metadata: Dict[str, Any]
    tenant_id: Optional[str] = None
    conversation_id: Optional[str] = None

    def __post_init__(self):
        self.validate()

    def validate(self) -> None:
        if not self.bot_id or not isinstance(self.bot_id, str):
            raise ValueError("bot_id must be a non-empty string")
        if not self.deployment_id or not isinstance(self.deployment_id, str):
            raise ValueError("deployment_id must be a non-empty string")
        if not self.channel or not isinstance(self.channel, str):
            raise ValueError("channel must be a non-empty string")
        if not self.external_user_id or not isinstance(self.external_user_id, str):
            raise ValueError("external_user_id must be a non-empty string")

        if not isinstance(self.message, dict):
            raise ValueError("message must be a dictionary")
        for req_field in ("message_id", "type", "text"):
            if req_field not in self.message:
                raise ValueError(f"message dictionary missing required key: '{req_field}'")

        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a dictionary")
        for req_field in ("language", "timezone"):
            if req_field not in self.metadata:
                raise ValueError(f"metadata dictionary missing required key: '{req_field}'")

    @classmethod
    def create(
        cls,
        bot_id: str,
        deployment_id: str,
        channel: str,
        external_user_id: str,
        text: str,
        message_id: Optional[str] = None,
        message_type: str = "text",
        language: str = "en",
        tz: str = "UTC",
        conversation_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> "IncomingMessage":
        meta = {"language": language, "timezone": tz}
        if extra_metadata:
            meta.update(extra_metadata)
        return cls(
            bot_id=bot_id,
            deployment_id=deployment_id,
            channel=channel,
            external_user_id=external_user_id,
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            message={
                "message_id": message_id or str(uuid.uuid4()),
                "type": message_type,
                "text": text,
            },
            metadata=meta,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "bot_id": self.bot_id,
            "deployment_id": self.deployment_id,
            "channel": self.channel,
            "external_user_id": self.external_user_id,
            "conversation_id": self.conversation_id,
            "message": dict(self.message),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IncomingMessage":
        return cls(
            tenant_id=data.get("tenant_id"),
            bot_id=data["bot_id"],
            deployment_id=data["deployment_id"],
            channel=data["channel"],
            external_user_id=data["external_user_id"],
            conversation_id=data.get("conversation_id"),
            message=data["message"],
            metadata=data["metadata"],
        )


@dataclass
class OutgoingResponse:
    """Core protocol representation of an outgoing response generated by the conversation engine.

    Channel adapters translate this standard response back into channel-specific payloads.
    """

    conversation_id: str
    response: Dict[str, Any]
    actions: List[Dict[str, Any]] = field(default_factory=list)
    session_status: str = SessionStatus.ACTIVE.value

    def __post_init__(self):
        self.validate()

    def validate(self) -> None:
        if not self.conversation_id or not isinstance(self.conversation_id, str):
            raise ValueError("conversation_id must be a non-empty string")

        if not isinstance(self.response, dict):
            raise ValueError("response must be a dictionary")
        for req_field in ("type", "text"):
            if req_field not in self.response:
                raise ValueError(f"response dictionary missing required key: '{req_field}'")

        if not isinstance(self.actions, list):
            raise ValueError("actions must be a list")

        if not self.session_status or not isinstance(self.session_status, str):
            raise ValueError("session_status must be a non-empty string")

    @classmethod
    def create(
        cls,
        conversation_id: str,
        text: str,
        response_type: str = "text",
        actions: Optional[List[Dict[str, Any]]] = None,
        session_status: str = SessionStatus.ACTIVE.value,
        extra_response_data: Optional[Dict[str, Any]] = None,
    ) -> "OutgoingResponse":
        resp = {"type": response_type, "text": text}
        if extra_response_data:
            resp.update(extra_response_data)
        return cls(
            conversation_id=conversation_id,
            response=resp,
            actions=actions or [],
            session_status=session_status,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "response": dict(self.response),
            "actions": list(self.actions),
            "session_status": self.session_status,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OutgoingResponse":
        return cls(
            conversation_id=data["conversation_id"],
            response=data["response"],
            actions=data.get("actions", []),
            session_status=data.get("session_status", SessionStatus.ACTIVE.value),
        )


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
