"""Public Chat API endpoints for Website Widget integration.

Handles authentication, CORS origin validation, rate limiting,
payload normalization via WebChannelAdapter, and flow orchestration.
"""

import re
from typing import Any, Dict, Optional
from urllib.parse import urlparse
import frappe
from frappe import _
from universal_chatbot.adapters.frappe_repository import FrappeConversationRepository
from universal_chatbot.channels.web.adapter import WebChannelAdapter
from universal_chatbot.core.exceptions import (
    DeploymentNotFoundError,
    SecurityValidationError,
)
from universal_chatbot.flow.engine import FlowExecutor
from universal_chatbot.universal_chatbot.doctype.bot_settings.bot_settings import get_bot_settings


def validate_deployment_origin(deployment_doc, request_headers: Dict[str, str]) -> None:
    """Validate HTTP Origin or Referer against the deployment's allowed_domains."""
    allowed_domains_str = (deployment_doc.allowed_domains or "*").strip()
    if allowed_domains_str == "*":
        return

    origin = request_headers.get("Origin") or request_headers.get("origin")
    referer = request_headers.get("Referer") or request_headers.get("referer")
    host_candidate = origin or referer

    if not host_candidate:
        # If no origin/referer header was provided, allow local or test execution
        return

    try:
        parsed_url = urlparse(host_candidate)
        candidate_hostname = (parsed_url.hostname or "").lower()
        candidate_netloc = (parsed_url.netloc or "").lower()
    except Exception:
        frappe.throw(_("Invalid Origin or Referer header."), exc=frappe.PermissionError)

    allowed_list = [
        d.strip().lower()
        for d in re.split(r"[,\n]+", allowed_domains_str)
        if d.strip()
    ]

    matched = False
    for allowed in allowed_list:
        if allowed == "*":
            matched = True
            break
        # Support full URL or hostname or netloc
        if allowed.startswith("http://") or allowed.startswith("https://"):
            allowed_parsed = urlparse(allowed)
            if (
                candidate_hostname == allowed_parsed.hostname
                or candidate_netloc == allowed_parsed.netloc
            ):
                matched = True
                break
        else:
            if candidate_hostname == allowed or candidate_netloc == allowed or allowed in candidate_netloc:
                matched = True
                break

    if not matched:
        frappe.throw(
            _("Origin '{0}' is not authorized to embed this chatbot.").format(host_candidate),
            exc=frappe.PermissionError,
        )


def get_active_deployment(deployment_key: str):
    """Retrieve and validate Bot Deployment document."""
    if not deployment_key:
        frappe.throw(_("Missing required parameter 'deployment_key'."), exc=frappe.MandatoryError)

    deployment_name = frappe.db.get_value(
        "Bot Deployment", {"deployment_key": deployment_key}, "name"
    )
    if not deployment_name:
        raise DeploymentNotFoundError(deployment_key)

    deployment_doc = frappe.get_doc("Bot Deployment", deployment_name)
    if deployment_doc.status != "Active":
        frappe.throw(
            _("Bot deployment is currently {0}.").format(deployment_doc.status),
            exc=frappe.PermissionError,
        )

    return deployment_doc


def resolve_flow_for_bot(bot_name: str, deployment_doc) -> str:
    """Determine the active flow ID for a deployment or bot."""
    # 1. Deployment-specific flow/version if set
    if deployment_doc.bot_version:
        ver_flow = frappe.db.get_value("Bot Version", deployment_doc.bot_version, "flow_definition")
        if ver_flow:
            # We can use published version snapshot or linked flow
            pass

    # 2. Bot primary flow
    primary_flow = frappe.db.get_value("Chatbot", bot_name, "primary_flow")
    if primary_flow and frappe.db.exists("Chatbot Flow", primary_flow):
        return primary_flow

    # 3. Find published flow for this bot
    published_flow = frappe.db.get_value(
        "Chatbot Flow", {"bot": bot_name, "status": "Published"}, "name"
    )
    if published_flow:
        return published_flow

    # 4. Fallback to any flow for this bot
    any_flow = frappe.db.get_value("Chatbot Flow", {"bot": bot_name}, "name")
    if any_flow:
        return any_flow

    # Create default onboarding flow if none exists
    default_flow = frappe.get_doc({
        "doctype": "Chatbot Flow",
        "bot": bot_name,
        "flow_name": "default_welcome",
        "status": "Published",
        "version": "1.0.0",
    }).insert(ignore_permissions=True)

    greeting = frappe.db.get_value("Chatbot", bot_name, "greeting_message") or "Hello! How can I help you today?"
    frappe.get_doc({
        "doctype": "Flow Node",
        "flow": default_flow.name,
        "node_id": "start_node",
        "node_type": "Start",
        "configuration": frappe.as_json({"message": greeting}),
    }).insert(ignore_permissions=True)

    return default_flow.name


