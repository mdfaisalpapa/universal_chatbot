"""Domain exceptions for Universal Chatbot.

Decoupled from any framework or database specifics.
"""

from typing import Any, Dict, Optional


class UniversalChatbotError(Exception):
    """Base exception for all Universal Chatbot domain errors."""

    def __init__(self, message: str, code: str = "GENERIC_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "code": self.code,
            "details": self.details,
        }


class BotNotFoundError(UniversalChatbotError):
    def __init__(self, bot_id: str):
        super().__init__(f"Chatbot not found: {bot_id}", code="BOT_NOT_FOUND", details={"bot_id": bot_id})


class DeploymentNotFoundError(UniversalChatbotError):
    def __init__(self, deployment_key: str):
        super().__init__(
            f"Deployment not found or inactive: {deployment_key}",
            code="DEPLOYMENT_NOT_FOUND",
            details={"deployment_key": deployment_key},
        )


class ConversationNotFoundError(UniversalChatbotError):
    def __init__(self, conversation_id: str):
        super().__init__(
            f"Conversation not found: {conversation_id}",
            code="CONVERSATION_NOT_FOUND",
            details={"conversation_id": conversation_id},
        )


class FlowExecutionError(UniversalChatbotError):
    def __init__(self, message: str, node_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        payload = details or {}
        if node_id:
            payload["node_id"] = node_id
        super().__init__(message, code="FLOW_EXECUTION_ERROR", details=payload)


class ConnectorError(UniversalChatbotError):
    def __init__(self, message: str, connector_name: Optional[str] = None, status_code: Optional[int] = None):
        super().__init__(
            message,
            code="CONNECTOR_ERROR",
            details={"connector": connector_name, "status_code": status_code},
        )


class ChannelError(UniversalChatbotError):
    def __init__(self, message: str, channel_type: Optional[str] = None):
        super().__init__(
            message,
            code="CHANNEL_ERROR",
            details={"channel_type": channel_type},
        )


class SecurityValidationError(UniversalChatbotError):
    def __init__(self, message: str, reason: str = "FORBIDDEN"):
        super().__init__(
            message,
            code="SECURITY_ERROR",
            details={"reason": reason},
        )
