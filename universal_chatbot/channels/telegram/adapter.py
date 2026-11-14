"""Telegram Channel Adapter.

Handles normalization of Telegram webhook updates into the common message protocol,
and formatting of outbound messages into Telegram Bot API requests.
"""

from typing import Any, Dict, List, Optional, Union
import uuid
import requests

from universal_chatbot.channels.base import BaseChannelAdapter
from universal_chatbot.core.exceptions import SecurityValidationError
from universal_chatbot.core.protocol import (
    EngineResponse,
    IncomingMessage,
    OutgoingResponse,
    SessionStatus,
)


class TelegramChannelAdapter(BaseChannelAdapter):
    """Adapter for Telegram Bot API communication."""

    channel_type = "telegram"

    def normalize_message(
        self, raw_payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None
    ) -> IncomingMessage:
        """Parse raw incoming Telegram update payload into IncomingMessage protocol."""
        if not isinstance(raw_payload, dict):
            raise SecurityValidationError("Invalid payload format. Expected JSON dictionary.")

        headers = headers or {}

        # 1. Deployment ID
        deployment_id = (
            raw_payload.get("deployment_key")
            or raw_payload.get("deployment_id")
            or headers.get("x-deployment-key")
            or "telegram_default"
        )

        # 2. Extract Message / Callback Query
        is_callback = "callback_query" in raw_payload
        callback_query = raw_payload.get("callback_query") or {}
        message_data = (
            raw_payload.get("message")
            or raw_payload.get("edited_message")
            or raw_payload.get("channel_post")
            or (callback_query.get("message") if is_callback else {})
            or raw_payload
        )

        # 3. Sender / User extraction
        shared_phone = ""
        if is_callback:
            from_user = callback_query.get("from", {})
            chat = callback_query.get("message", {}).get("chat", {})
            user_id = str(from_user.get("id") or chat.get("id") or "")
            msg_id = str(callback_query.get("id") or uuid.uuid4())
            text = str(callback_query.get("data") or "").strip()
            chat_id = chat.get("id") or from_user.get("id")
        else:
            from_user = message_data.get("from", {})
            chat = message_data.get("chat", {})
            user_id = str(
                from_user.get("id")
                or chat.get("id")
                or raw_payload.get("external_user_id")
                or raw_payload.get("sender_id")
                or ""
            )
            msg_id = str(message_data.get("message_id") or raw_payload.get("message_id") or uuid.uuid4())
            contact_obj = message_data.get("contact") or {}
            shared_phone = contact_obj.get("phone_number", "")
            text = str(
                message_data.get("text")
                or shared_phone
                or raw_payload.get("text")
                or raw_payload.get("content")
                or ""
            ).strip()
            chat_id = chat.get("id") or from_user.get("id") or user_id

        if not user_id:
            raise SecurityValidationError("Missing required sender user ID in Telegram payload.")

        # 4. Message object
        message_dict = {
            "message_id": msg_id,
            "type": "contact" if shared_phone else "text",
            "text": text,
            "phone_number": shared_phone,
        }

        # 5. Metadata extraction
        language = from_user.get("language_code") or "en"
        meta_dict = {
            "language": language,
            "timezone": "UTC",
            "chat_id": chat_id,
            "first_name": from_user.get("first_name", ""),
            "last_name": from_user.get("last_name", ""),
            "username": from_user.get("username", ""),
            "update_id": raw_payload.get("update_id"),
            "is_callback": is_callback,
            "phone_number": shared_phone,
        }

        # Transfer any extra metadata
        extra = raw_payload.get("metadata")
        if isinstance(extra, dict):
            for k, v in extra.items():
                if k not in meta_dict:
                    meta_dict[k] = v

        return IncomingMessage(
            tenant_id=raw_payload.get("tenant_id"),
            bot_id=str(raw_payload.get("bot_id", "telegram_bot")),
            deployment_id=str(deployment_id),
            channel=self.channel_type,
            external_user_id=user_id,
            conversation_id=raw_payload.get("conversation_id"),
            message=message_dict,
            metadata=meta_dict,
        )

    def format_response(
        self,
        response: Union[OutgoingResponse, EngineResponse, Dict[str, Any]],
        recipient: Optional[Union[str, int]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Convert standard conversation engine response into Telegram sendMessage payload."""
        chat_id = recipient or kwargs.get("chat_id")

        text = ""
        actions: List[Dict[str, Any]] = []

        if isinstance(response, OutgoingResponse):
            text = response.response.get("text", "")
            actions = response.actions
        elif isinstance(response, EngineResponse):
            msgs = [m.to_dict() for m in response.messages]
            text = msgs[-1]["content"] if msgs else ""
        elif isinstance(response, dict):
            raw_msgs = response.get("messages", [])
            if raw_msgs:
                # Concatenate or take last
                text = raw_msgs[-1].get("text", "")
                for m in raw_msgs:
                    if m.get("options"):
                        for opt in m["options"]:
                            act_dict = {
                                "label": opt.get("label"),
                                "value": opt.get("value"),
                            }
                            if opt.get("url"):
                                act_dict["url"] = opt["url"]
                            if opt.get("web_app_url"):
                                act_dict["web_app_url"] = opt["web_app_url"]
                            actions.append(act_dict)
            else:
                text = response.get("response", {}).get("text", "")
            if not actions and response.get("actions"):
                actions = response["actions"]

        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "text": text or "...",
            "parse_mode": "HTML",
        }

        # Build keyboard buttons if options exist
        if actions:
            has_request_contact = any(act.get("request_contact") for act in actions)
            if has_request_contact:
                # Telegram requires ReplyKeyboardMarkup for request_contact buttons
                reply_keyboard = []
                row = []
                for act in actions:
                    lbl = act.get("label") or act.get("text") or act.get("value") or ""
                    btn = {"text": str(lbl)}
                    if act.get("request_contact"):
                        btn["request_contact"] = True
                    row.append(btn)
                    if len(row) >= 2:
                        reply_keyboard.append(row)
                        row = []
                if row:
                    reply_keyboard.append(row)
                payload["reply_markup"] = {
                    "keyboard": reply_keyboard,
                    "resize_keyboard": True,
                    "one_time_keyboard": True,
                }
            else:
                inline_keyboard = []
                row: List[Dict[str, str]] = []
                for act in actions:
                    lbl = act.get("label") or act.get("text") or act.get("value") or ""
                    url = act.get("url")
                    web_app_url = act.get("web_app_url")
                    val = act.get("value") or act.get("label") or ""

                    btn: Dict[str, Any] = {"text": str(lbl)}
                    if web_app_url:
                        btn["web_app"] = {"url": str(web_app_url)}
                    elif url:
                        btn["url"] = str(url)
                    else:
                        btn["callback_data"] = str(val)[:64]

                    row.append(btn)
                    if len(row) >= 2:
                        inline_keyboard.append(row)
                        row = []
                if row:
                    inline_keyboard.append(row)
                payload["reply_markup"] = {"inline_keyboard": inline_keyboard}

        return payload

    def send_telegram_message(
        self, bot_token: str, payload: Dict[str, Any]
    ) -> requests.Response:
        """Transmit formatted message payload to Telegram Bot API."""
        if not bot_token:
            raise ValueError("bot_token is required to send Telegram message.")

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        response = requests.post(url, json=payload, timeout=10)
        return response

    def answer_callback_query(
        self, bot_token: str, callback_query_id: str, text: Optional[str] = None
    ) -> Optional[requests.Response]:
        """Acknowledge Telegram callback query to stop loading spinner."""
        if not bot_token or not callback_query_id:
            return None
        url = f"https://api.telegram.org/bot{bot_token}/answerCallbackQuery"
        try:
            return requests.post(
                url, json={"callback_query_id": callback_query_id, "text": text or ""}, timeout=5
            )
        except Exception:
            return None


def telegram_webhook(deployment_key: Optional[str] = None) -> Dict[str, Any]:
    """Whitelisted Frappe webhook endpoint to receive incoming Telegram updates."""
    import frappe
    from universal_chatbot.channels.gateway import get_channel_gateway
    from universal_chatbot.universal_chatbot.doctype.bot_channel.bot_channel import BotChannel

    gateway = get_channel_gateway()
    headers = dict(getattr(frappe.local, "request", None) and frappe.local.request.headers or {})

    # Extract update payload
    raw_payload = frappe.request.get_json(force=True, silent=True) or dict(frappe.form_dict)

    dep_key = deployment_key or frappe.request.args.get("deployment_key") or raw_payload.get("deployment_key")

    # Optional Telegram Secret Token verification
    secret_header = headers.get("X-Telegram-Bot-Api-Secret-Token") or headers.get("x-telegram-bot-api-secret-token")

    # Route through Channel Gateway into Conversation Engine
    result = gateway.process_and_execute(
        channel_type="telegram",
        raw_payload=raw_payload,
        headers=headers,
        deployment_key=dep_key,
    )

    deployment = result.get("deployment")
    channel_doc = BotChannel.get_channel_by_deployment(deployment.name, channel_type="Telegram")
    if channel_doc:
        creds = channel_doc.get_credentials()
        bot_token = creds.get("bot_token")
        if bot_token and result.get("formatted_response"):
            adapter = gateway.get_adapter("telegram")
            if isinstance(adapter, TelegramChannelAdapter):
                try:
                    adapter.send_telegram_message(bot_token, result["formatted_response"])
                except Exception as e:
                    frappe.logger("universal_chatbot").error(f"Failed to send Telegram message: {e}")

    return {"status": "ok", "conversation_id": result.get("conversation_id")}


try:
    import frappe
    telegram_webhook = frappe.whitelist(allow_guest=True)(telegram_webhook)
except Exception:
    pass
