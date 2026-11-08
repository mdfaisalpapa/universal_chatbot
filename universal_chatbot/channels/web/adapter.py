"""Web widget channel adapter.

Normalizes incoming website widget requests into the common message protocol
and translates engine responses back into the widget delivery payload.
Strict Architectural Rule: Pure Python, no Frappe imports.
"""

from typing import Any, Dict, List, Optional, Union
import uuid
from universal_chatbot.channels.base import BaseChannelAdapter
from universal_chatbot.core.exceptions import SecurityValidationError
from universal_chatbot.core.protocol import (
    EngineResponse,
    IncomingMessage,
    OutgoingResponse,
    SessionStatus,
)


class WebChannelAdapter(BaseChannelAdapter):
    """Adapter for the embeddable website chat widget."""

    channel_type = "web"

    def normalize_message(
        self, raw_payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None
    ) -> IncomingMessage:
        """Translate raw web widget HTTP JSON payload into pure Python IncomingMessage protocol."""
        if not isinstance(raw_payload, dict):
            raise SecurityValidationError("Invalid payload format. Expected JSON dictionary.")

        headers = headers or {}

        # 1. Deployment Key / ID
        deployment_id = (
            raw_payload.get("deployment_key")
            or raw_payload.get("deployment_id")
            or headers.get("x-deployment-key")
        )
        if not deployment_id:
            raise SecurityValidationError("Missing required 'deployment_key'.")

        # 2. External User ID (generated in browser localStorage)
        external_user_id = (
            raw_payload.get("external_user_id")
            or raw_payload.get("sender_id")
            or raw_payload.get("session_id")
            or headers.get("x-user-id")
        )
        if not external_user_id:
            raise SecurityValidationError("Missing required 'external_user_id'.")

        # 3. Message object extraction
        raw_msg = raw_payload.get("message")
        if isinstance(raw_msg, dict):
            msg_id = raw_msg.get("message_id") or str(uuid.uuid4())
            msg_type = raw_msg.get("type", "text")
            msg_text = str(raw_msg.get("text", "")).strip()
        else:
            msg_id = raw_payload.get("message_id") or str(uuid.uuid4())
            msg_type = raw_payload.get("type", "text")
            msg_text = str(raw_payload.get("content") or raw_payload.get("text") or "").strip()

        message_dict = {
            "message_id": msg_id,
            "type": msg_type,
            "text": msg_text,
        }

        # 4. Metadata extraction
        raw_meta = raw_payload.get("metadata") if isinstance(raw_payload.get("metadata"), dict) else {}
        meta_dict = {
            "language": raw_meta.get("language") or raw_payload.get("language") or "en",
            "timezone": raw_meta.get("timezone") or raw_payload.get("timezone") or "UTC",
            "origin": headers.get("origin") or headers.get("referer") or raw_meta.get("origin", ""),
            "user_agent": headers.get("user-agent") or raw_meta.get("user_agent", ""),
        }
        for k, v in raw_meta.items():
            if k not in meta_dict:
                meta_dict[k] = v

        return IncomingMessage(
            tenant_id=raw_payload.get("tenant_id"),
            bot_id=str(raw_payload.get("bot_id", "")),
            deployment_id=str(deployment_id),
            channel=self.channel_type,
            external_user_id=str(external_user_id),
            conversation_id=raw_payload.get("conversation_id"),
            message=message_dict,
            metadata=meta_dict,
        )

    def format_response(
        self, response: Union[OutgoingResponse, EngineResponse, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Translate the pure Python OutgoingResponse into a JSON dictionary

        formatted for the web widget to render.
        """
        if isinstance(response, OutgoingResponse):
            return {
                "status": "success",
                "conversation_id": response.conversation_id,
                "session_status": response.session_status,
                "response": {
                    "type": response.response.get("type", "text"),
                    "text": response.response.get("text", ""),
                },
                "actions": response.actions,
                "messages": [
                    {
                        "type": response.response.get("type", "text"),
                        "text": response.response.get("text", ""),
                        "options": [
                            act for act in response.actions if act.get("type") in ("option", "quick_reply")
                        ],
                    }
                ],
            }

        elif isinstance(response, EngineResponse):
            msgs: List[Dict[str, Any]] = [m.to_dict() for m in response.messages]
            last_text = msgs[-1]["content"] if msgs else ""
            last_type = msgs[-1]["message_type"] if msgs else "text"
            return {
                "status": "error" if response.error else "success",
                "conversation_id": response.conversation_id,
                "session_status": (
                    SessionStatus.COMPLETED.value
                    if response.is_completed
                    else SessionStatus.ACTIVE.value
                ),
                "response": {"type": last_type, "text": last_text},
                "actions": [],
                "messages": msgs,
                "current_node_id": response.current_node_id,
                "error": response.error,
            }

        elif isinstance(response, dict):
            # Already a dictionary (e.g. from FlowExecutionResult.to_dict())
            conv_id = response.get("conversation_id", "")
            status_val = response.get("status", "running")
            session_status = (
                SessionStatus.PAUSED.value
                if status_val == "paused"
                else (
                    SessionStatus.COMPLETED.value
                    if status_val == "completed"
                    else SessionStatus.ACTIVE.value
                )
            )
            raw_msgs = response.get("messages", [])
            last_text = raw_msgs[-1].get("text", "") if raw_msgs else ""
            last_type = raw_msgs[-1].get("type", "text") if raw_msgs else "text"

            actions = []
            for m in raw_msgs:
                if m.get("options"):
                    for opt in m["options"]:
                        actions.append({
                            "type": "quick_reply",
                            "label": opt.get("label"),
                            "value": opt.get("value"),
                        })

            return {
                "status": "error" if response.get("error") else "success",
                "conversation_id": conv_id,
                "session_status": session_status,
                "response": {"type": last_type, "text": last_text},
                "actions": actions,
                "messages": raw_msgs,
                "current_node_id": response.get("current_node_id"),
                "error": response.get("error"),
            }

        raise ValueError(f"Unsupported response type for formatting: {type(response)}")
