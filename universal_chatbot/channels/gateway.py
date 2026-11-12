"""Channel Gateway and Registry.

Decoupled pure Python routing and adapter registration for omnichannel messaging.
Routes incoming webhooks from external channels (Web, Telegram, WhatsApp)
to their respective channel adapters and coordinates bidirectional communication
with the Conversation Engine.
"""

from typing import Any, Dict, Optional, Type, Union
from universal_chatbot.channels.base import BaseChannelAdapter
from universal_chatbot.channels.web.adapter import WebChannelAdapter
from universal_chatbot.core.exceptions import SecurityValidationError
from universal_chatbot.core.protocol import IncomingMessage, OutgoingResponse


class ChannelGateway:
    """Central gateway registry for all messaging channels."""

    def __init__(self):
        self._adapters: Dict[str, BaseChannelAdapter] = {}
        self._register_default_adapters()

    def _register_default_adapters(self) -> None:
        """Register default built-in channel adapters."""
        self.register_adapter("web", WebChannelAdapter())
        try:
            from universal_chatbot.channels.telegram.adapter import TelegramChannelAdapter
            self.register_adapter("telegram", TelegramChannelAdapter())
        except ImportError:
            pass
        try:
            from universal_chatbot.channels.whatsapp.adapter import WhatsAppChannelAdapter
            self.register_adapter("whatsapp", WhatsAppChannelAdapter())
        except ImportError:
            pass

    def register_adapter(
        self, channel_type: str, adapter: Union[BaseChannelAdapter, Type[BaseChannelAdapter]]
    ) -> None:
        """Register a channel adapter instance or class."""
        key = (channel_type or "").strip().lower()
        if isinstance(adapter, type) and issubclass(adapter, BaseChannelAdapter):
            self._adapters[key] = adapter()
        elif isinstance(adapter, BaseChannelAdapter):
            self._adapters[key] = adapter
        else:
            raise TypeError(
                f"Adapter must be an instance or subclass of BaseChannelAdapter, got {type(adapter)}"
            )

    def get_adapter(self, channel_type: str) -> BaseChannelAdapter:
        """Retrieve the adapter for a given channel name."""
        key = (channel_type or "").strip().lower()
        if key not in self._adapters:
            # Try lazy import
            if key in ("telegram", "tg"):
                from universal_chatbot.channels.telegram.adapter import TelegramChannelAdapter
                self._adapters[key] = TelegramChannelAdapter()
            elif key in ("whatsapp", "wa"):
                from universal_chatbot.channels.whatsapp.adapter import WhatsAppChannelAdapter
                self._adapters[key] = WhatsAppChannelAdapter()
            elif key == "web":
                self._adapters[key] = WebChannelAdapter()
            else:
                raise ValueError(f"No channel adapter registered for channel: '{channel_type}'")
        return self._adapters[key]

    def has_adapter(self, channel_type: str) -> bool:
        """Check if an adapter is registered for the channel type."""
        key = (channel_type or "").strip().lower()
        return key in self._adapters

    def normalize_incoming(
        self, channel_type: str, raw_payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None
    ) -> IncomingMessage:
        """Route raw HTTP payload to the appropriate channel adapter for normalization."""
        adapter = self.get_adapter(channel_type)
        return adapter.normalize_message(raw_payload, headers)

    def format_outgoing(
        self, channel_type: str, response: Union[OutgoingResponse, Dict[str, Any]], **kwargs
    ) -> Dict[str, Any]:
        """Route standard response to the appropriate channel adapter for channel formatting."""
        adapter = self.get_adapter(channel_type)
        return adapter.format_response(response, **kwargs)

    def process_and_execute(
        self,
        channel_type: str,
        raw_payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        deployment_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Dispatch an incoming payload from any channel into the Frappe conversation engine."""
        import frappe
        from universal_chatbot.adapters.frappe_repository import FrappeConversationRepository
        from universal_chatbot.flow.engine import FlowExecutor
        from universal_chatbot.api.v1.chat import get_active_deployment, resolve_flow_for_bot
        from universal_chatbot.universal_chatbot.doctype.bot_channel.bot_channel import BotChannel

        adapter = self.get_adapter(channel_type)
        headers = headers or {}

        # 1. Resolve Deployment
        dep_key = (
            deployment_key
            or raw_payload.get("deployment_key")
            or raw_payload.get("deployment_id")
            or headers.get("x-deployment-key")
        )

        deployment = None
        if dep_key:
            try:
                deployment = get_active_deployment(dep_key)
            except Exception:
                deployment = None

        if not deployment and channel_type in ("whatsapp", "wa"):
            phone_id = raw_payload.get("phone_number_id")
            if not phone_id and isinstance(raw_payload.get("entry"), list) and raw_payload["entry"]:
                changes = raw_payload["entry"][0].get("changes", [])
                if changes and isinstance(changes, list):
                    phone_id = changes[0].get("value", {}).get("metadata", {}).get("phone_number_id")
            if phone_id:
                ch_name = frappe.db.get_value("Bot Channel", {"whatsapp_phone_number_id": str(phone_id), "is_enabled": 1}, "name")
                if ch_name:
                    d_name = frappe.db.get_value("Bot Deployment", {"channel": ch_name, "status": "Active"}, "name") or frappe.db.get_value("Bot Channel", ch_name, "deployment")
                    if d_name:
                        deployment = frappe.get_doc("Bot Deployment", d_name)

        if not deployment:
            # Fallback: find deployment linked to this channel type
            channel_name = frappe.db.get_value(
                "Bot Channel",
                {"channel_type": channel_type.capitalize(), "is_enabled": 1},
                "name",
            ) or frappe.db.get_value(
                "Bot Channel",
                {"channel_type": channel_type, "is_enabled": 1},
                "name",
            )
            if channel_name:
                dep_name = frappe.db.get_value("Bot Deployment", {"channel": channel_name, "status": "Active"}, "name")
                if not dep_name:
                    dep_name = frappe.db.get_value("Bot Channel", channel_name, "deployment")
                if dep_name:
                    deployment = frappe.get_doc("Bot Deployment", dep_name)

        if not deployment:
            raise SecurityValidationError(
                f"Could not resolve an active Bot Deployment for channel '{channel_type}'."
            )

        # Inject deployment_key and bot_id into raw_payload if missing
        if "deployment_key" not in raw_payload and "deployment_id" not in raw_payload:
            raw_payload["deployment_key"] = deployment.deployment_key
        if "bot_id" not in raw_payload:
            raw_payload["bot_id"] = deployment.chatbot

        # 2. Normalize Incoming Payload
        incoming_msg = adapter.normalize_message(raw_payload, headers)

        repo = FrappeConversationRepository()
        executor = FlowExecutor()

        # 3. Resolve Contact & Channel Identity
        external_id = incoming_msg.external_user_id
        contact = repo.get_contact_by_channel_identity(channel_type, external_id)
        if not contact:
            disp_name = (
                incoming_msg.metadata.get("first_name")
                or incoming_msg.metadata.get("profile_name")
                or f"{channel_type.capitalize()} User {external_id[-4:]}"
            )
            contact = repo.get_or_create_contact(
                display_name=disp_name,
                contact_status="Active",
            )
            repo.get_or_create_channel_identity(
                contact_id=contact["name"],
                channel=channel_type,
                external_user_id=external_id,
                verification_status="Verified" if channel_type in ("telegram", "whatsapp") else "Anonymous",
            )

        # 4. Resolve Conversation
        conv_list = frappe.get_all(
            "Chat Conversation",
            filters={
                "contact": contact["name"],
                "deployment": deployment.name,
                "status": ["in", ["Active", "Paused"]],
            },
            order_by="modified desc",
            limit=1,
        )

        if conv_list:
            conv_id = conv_list[0].name
        else:
            new_conv = repo.create_conversation(
                bot=deployment.chatbot,
                deployment=deployment.name,
                contact=contact["name"],
                channel=channel_type,
                status="Active",
            )
            conv_id = new_conv["name"]
            repo.record_event(
                conversation_id=conv_id,
                event_type="conversation_started",
                details={"channel": channel_type, "external_user_id": external_id},
            )

        # 5. Log Inbound Message
        inbound_text = incoming_msg.message.get("text", "")
        repo.log_message(
            conversation_id=conv_id,
            direction="Inbound",
            message_type="Text",
            content=inbound_text,
            external_message_id=incoming_msg.message.get("message_id"),
        )
        repo.record_event(
            conversation_id=conv_id,
            event_type="message_received",
            details={"text": inbound_text, "channel": channel_type},
        )

        # 6. Execute Flow
        state = repo.get_state(conv_id) or {}
        if "context" not in state:
            state["context"] = {}
        state["context"].setdefault("channel", channel_type)
        state["context"].setdefault("channel_user_id", external_id)

        flow_id = resolve_flow_for_bot(deployment.chatbot, deployment)
        flow_def = repo.get_flow_definition(flow_id)

        flow_result = executor.execute(
            flow=flow_def,
            conversation_id=conv_id,
            state=state,
            incoming_message=incoming_msg,
            action_executor=repo.execute_action,
        )

        # 7. Log Outbound Messages
        for out_msg in flow_result.messages:
            txt = out_msg.get("text", "")
            mtype = out_msg.get("type", "text").capitalize()
            repo.log_message(
                conversation_id=conv_id,
                direction="Outbound",
                message_type=mtype,
                content=txt,
            )
            repo.record_event(
                conversation_id=conv_id,
                event_type="message_sent",
                details={"text": txt, "type": out_msg.get("type")},
            )

        # 8. Save State
        repo.save_state(
            conversation_id=conv_id,
            current_node=flow_result.current_node_id,
            variables=flow_result.variables,
            context=flow_result.context,
        )
        repo.save_flow_execution(
            conversation_id=conv_id,
            flow_id=flow_id,
            current_node=flow_result.current_node_id,
            status=flow_result.status.value,
            execution_context={"variables": flow_result.variables},
        )

        if flow_result.status.value == "completed":
            repo.update_conversation_status(conv_id, "Closed")
            repo.record_event(conv_id, "conversation_ended", {"reason": "flow_completed"})

        # 9. Format Outgoing Delivery Payload
        recipient_id = (
            incoming_msg.metadata.get("chat_id")
            or incoming_msg.external_user_id
        )
        formatted_response = adapter.format_response(
            flow_result.to_dict(),
            recipient=recipient_id,
        )

        return {
            "conversation_id": conv_id,
            "status": flow_result.status.value,
            "flow_result": flow_result.to_dict(),
            "formatted_response": formatted_response,
            "recipient_id": recipient_id,
            "deployment": deployment,
            "incoming_message": incoming_msg,
        }


# Global singleton instance
_gateway_instance: Optional[ChannelGateway] = None


def get_channel_gateway() -> ChannelGateway:
    """Return the global ChannelGateway singleton."""
    global _gateway_instance
    if _gateway_instance is None:
        _gateway_instance = ChannelGateway()
    return _gateway_instance