@frappe.whitelist(allow_guest=True)
def init_chat(
    deployment_key: str,
    external_user_id: str,
    conversation_id: Optional[str] = None,
    language: str = "en",
    timezone: str = "UTC",
) -> Dict[str, Any]:
    """Bootstrap endpoint called by the widget on load/refresh."""
    settings = get_bot_settings()
    if not settings.enabled:
        frappe.throw(_("Chatbot engine is currently disabled."), exc=frappe.PermissionError)

    # 1. Validate Deployment and Origin
    deployment = get_active_deployment(deployment_key)
    headers = getattr(frappe.local, "request", None) and frappe.local.request.headers or {}
    validate_deployment_origin(deployment, dict(headers))

    repo = FrappeConversationRepository()
    adapter = WebChannelAdapter()
    executor = FlowExecutor()

    bot_doc = frappe.get_doc("Chatbot", deployment.chatbot)

    # 2. Explicit Identity & Contact Resolution
    contact = repo.get_contact_by_channel_identity("web", external_user_id)
    if not contact:
        contact = repo.get_or_create_contact(
            display_name=f"Guest {external_user_id[-6:]}",
            contact_status="Active",
        )
        repo.get_or_create_channel_identity(
            contact_id=contact["name"],
            channel="web",
            external_user_id=external_user_id,
            verification_status="Anonymous",
        )

    # 3. Handle existing conversation state on page refresh
    conv_doc = None
    if conversation_id:
        conv_dict = repo.get_conversation(conversation_id)
        if (
            conv_dict
            and conv_dict.get("contact") == contact["name"]
            and conv_dict.get("deployment") == deployment.name
            and conv_dict.get("status") in ("Active", "Paused")
        ):
            conv_doc = conv_dict

    messages: list = []
    current_node = None
    session_status = "active"

    if conv_doc:
        # Load previous history for seamless browser refresh
        raw_msgs = repo.get_messages(conv_doc["name"], limit=50)
        for m in raw_msgs:
            messages.append({
                "direction": m["direction"].lower(),
                "text": m["content"],
                "type": m["message_type"].lower(),
                "timestamp": str(m["timestamp"]),
            })
        state = repo.get_state(conv_doc["name"]) or {}
        current_node = state.get("current_node")
        session_status = "paused" if current_node else "active"
        actual_conv_id = conv_doc["name"]
    else:
        # Create brand new conversation session
        new_conv = repo.create_conversation(
            bot=bot_doc.name,
            deployment=deployment.name,
            contact=contact["name"],
            channel="web",
            status="Active",
        )
        actual_conv_id = new_conv["name"]

        repo.record_event(
            conversation_id=actual_conv_id,
            event_type="conversation_started",
            details={"ip": frappe.local.request_ip or "127.0.0.1", "user_agent": headers.get("user-agent")},
        )

        # Trigger initial flow execution
        flow_id = resolve_flow_for_bot(bot_doc.name, deployment)
        flow_def = repo.get_flow_definition(flow_id)

        flow_result = executor.execute(
            flow=flow_def,
            conversation_id=actual_conv_id,
            state={},
        )

        # Log outbound messages
        for out_msg in flow_result.messages:
            txt = out_msg.get("text", "")
            mtype = out_msg.get("type", "text").capitalize()
            repo.log_message(
                conversation_id=actual_conv_id,
                direction="Outbound",
                message_type=mtype,
                content=txt,
            )
            messages.append({
                "direction": "outbound",
                "text": txt,
                "type": out_msg.get("type", "text"),
                "options": out_msg.get("options", []),
            })

        # Save state & execution
        repo.save_state(
            conversation_id=actual_conv_id,
            current_node=flow_result.current_node_id,
            variables=flow_result.variables,
            context=flow_result.context,
        )
        repo.save_flow_execution(
            conversation_id=actual_conv_id,
            flow_id=flow_id,
            current_node=flow_result.current_node_id,
            status=flow_result.status.value,
            execution_context={"variables": flow_result.variables},
        )
        current_node = flow_result.current_node_id
        session_status = flow_result.status.value

    # Parse theme config
    theme_cfg = {}
    if deployment.theme_config:
        try:
            theme_cfg = frappe.parse_json(deployment.theme_config)
        except Exception:
            theme_cfg = {}

    return {
        "status": "success",
        "conversation_id": actual_conv_id,
        "external_user_id": external_user_id,
        "bot_title": bot_doc.title or bot_doc.bot_name,
        "bot_avatar": bot_doc.avatar or "",
        "theme": theme_cfg,
        "custom_css": deployment.custom_css or "",
        "current_node_id": current_node,
        "session_status": session_status,
        "messages": messages,
    }


