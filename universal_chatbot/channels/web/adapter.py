"""Web widget channel adapter.

Normalizes incoming website widget requests and formats responses.
Strict Architectural Rule: No Frappe imports.
"""

from typing import Any, Dict, Optional
from universal_chatbot.channels.base import BaseChannelAdapter
from universal_chatbot.core.exceptions import SecurityValidationError
from universal_chatbot.core.protocol import (
    EngineResponse,
    NormalizedIncomingMessage,
)


class WebChannelAdapter(BaseChannelAdapter):
    """Adapter for the embeddable website chat widget."""

    channel_type = "web"

    def normalize_request(
        self, raw_payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None
    ) -> NormalizedIncomingMessage:
        if not isinstance(raw_payload, dict):
            raise SecurityValidationError("Invalid payload format. Expected JSON object.")

        deployment_key = raw_payload.get("deployment_key") or (headers.get("x-deployment-key") if headers else None)
        if not deployment_key:
            raise SecurityValidationError("Missing required 'deployment_key'.")

        sender_id = raw_payload.get("sender_id") or raw_payload.get("session_id")
        if not sender_id:
            raise SecurityValidationError("Missing required 'sender_id'.")

        content = raw_payload.get("content") or raw_payload.get("message") or ""
        bot_id = raw_payload.get("bot_id", "")
        conversation_id = raw_payload.get("conversation_id")
        tenant_id = raw_payload.get("tenant_id")
        payload = raw_payload.get("payload") or {}

        metadata = {
            "origin": (headers or {}).get("origin", ""),
            "user_agent": (headers or {}).get("user-agent", ""),
            "client_timestamp": raw_payload.get("timestamp"),
            **(raw_payload.get("metadata") or {}),
        }

        return NormalizedIncomingMessage(
            sender_id=str(sender_id),
            channel_type=self.channel_type,
            content=str(content),
            bot_id=str(bot_id),
            deployment_key=str(deployment_key),
            conversation_id=str(conversation_id) if conversation_id else None,
            tenant_id=str(tenant_id) if tenant_id else None,
            metadata=metadata,
            payload=payload,
        )

    def format_response(self, engine_response: EngineResponse) -> Dict[str, Any]:
        """Convert EngineResponse into website widget JSON format."""
        return {
            "status": "success" if not engine_response.error else "error",
            "conversation_id": engine_response.conversation_id,
            "messages": [msg.to_dict() for msg in engine_response.messages],
            "current_node_id": engine_response.current_node_id,
            "is_completed": engine_response.is_completed,
            "error": engine_response.error,
        }