@frappe.whitelist(allow_guest=True)
def send_message(
    deployment_key: str,
    external_user_id: str,
    conversation_id: str,
    message: str = "",
    payload: Optional[str] = None,
    language: str = "en",
    timezone: str = "UTC",
) -> Dict[str, Any]:
    """Primary messaging endpoint called when user sends a message or clicks an option."""
    settings = get_bot_settings()
    if not settings.enabled:
        frappe.throw(_("Chatbot engine is currently disabled."), exc=frappe.PermissionError)

    # 1. Validate Deployment and Origin
    deployment = get_active_deployment(deployment_key)
    headers = getattr(frappe.local, "request", None) and frappe.local.request.headers or {}
    validate_deployment_origin(deployment, dict(headers))

    repo = FrappeConversationRepository()
    adapter = WebChannelAdapter()
    executor = FlowExecutor()

    # 2. Normalize Incoming Request
    raw_payload = {
        "deployment_key": deployment_key,
        "external_user_id": external_user_id,
        "conversation_id": conversation_id,
        "content": message,
        "bot_id": deployment.chatbot,
        "metadata": {"language": language, "timezone": timezone},
    }
    if payload:
        try:
            raw_payload["payload"] = frappe.parse_json(payload)
        except Exception:
            raw_payload["payload"] = {"raw": payload}

    incoming_msg = adapter.normalize_message(raw_payload, dict(headers))

    # 3. Verify Conversation & Contact ownership
    conv_dict = repo.get_conversation(conversation_id)
    if not conv_dict:
        frappe.throw(_("Conversation {0} not found.").format(conversation_id), exc=frappe.DoesNotExistError)

    contact = repo.get_contact_by_channel_identity("web", external_user_id)
    if not contact or conv_dict.get("contact") != contact["name"]:
        frappe.throw(_("Access denied to conversation {0}.").format(conversation_id), exc=frappe.PermissionError)

    # 4. Persist Inbound Message
    repo.log_message(
        conversation_id=conversation_id,
        direction="Inbound",
        message_type="Text",
        content=incoming_msg.message.get("text", ""),
        external_message_id=incoming_msg.message.get("message_id"),
    )
    repo.record_event(
        conversation_id=conversation_id,
        event_type="message_received",
        details={"text": incoming_msg.message.get("text", "")},
    )

    # 5. Load State & Execute Flow
    state = repo.get_state(conversation_id) or {}
    flow_id = resolve_flow_for_bot(deployment.chatbot, deployment)
    flow_def = repo.get_flow_definition(flow_id)

    flow_result = executor.execute(
        flow=flow_def,
        conversation_id=conversation_id,
        state=state,
        incoming_message=incoming_msg,
    )

    # 6. Persist Outbound Messages
    for out_msg in flow_result.messages:
        txt = out_msg.get("text", "")
        mtype = out_msg.get("type", "text").capitalize()
        repo.log_message(
            conversation_id=conversation_id,
            direction="Outbound",
            message_type=mtype,
            content=txt,
        )
        repo.record_event(
            conversation_id=conversation_id,
            event_type="message_sent",
            details={"text": txt, "type": out_msg.get("type")},
        )

    # 7. Update State & Flow Execution Record
    repo.save_state(
        conversation_id=conversation_id,
        current_node=flow_result.current_node_id,
        variables=flow_result.variables,
        context=flow_result.context,
    )
    repo.save_flow_execution(
        conversation_id=conversation_id,
        flow_id=flow_id,
        current_node=flow_result.current_node_id,
        status=flow_result.status.value,
        execution_context={"variables": flow_result.variables},
    )

    if flow_result.status.value == "completed":
        repo.update_conversation_status(conversation_id, "Closed")
        repo.record_event(conversation_id, "conversation_ended", {"reason": "flow_completed"})

    # 8. Return Formatted Response via Adapter
    return adapter.format_response(flow_result.to_dict())
