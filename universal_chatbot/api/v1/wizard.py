"""Guided Bot Creation Wizard API.

Provides atomic, multi-channel bot provisioning from templates with automatic
flow construction, version snapshot publishing, and channel deployment generation.
"""

import json
import re
from typing import Any, Dict, List, Optional
import frappe
from frappe import _
from universal_chatbot.api.v1.flow_designer import save_visual_flow, publish_flow


TEMPLATES: Dict[str, Dict[str, Any]] = {
    "api_lookup": {
        "id": "api_lookup",
        "title": "ERP & API Lookup Assistant",
        "description": "Prompts user for an ID/flat number, calls an external system via REST, and prints formatted output.",
        "badge": "Popular",
        "icon": "⚡",
        "flow": {
            "nodes": [
                {
                    "node_id": "start_node",
                    "node_type": "Start",
                    "configuration": {
                        "message": "Hello! Welcome to the automated assistant.",
                        "ui_x": 320,
                        "ui_y": 60,
                    },
                },
                {
                    "node_id": "ask_id_node",
                    "node_type": "Ask Question",
                    "configuration": {
                        "question": "Please enter your reference or flat number:",
                        "save_to_variable": "lookup_id",
                        "ui_x": 320,
                        "ui_y": 200,
                    },
                },
                {
                    "node_id": "call_action_node",
                    "node_type": "Call Action",
                    "configuration": {
                        "action_name": "get_maintenance_dues",
                        "parameters": {"flat_number": "{{lookup_id}}"},
                        "output_mapping": {
                            "owner_name": "owner_name",
                            "flat_details": "flat_details",
                            "outstanding_amount": "outstanding_amount",
                        },
                        "ui_x": 320,
                        "ui_y": 360,
                    },
                },
                {
                    "node_id": "send_result_node",
                    "node_type": "Send Message",
                    "configuration": {
                        "message": "Here are your details for {{lookup_id}}:\n👤 Name: {{owner_name}}\n🏢 Details: {{flat_details}}\n💰 Outstanding Dues: ₹ {{outstanding_amount}}",
                        "ui_x": 320,
                        "ui_y": 510,
                    },
                },
                {
                    "node_id": "end_node",
                    "node_type": "End",
                    "configuration": {
                        "message": "Thank you for using our service!",
                        "ui_x": 320,
                        "ui_y": 640,
                    },
                },
            ],
            "transitions": [
                {"source_node": "start_node", "target_node": "ask_id_node", "condition": ""},
                {"source_node": "ask_id_node", "target_node": "call_action_node", "condition": ""},
                {"source_node": "call_action_node", "target_node": "send_result_node", "condition": ""},
                {"source_node": "send_result_node", "target_node": "end_node", "condition": ""},
            ],
            "variables": [
                {"variable_name": "lookup_id", "data_type": "String", "default_value": ""},
                {"variable_name": "owner_name", "data_type": "String", "default_value": ""},
                {"variable_name": "flat_details", "data_type": "String", "default_value": ""},
                {"variable_name": "outstanding_amount", "data_type": "String", "default_value": ""},
            ],
        },
    },
    "simple_faq": {
        "id": "simple_faq",
        "title": "FAQ & Support Assistant",
        "description": "Interactive multiple choice menu with branches for business hours, contact info, and inquiries.",
        "badge": "Standard",
        "icon": "💬",
        "flow": {
            "nodes": [
                {
                    "node_id": "start_node",
                    "node_type": "Start",
                    "configuration": {
                        "message": "Hello! Welcome to our Customer Support Desk.",
                        "ui_x": 320,
                        "ui_y": 60,
                    },
                },
                {
                    "node_id": "menu_node",
                    "node_type": "Multiple Choice",
                    "configuration": {
                        "prompt": "How can we help you today?",
                        "options": [
                            {"label": "Office Hours", "value": "hours"},
                            {"label": "Contact Info", "value": "contact"},
                        ],
                        "ui_x": 320,
                        "ui_y": 200,
                    },
                },
                {
                    "node_id": "msg_hours",
                    "node_type": "Send Message",
                    "configuration": {
                        "message": "Our office is open Monday through Saturday, from 9:00 AM to 6:00 PM.",
                        "ui_x": 140,
                        "ui_y": 360,
                    },
                },
                {
                    "node_id": "msg_contact",
                    "node_type": "Send Message",
                    "configuration": {
                        "message": "You can reach our management office at support@example.com or call +91 94456 98019.",
                        "ui_x": 500,
                        "ui_y": 360,
                    },
                },
                {
                    "node_id": "end_node",
                    "node_type": "End",
                    "configuration": {
                        "message": "Thank you for reaching out. Have a wonderful day!",
                        "ui_x": 320,
                        "ui_y": 520,
                    },
                },
            ],
            "transitions": [
                {"source_node": "start_node", "target_node": "menu_node", "condition": ""},
                {"source_node": "menu_node", "target_node": "msg_hours", "condition": ""},
                {"source_node": "menu_node", "target_node": "msg_contact", "condition": ""},
                {"source_node": "msg_hours", "target_node": "end_node", "condition": ""},
                {"source_node": "msg_contact", "target_node": "end_node", "condition": ""},
            ],
            "variables": [],
        },
    },
    "blank": {
        "id": "blank",
        "title": "Blank Canvas",
        "description": "A minimal starting structure with just Start and Greeting, ready for custom design.",
        "badge": "Custom",
        "icon": "🎨",
        "flow": {
            "nodes": [
                {
                    "node_id": "start_node",
                    "node_type": "Start",
                    "configuration": {
                        "message": "Hello! I am your AI assistant. How can I help you?",
                        "ui_x": 320,
                        "ui_y": 100,
                    },
                },
                {
                    "node_id": "welcome_message",
                    "node_type": "Send Message",
                    "configuration": {
                        "message": "Feel free to ask any question.",
                        "ui_x": 320,
                        "ui_y": 260,
                    },
                },
                {
                    "node_id": "end_node",
                    "node_type": "End",
                    "configuration": {
                        "message": "Goodbye!",
                        "ui_x": 320,
                        "ui_y": 420,
                    },
                },
            ],
            "transitions": [
                {"source_node": "start_node", "target_node": "welcome_message", "condition": ""},
                {"source_node": "welcome_message", "target_node": "end_node", "condition": ""},
            ],
            "variables": [],
        },
    },
}

TEMPLATE_ALIAS_MAP: Dict[str, str] = {
    "erp & api lookup": "api_lookup",
    "erp & api lookup assistant": "api_lookup",
    "faq & support": "simple_faq",
    "faq & support assistant": "simple_faq",
    "blank canvas": "blank",
    "blank": "blank",
    "api_lookup": "api_lookup",
    "simple_faq": "simple_faq",
}


@frappe.whitelist()
def get_bot_templates() -> List[Dict[str, Any]]:
    """Return list of available starter templates."""
    frappe.has_permission("Chatbot", "read", throw=True)
    return [
        {
            "id": t["id"],
            "title": t["title"],
            "description": t["description"],
            "badge": t.get("badge", ""),
            "icon": t.get("icon", "🤖"),
            "nodes_count": len(t["flow"]["nodes"]),
        }
        for t in TEMPLATES.values()
    ]


@frappe.whitelist()
def get_bot_config(bot_slug: str) -> Dict[str, Any]:
    """Retrieve full configuration for a bot including its channels, credentials, and deployments."""
    frappe.has_permission("Chatbot", "read", throw=True)
    slug = (bot_slug or "").strip()
    if not slug or not frappe.db.exists("Chatbot", slug):
        frappe.throw(_("Chatbot '{0}' not found.").format(slug), exc=frappe.DoesNotExistError)

    chatbot_doc = frappe.get_doc("Chatbot", slug)
    base_host = frappe.utils.get_url()

    # Get channels
    channels_data = {}
    channels = frappe.get_all(
        "Bot Channel",
        filters={"chatbot": slug},
        fields=[
            "name",
            "channel_name",
            "channel_type",
            "is_enabled",
            "deployment",
            "whatsapp_phone_number_id",
            "whatsapp_verify_token",
            "telegram_webhook_secret",
        ],
    )

    for ch in channels:
        ch_doc = frappe.get_doc("Bot Channel", ch.name)
        creds = ch_doc.get_credentials()
        ch_type = ch.channel_type.lower().replace(" ", "_")
        channels_data[ch_type] = {
            "name": ch.name,
            "channel_type": ch.channel_type,
            "is_enabled": ch.is_enabled,
            "deployment": ch.deployment,
            "whatsapp_phone_number_id": ch.whatsapp_phone_number_id or "",
            "whatsapp_access_token": creds.get("access_token", ""),
            "whatsapp_verify_token": ch.whatsapp_verify_token or "",
            "telegram_bot_token": creds.get("bot_token", ""),
            "telegram_webhook_secret": ch.telegram_webhook_secret or "",
        }

    # Get deployments
    deployments = frappe.get_all(
        "Bot Deployment",
        filters={"chatbot": slug},
        fields=["name", "deployment_name", "channel", "status", "deployment_key", "allowed_domains"],
    )

    deployments_list = []
    for dep in deployments:
        dep_key = dep.deployment_key
        ch_type = ""
        matching_channels = [c for c in channels if c["name"] == dep.channel]
        if matching_channels:
            ch_type = matching_channels[0]["channel_type"]
        elif "whatsapp" in dep.deployment_name.lower():
            ch_type = "WhatsApp"
        elif "telegram" in dep.deployment_name.lower():
            ch_type = "Telegram"
        else:
            ch_type = "Web Widget"

        webhook_url = ""
        embed_script = ""
        if ch_type == "WhatsApp":
            webhook_url = f"{base_host}/api/method/universal_chatbot.api.v1.webhook.whatsapp_webhook?deployment_key={dep_key}"
        elif ch_type == "Telegram":
            webhook_url = f"{base_host}/api/method/universal_chatbot.api.v1.webhook.telegram_webhook?deployment_key={dep_key}"
        elif ch_type == "Web Widget":
            embed_script = f'<script src="{base_host}/assets/universal_chatbot/widget/chatbot-widget.js" data-deployment="{dep_key}"></script>'

        deployments_list.append({
            "name": dep.name,
            "deployment_name": dep.deployment_name,
            "channel": dep.channel,
            "channel_type": ch_type,
            "status": dep.status,
            "deployment_key": dep_key,
            "allowed_domains": dep.allowed_domains,
            "webhook_url": webhook_url,
            "embed_script": embed_script,
        })

    return {
        "bot_slug": chatbot_doc.name,
        "title": chatbot_doc.title,
        "status": chatbot_doc.status,
        "is_published": chatbot_doc.is_published,
        "primary_flow": chatbot_doc.primary_flow,
        "active_version": chatbot_doc.active_version,
        "description": chatbot_doc.description,
        "channels": channels_data,
        "deployments": deployments_list,
    }


@frappe.whitelist()
def update_bot_config(
    bot_slug: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    channels: Optional[Any] = None,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """Atomically updates a Chatbot document along with all its linked channels and deployments."""
    frappe.has_permission("Chatbot", "write", throw=True)
    slug = (bot_slug or "").strip()
    if not slug or not frappe.db.exists("Chatbot", slug):
        frappe.throw(_("Chatbot '{0}' not found.").format(slug), exc=frappe.DoesNotExistError)

    chatbot_doc = frappe.get_doc("Chatbot", slug)
    if title:
        chatbot_doc.title = title.strip()
    if description is not None:
        chatbot_doc.description = description
    if status:
        chatbot_doc.status = status
    chatbot_doc.save(ignore_permissions=True)

    title_clean = chatbot_doc.title

    if isinstance(channels, str):
        try:
            channels = json.loads(channels)
        except Exception:
            channels = []
    channels = channels or []

    for ch_cfg in channels:
        ch_type = (ch_cfg.get("channel_type") or ch_cfg.get("type") or "").strip().lower()
        if not ch_type:
            continue

        if "whatsapp" in ch_type:
            channel_name = f"{title_clean} WhatsApp Channel"
            dep_name = f"{title_clean} WhatsApp"
            is_enabled = 1 if ch_cfg.get("is_enabled", True) else 0

            # Find or create Bot Deployment
            dep_name_found = frappe.db.get_value(
                "Bot Deployment", {"chatbot": slug, "deployment_name": ["like", "%WhatsApp%"]}, "name"
            )
            if dep_name_found:
                dep_doc = frappe.get_doc("Bot Deployment", dep_name_found)
                dep_doc.status = "Active" if is_enabled else "Inactive"
                dep_doc.save(ignore_permissions=True)
            else:
                dep_key = f"wa_{frappe.generate_hash(length=12)}"
                dep_doc = frappe.get_doc({
                    "doctype": "Bot Deployment",
                    "deployment_name": dep_name,
                    "chatbot": slug,
                    "channel": channel_name,
                    "bot_version": chatbot_doc.active_version,
                    "status": "Active" if is_enabled else "Inactive",
                    "deployment_key": dep_key,
                    "allowed_domains": "*",
                })
                dep_doc.flags.ignore_mandatory = True
                dep_doc.flags.ignore_links = True
                dep_doc.insert(ignore_permissions=True)

            # Find or create Bot Channel
            ch_name_found = frappe.db.get_value(
                "Bot Channel", {"chatbot": slug, "channel_type": "WhatsApp"}, "name"
            )
            if ch_name_found:
                channel_doc = frappe.get_doc("Bot Channel", ch_name_found)
                channel_doc.is_enabled = is_enabled
                if "phone_number_id" in ch_cfg:
                    channel_doc.whatsapp_phone_number_id = str(ch_cfg["phone_number_id"]).strip()
                if "access_token" in ch_cfg and ch_cfg["access_token"]:
                    channel_doc.whatsapp_access_token = str(ch_cfg["access_token"]).strip()
                if "verify_token" in ch_cfg and ch_cfg["verify_token"]:
                    channel_doc.whatsapp_verify_token = str(ch_cfg["verify_token"]).strip()
                channel_doc.deployment = dep_doc.name
                channel_doc.bot_deployment = dep_doc.name
                channel_doc.save(ignore_permissions=True)
            else:
                channel_doc = frappe.get_doc({
                    "doctype": "Bot Channel",
                    "channel_name": channel_name,
                    "channel_type": "WhatsApp",
                    "is_enabled": is_enabled,
                    "chatbot": slug,
                    "deployment": dep_doc.name,
                    "bot_deployment": dep_doc.name,
                    "whatsapp_phone_number_id": (ch_cfg.get("phone_number_id") or "").strip(),
                    "whatsapp_access_token": (ch_cfg.get("access_token") or "").strip(),
                    "whatsapp_verify_token": (ch_cfg.get("verify_token") or f"verify_{frappe.generate_hash(length=8)}").strip(),
                }).insert(ignore_permissions=True)

            frappe.db.set_value("Bot Channel", channel_doc.name, "deployment", dep_doc.name)
            frappe.db.set_value("Bot Deployment", dep_doc.name, "channel", channel_doc.name)

        elif "telegram" in ch_type:
            channel_name = f"{title_clean} Telegram Channel"
            dep_name = f"{title_clean} Telegram"
            is_enabled = 1 if ch_cfg.get("is_enabled", True) else 0

            # Find or create Bot Deployment
            dep_name_found = frappe.db.get_value(
                "Bot Deployment", {"chatbot": slug, "deployment_name": ["like", "%Telegram%"]}, "name"
            )
            if dep_name_found:
                dep_doc = frappe.get_doc("Bot Deployment", dep_name_found)
                dep_doc.status = "Active" if is_enabled else "Inactive"
                dep_doc.save(ignore_permissions=True)
            else:
                dep_key = f"tg_{frappe.generate_hash(length=12)}"
                dep_doc = frappe.get_doc({
                    "doctype": "Bot Deployment",
                    "deployment_name": dep_name,
                    "chatbot": slug,
                    "channel": channel_name,
                    "bot_version": chatbot_doc.active_version,
                    "status": "Active" if is_enabled else "Inactive",
                    "deployment_key": dep_key,
                    "allowed_domains": "*",
                })
                dep_doc.flags.ignore_mandatory = True
                dep_doc.flags.ignore_links = True
                dep_doc.insert(ignore_permissions=True)

            # Find or create Bot Channel
            ch_name_found = frappe.db.get_value(
                "Bot Channel", {"chatbot": slug, "channel_type": "Telegram"}, "name"
            )
            if ch_name_found:
                channel_doc = frappe.get_doc("Bot Channel", ch_name_found)
                channel_doc.is_enabled = is_enabled
                if "bot_token" in ch_cfg and ch_cfg["bot_token"]:
                    channel_doc.telegram_bot_token = str(ch_cfg["bot_token"]).strip()
                channel_doc.deployment = dep_doc.name
                channel_doc.bot_deployment = dep_doc.name
                channel_doc.save(ignore_permissions=True)
            else:
                channel_doc = frappe.get_doc({
                    "doctype": "Bot Channel",
                    "channel_name": channel_name,
                    "channel_type": "Telegram",
                    "is_enabled": is_enabled,
                    "chatbot": slug,
                    "deployment": dep_doc.name,
                    "bot_deployment": dep_doc.name,
                    "telegram_bot_token": (ch_cfg.get("bot_token") or "").strip(),
                    "telegram_webhook_secret": frappe.generate_hash(length=16),
                }).insert(ignore_permissions=True)

            frappe.db.set_value("Bot Channel", channel_doc.name, "deployment", dep_doc.name)
            frappe.db.set_value("Bot Deployment", dep_doc.name, "channel", channel_doc.name)

        elif "web" in ch_type or "widget" in ch_type:
            channel_name = f"{title_clean} Web Widget"
            dep_name = f"{title_clean} Web Widget"
            is_enabled = 1 if ch_cfg.get("is_enabled", True) else 0

            # Find or create Bot Deployment
            dep_name_found = frappe.db.get_value(
                "Bot Deployment", {"chatbot": slug, "deployment_name": ["like", "%Web Widget%"]}, "name"
            )
            if dep_name_found:
                dep_doc = frappe.get_doc("Bot Deployment", dep_name_found)
                dep_doc.status = "Active" if is_enabled else "Inactive"
                if "allowed_domains" in ch_cfg:
                    dep_doc.allowed_domains = (ch_cfg["allowed_domains"] or "*").strip()
                dep_doc.save(ignore_permissions=True)
            else:
                dep_key = f"web_{frappe.generate_hash(length=12)}"
                dep_doc = frappe.get_doc({
                    "doctype": "Bot Deployment",
                    "deployment_name": dep_name,
                    "chatbot": slug,
                    "channel": channel_name,
                    "bot_version": chatbot_doc.active_version,
                    "status": "Active" if is_enabled else "Inactive",
                    "deployment_key": dep_key,
                    "allowed_domains": (ch_cfg.get("allowed_domains") or "*").strip(),
                })
                dep_doc.flags.ignore_mandatory = True
                dep_doc.flags.ignore_links = True
                dep_doc.insert(ignore_permissions=True)

            # Find or create Bot Channel
            ch_name_found = frappe.db.get_value(
                "Bot Channel", {"chatbot": slug, "channel_type": "Web Widget"}, "name"
            )
            if ch_name_found:
                channel_doc = frappe.get_doc("Bot Channel", ch_name_found)
                channel_doc.is_enabled = is_enabled
                channel_doc.deployment = dep_doc.name
                channel_doc.bot_deployment = dep_doc.name
                channel_doc.save(ignore_permissions=True)
            else:
                channel_doc = frappe.get_doc({
                    "doctype": "Bot Channel",
                    "channel_name": channel_name,
                    "channel_type": "Web Widget",
                    "is_enabled": is_enabled,
                    "chatbot": slug,
                    "deployment": dep_doc.name,
                    "bot_deployment": dep_doc.name,
                }).insert(ignore_permissions=True)

            frappe.db.set_value("Bot Channel", channel_doc.name, "deployment", dep_doc.name)
            frappe.db.set_value("Bot Deployment", dep_doc.name, "channel", channel_doc.name)

    frappe.db.commit()
    return get_bot_config(slug)


@frappe.whitelist()
def quick_create_bot(
    title: str,
    bot_slug: Optional[str] = None,
    description: Optional[str] = None,
    template_id: str = "api_lookup",
    channels: Optional[Any] = None,
    allow_existing: bool = False,
    edit_mode: bool = False,
) -> Dict[str, Any]:
    """Atomically provisions or updates a Chatbot, Chatbot Flow, Bot Version,
    and configures channels & deployments.

    Supports both create mode and edit mode (edit_mode=True).
    """
    is_edit = bool(frappe.utils.cint(edit_mode))
    frappe.has_permission("Chatbot", "write" if is_edit else "create", throw=True)

    title_clean = (title or "").strip()
    if not title_clean:
        frappe.throw(_("Bot Title is required."))

    # Generate or clean slug
    slug = (bot_slug or "").strip().lower()
    if not slug:
        slug = re.sub(r"[^a-z0-9_]+", "_", title_clean.lower()).strip("_")
    if not slug:
        slug = f"bot_{frappe.generate_hash(length=6)}"

    is_existing = frappe.db.exists("Chatbot", slug)
    if is_existing and not is_edit and not frappe.utils.cint(allow_existing):
        frappe.throw(_("Chatbot with ID '{0}' already exists. Please choose a different title or slug.").format(slug))

    template_key = TEMPLATE_ALIAS_MAP.get(str(template_id or "").strip().lower(), template_id)
    template = TEMPLATES.get(template_key) or TEMPLATES["blank"]

    # 1. Create or Update Chatbot Document
    if is_existing or is_edit:
        chatbot_doc = frappe.get_doc("Chatbot", slug)
        chatbot_doc.title = title_clean
        if description is not None:
            chatbot_doc.description = description
        chatbot_doc.save(ignore_permissions=True)
    else:
        chatbot_doc = frappe.get_doc({
            "doctype": "Chatbot",
            "bot_name": slug,
            "title": title_clean,
            "description": description or f"{title_clean} created via Guided Bot Wizard",
            "status": "Active",
            "is_published": 1,
            "greeting_message": f"Hello! Welcome to {title_clean}.",
            "fallback_message": "I'm sorry, I didn't quite catch that. Could you please rephrase?",
        }).insert(ignore_permissions=True)

    # 2. Create or Update Chatbot Flow
    existing_flow = frappe.db.get_value("Chatbot Flow", {"bot": slug, "flow_name": "main_flow"}, "name")
    if not existing_flow:
        existing_flow = frappe.db.get_value("Chatbot Flow", {"bot": slug}, "name")

    version_result = {}
    if existing_flow:
        flow_doc = frappe.get_doc("Chatbot Flow", existing_flow)
        actual_flow_name = flow_doc.name
        if not is_edit:
            # Overwrite with template only in create/scaffold mode
            flow_spec = template["flow"]
            save_visual_flow(flow_name=actual_flow_name, flow_data=flow_spec)
            version_result = publish_flow(
                flow_name=actual_flow_name,
                changelog=f"Release updated from template '{template['title']}' via Guided Wizard",
            )
        else:
            version_result = {
                "bot_version": chatbot_doc.active_version,
                "version_number": (chatbot_doc.active_version or "1.0.0").replace("v", ""),
            }
    else:
        flow_doc = frappe.get_doc({
            "doctype": "Chatbot Flow",
            "bot": slug,
            "flow_name": "main_flow",
            "status": "Draft",
            "version": "1.0.0",
            "description": f"Main flow for {title_clean}",
        }).insert(ignore_permissions=True)
        actual_flow_name = flow_doc.name
        flow_spec = template["flow"]
        save_visual_flow(flow_name=actual_flow_name, flow_data=flow_spec)
        version_result = publish_flow(
            flow_name=actual_flow_name,
            changelog=f"Initial release v1.0.0 generated from template '{template['title']}' via Guided Wizard",
        )

    # 3. Process Channels & Deployments
    if isinstance(channels, str):
        try:
            channels = json.loads(channels)
        except Exception:
            channels = []
    channels = channels or []

    created_deployments = []
    base_host = frappe.utils.get_url()

    for ch_cfg in channels:
        ch_type = ch_cfg.get("channel_type") or ch_cfg.get("type")
        if not ch_type:
            continue

        type_lower = ch_type.lower()
        is_enabled = 1 if ch_cfg.get("is_enabled", True) else 0

        if "whatsapp" in type_lower:
            channel_name = f"{title_clean} WhatsApp Channel"
            dep_name = f"{title_clean} WhatsApp"

            # Check existing Bot Deployment
            dep_name_found = frappe.db.get_value(
                "Bot Deployment", {"chatbot": slug, "deployment_name": ["like", "%WhatsApp%"]}, "name"
            )
            if not dep_name_found:
                dep_name_found = frappe.db.get_value("Bot Deployment", {"chatbot": slug, "name": ["like", "%WhatsApp%"]}, "name")

            if dep_name_found:
                dep_doc = frappe.get_doc("Bot Deployment", dep_name_found)
                dep_doc.status = "Active" if is_enabled else "Inactive"
                if version_result.get("bot_version"):
                    dep_doc.bot_version = version_result.get("bot_version")
                dep_key = dep_doc.deployment_key
                dep_doc.save(ignore_permissions=True)
            else:
                dep_key = f"wa_{frappe.generate_hash(length=12)}"
                dep_doc = frappe.get_doc({
                    "doctype": "Bot Deployment",
                    "deployment_name": dep_name,
                    "chatbot": slug,
                    "channel": channel_name,
                    "bot_version": version_result.get("bot_version"),
                    "status": "Active" if is_enabled else "Inactive",
                    "deployment_key": dep_key,
                    "allowed_domains": "*",
                })
                dep_doc.flags.ignore_mandatory = True
                dep_doc.flags.ignore_links = True
                dep_doc.insert(ignore_permissions=True)

            # Check existing Bot Channel
            ch_name_found = frappe.db.get_value(
                "Bot Channel", {"chatbot": slug, "channel_type": "WhatsApp"}, "name"
            )
            if not ch_name_found:
                ch_name_found = frappe.db.get_value(
                    "Bot Channel", {"chatbot": slug, "channel_name": ["like", "%WhatsApp%"]}, "name"
                )

            if ch_name_found:
                channel_doc = frappe.get_doc("Bot Channel", ch_name_found)
                channel_doc.is_enabled = is_enabled
                channel_doc.deployment = dep_doc.name
                channel_doc.bot_deployment = dep_doc.name
                if "phone_number_id" in ch_cfg:
                    channel_doc.whatsapp_phone_number_id = str(ch_cfg["phone_number_id"]).strip()
                if "access_token" in ch_cfg and ch_cfg["access_token"]:
                    channel_doc.whatsapp_access_token = str(ch_cfg["access_token"]).strip()
                if "verify_token" in ch_cfg and ch_cfg["verify_token"]:
                    channel_doc.whatsapp_verify_token = str(ch_cfg["verify_token"]).strip()
                channel_doc.save(ignore_permissions=True)
            else:
                channel_doc = frappe.get_doc({
                    "doctype": "Bot Channel",
                    "channel_name": channel_name,
                    "channel_type": "WhatsApp",
                    "is_enabled": is_enabled,
                    "chatbot": slug,
                    "deployment": dep_doc.name,
                    "bot_deployment": dep_doc.name,
                    "whatsapp_phone_number_id": (ch_cfg.get("phone_number_id") or "").strip(),
                    "whatsapp_access_token": (ch_cfg.get("access_token") or "").strip(),
                    "whatsapp_verify_token": (ch_cfg.get("verify_token") or f"verify_{frappe.generate_hash(length=8)}").strip(),
                }).insert(ignore_permissions=True)

            # Ensure bidirectional reference integrity
            frappe.db.set_value("Bot Channel", channel_doc.name, "deployment", dep_doc.name)
            frappe.db.set_value("Bot Deployment", dep_doc.name, "channel", channel_doc.name)

            webhook_url = f"{base_host}/api/method/universal_chatbot.api.v1.webhook.whatsapp_webhook?deployment_key={dep_key}"

            created_deployments.append({
                "channel_type": "WhatsApp",
                "channel_name": channel_doc.name,
                "deployment_name": dep_doc.name,
                "deployment_key": dep_key,
                "webhook_url": webhook_url,
                "verify_token": channel_doc.whatsapp_verify_token,
            })

        elif "telegram" in type_lower:
            channel_name = f"{title_clean} Telegram Channel"
            dep_name = f"{title_clean} Telegram"

            # Check existing Bot Deployment
            dep_name_found = frappe.db.get_value(
                "Bot Deployment", {"chatbot": slug, "deployment_name": ["like", "%Telegram%"]}, "name"
            )
            if not dep_name_found:
                dep_name_found = frappe.db.get_value("Bot Deployment", {"chatbot": slug, "name": ["like", "%Telegram%"]}, "name")

            if dep_name_found:
                dep_doc = frappe.get_doc("Bot Deployment", dep_name_found)
                dep_doc.status = "Active" if is_enabled else "Inactive"
                if version_result.get("bot_version"):
                    dep_doc.bot_version = version_result.get("bot_version")
                dep_key = dep_doc.deployment_key
                dep_doc.save(ignore_permissions=True)
            else:
                dep_key = f"tg_{frappe.generate_hash(length=12)}"
                dep_doc = frappe.get_doc({
                    "doctype": "Bot Deployment",
                    "deployment_name": dep_name,
                    "chatbot": slug,
                    "channel": channel_name,
                    "bot_version": version_result.get("bot_version"),
                    "status": "Active" if is_enabled else "Inactive",
                    "deployment_key": dep_key,
                    "allowed_domains": "*",
                })
                dep_doc.flags.ignore_mandatory = True
                dep_doc.flags.ignore_links = True
                dep_doc.insert(ignore_permissions=True)

            # Check existing Bot Channel
            ch_name_found = frappe.db.get_value(
                "Bot Channel", {"chatbot": slug, "channel_type": "Telegram"}, "name"
            )
            if not ch_name_found:
                ch_name_found = frappe.db.get_value(
                    "Bot Channel", {"chatbot": slug, "channel_name": ["like", "%Telegram%"]}, "name"
                )

            if ch_name_found:
                channel_doc = frappe.get_doc("Bot Channel", ch_name_found)
                channel_doc.is_enabled = is_enabled
                channel_doc.deployment = dep_doc.name
                channel_doc.bot_deployment = dep_doc.name
                if "bot_token" in ch_cfg and ch_cfg["bot_token"]:
                    channel_doc.telegram_bot_token = str(ch_cfg["bot_token"]).strip()
                channel_doc.save(ignore_permissions=True)
            else:
                channel_doc = frappe.get_doc({
                    "doctype": "Bot Channel",
                    "channel_name": channel_name,
                    "channel_type": "Telegram",
                    "is_enabled": is_enabled,
                    "chatbot": slug,
                    "deployment": dep_doc.name,
                    "bot_deployment": dep_doc.name,
                    "telegram_bot_token": (ch_cfg.get("bot_token") or "").strip(),
                    "telegram_webhook_secret": frappe.generate_hash(length=16),
                }).insert(ignore_permissions=True)

            # Ensure bidirectional reference integrity
            frappe.db.set_value("Bot Channel", channel_doc.name, "deployment", dep_doc.name)
            frappe.db.set_value("Bot Deployment", dep_doc.name, "channel", channel_doc.name)

            webhook_url = f"{base_host}/api/method/universal_chatbot.api.v1.webhook.telegram_webhook?deployment_key={dep_key}"

            created_deployments.append({
                "channel_type": "Telegram",
                "channel_name": channel_doc.name,
                "deployment_name": dep_doc.name,
                "deployment_key": dep_key,
                "webhook_url": webhook_url,
            })

        elif "web" in type_lower or "widget" in type_lower:
            channel_name = f"{title_clean} Web Widget"
            dep_name = f"{title_clean} Web Widget"

            # Check existing Bot Deployment
            dep_name_found = frappe.db.get_value(
                "Bot Deployment", {"chatbot": slug, "deployment_name": ["like", "%Web Widget%"]}, "name"
            )
            if not dep_name_found:
                dep_name_found = frappe.db.get_value("Bot Deployment", {"chatbot": slug, "name": ["like", "%Web%"]}, "name")

            if dep_name_found:
                dep_doc = frappe.get_doc("Bot Deployment", dep_name_found)
                dep_doc.status = "Active" if is_enabled else "Inactive"
                if version_result.get("bot_version"):
                    dep_doc.bot_version = version_result.get("bot_version")
                if "allowed_domains" in ch_cfg:
                    dep_doc.allowed_domains = (ch_cfg["allowed_domains"] or "*").strip()
                dep_key = dep_doc.deployment_key
                dep_doc.save(ignore_permissions=True)
            else:
                dep_key = f"web_{frappe.generate_hash(length=12)}"
                dep_doc = frappe.get_doc({
                    "doctype": "Bot Deployment",
                    "deployment_name": dep_name,
                    "chatbot": slug,
                    "channel": channel_name,
                    "bot_version": version_result.get("bot_version"),
                    "status": "Active" if is_enabled else "Inactive",
                    "deployment_key": dep_key,
                    "allowed_domains": (ch_cfg.get("allowed_domains") or "*").strip(),
                })
                dep_doc.flags.ignore_mandatory = True
                dep_doc.flags.ignore_links = True
                dep_doc.insert(ignore_permissions=True)

            # Check existing Bot Channel
            ch_name_found = frappe.db.get_value(
                "Bot Channel", {"chatbot": slug, "channel_type": "Web Widget"}, "name"
            )
            if not ch_name_found:
                ch_name_found = frappe.db.get_value(
                    "Bot Channel", {"chatbot": slug, "channel_name": ["like", "%Web Widget%"]}, "name"
                )

            if ch_name_found:
                channel_doc = frappe.get_doc("Bot Channel", ch_name_found)
                channel_doc.is_enabled = is_enabled
                channel_doc.deployment = dep_doc.name
                channel_doc.bot_deployment = dep_doc.name
                channel_doc.save(ignore_permissions=True)
            else:
                channel_doc = frappe.get_doc({
                    "doctype": "Bot Channel",
                    "channel_name": channel_name,
                    "channel_type": "Web Widget",
                    "is_enabled": is_enabled,
                    "chatbot": slug,
                    "deployment": dep_doc.name,
                    "bot_deployment": dep_doc.name,
                }).insert(ignore_permissions=True)

            # Ensure bidirectional reference integrity
            frappe.db.set_value("Bot Channel", channel_doc.name, "deployment", dep_doc.name)
            frappe.db.set_value("Bot Deployment", dep_doc.name, "channel", channel_doc.name)

            embed_script = f'<script src="{base_host}/assets/universal_chatbot/widget/chatbot-widget.js" data-deployment="{dep_key}"></script>'

            created_deployments.append({
                "channel_type": "Web Widget",
                "channel_name": channel_doc.name,
                "deployment_name": dep_doc.name,
                "deployment_key": dep_key,
                "embed_script": embed_script,
            })

    frappe.db.commit()

    return {
        "status": "success",
        "bot_slug": slug,
        "title": title_clean,
        "flow_name": actual_flow_name,
        "bot_version": version_result.get("bot_version"),
        "version_number": version_result.get("version_number"),
        "deployments": created_deployments,
        "designer_url": f"/app/flow-designer/{actual_flow_name}",
    }


@frappe.whitelist()
def get_bot_flows(bot_slug: str) -> List[Dict[str, Any]]:
    """Retrieve all Chatbot Flow records linked to this bot."""
    frappe.has_permission("Chatbot", "read", throw=True)
    slug = (bot_slug or "").strip()
    if not slug:
        return []

    bot_doc = frappe.get_doc("Chatbot", slug) if frappe.db.exists("Chatbot", slug) else None
    primary_flow = bot_doc.primary_flow if bot_doc else None

    flows = frappe.get_all(
        "Chatbot Flow",
        filters={"bot": slug},
        fields=["name", "flow_name", "status", "version", "description", "modified"],
        order_by="modified desc",
    )

    results = []
    for f in flows:
        node_count = frappe.db.count("Flow Node", {"flow": f.name})
        results.append({
            "name": f.name,
            "flow_name": f.flow_name,
            "title": f.flow_name.replace("_", " ").title(),
            "status": f.status or "Draft",
            "version": f.version or "1.0.0",
            "description": f.description or "",
            "is_primary": (f.name == primary_flow),
            "node_count": node_count,
            "modified": frappe.utils.format_datetime(f.modified, "medium") if f.modified else "",
        })
    return results


@frappe.whitelist()
def create_chatbot_flow(
    bot_slug: str,
    flow_name: str,
    title: str = "",
    description: str = "",
    set_as_primary: int = 0,
) -> Dict[str, Any]:
    """Create a new Chatbot Flow linked to this bot and seed starter canvas nodes."""
    frappe.has_permission("Chatbot Flow", "create", throw=True)
    slug = (bot_slug or "").strip()
    if not slug or not frappe.db.exists("Chatbot", slug):
        frappe.throw(_("Chatbot '{0}' not found.").format(slug))

    raw_flow_name = (flow_name or title or "").strip()
    clean_flow_name = re.sub(r"[^a-zA-Z0-9_]+", "_", raw_flow_name).strip("_").lower()
    if not clean_flow_name:
        clean_flow_name = f"flow_{frappe.generate_hash(length=6)}"

    expected_flow_id = f"{slug}-{clean_flow_name}"
    if frappe.db.exists("Chatbot Flow", expected_flow_id):
        clean_flow_name = f"{clean_flow_name}_{frappe.generate_hash(length=4)}"

    flow_doc = frappe.get_doc({
        "doctype": "Chatbot Flow",
        "bot": slug,
        "flow_name": clean_flow_name,
        "status": "Draft",
        "version": "1.0.0",
        "description": description or f"Flow for {slug}",
    }).insert(ignore_permissions=True)

    # Seed starter canvas nodes (Start -> End) so visual designer opens ready to use
    starter_nodes = [
        {
            "node_id": "start_node",
            "node_type": "Start",
            "configuration": {
                "message": f"Hello! Starting flow {clean_flow_name}.",
                "ui_x": 320,
                "ui_y": 80,
            },
        },
        {
            "node_id": "end_node",
            "node_type": "End",
            "configuration": {
                "message": "Flow completed.",
                "ui_x": 320,
                "ui_y": 280,
            },
        },
    ]
    starter_transitions = [
        {"source_node": "start_node", "target_node": "end_node", "condition": ""}
    ]
    save_visual_flow(
        flow_name=flow_doc.name,
        flow_data={
            "nodes": starter_nodes,
            "transitions": starter_transitions,
            "variables": [],
        },
    )

    if int(set_as_primary or 0):
        frappe.db.set_value("Chatbot", slug, "primary_flow", flow_doc.name)

    frappe.db.commit()

    return {
        "status": "success",
        "flow_name": flow_doc.name,
        "message": _("Flow '{0}' created successfully!").format(flow_doc.name),
        "designer_url": f"/app/flow-designer/{flow_doc.name}",
    }


@frappe.whitelist()
def update_chatbot_flow_properties(
    flow_name: str,
    title: str = "",
    description: str = "",
    status: str = "Draft",
    version: str = "1.0.0",
    set_as_primary: int = 0,
) -> Dict[str, Any]:
    """Update metadata properties of an existing flow."""
    frappe.has_permission("Chatbot Flow", "write", throw=True)
    flow_id = (flow_name or "").strip()
    if not flow_id or not frappe.db.exists("Chatbot Flow", flow_id):
        frappe.throw(_("Chatbot Flow '{0}' not found.").format(flow_id))

    flow_doc = frappe.get_doc("Chatbot Flow", flow_id)
    if description is not None:
        flow_doc.description = description
    if status:
        flow_doc.status = status
    if version:
        flow_doc.version = version
    flow_doc.save(ignore_permissions=True)

    bot_slug = flow_doc.bot
    if bot_slug and frappe.db.exists("Chatbot", bot_slug):
        cur_primary = frappe.db.get_value("Chatbot", bot_slug, "primary_flow")
        if int(set_as_primary or 0):
            frappe.db.set_value("Chatbot", bot_slug, "primary_flow", flow_doc.name)
        elif not int(set_as_primary or 0) and cur_primary == flow_doc.name:
            frappe.db.set_value("Chatbot", bot_slug, "primary_flow", None)

    frappe.db.commit()
    return {"status": "success", "message": _("Flow properties updated.")}


@frappe.whitelist()
def delete_chatbot_flow(flow_name: str) -> Dict[str, Any]:
    """Delete a flow and its flow nodes, and clear primary_flow if linked."""
    frappe.has_permission("Chatbot Flow", "delete", throw=True)
    flow_id = (flow_name or "").strip()
    if not flow_id or not frappe.db.exists("Chatbot Flow", flow_id):
        return {"status": "success", "message": _("Flow already removed.")}

    flow_doc = frappe.get_doc("Chatbot Flow", flow_id)
    bot_slug = flow_doc.bot

    # If this flow was primary on Chatbot, clear it
    if bot_slug and frappe.db.exists("Chatbot", bot_slug):
        cur_primary = frappe.db.get_value("Chatbot", bot_slug, "primary_flow")
        if cur_primary == flow_id:
            frappe.db.set_value("Chatbot", bot_slug, "primary_flow", None)

    # Delete linked Flow Node records
    frappe.db.delete("Flow Node", {"flow": flow_id})

    # Delete the Chatbot Flow doc
    frappe.delete_doc("Chatbot Flow", flow_id, ignore_permissions=True)
    frappe.db.commit()

    return {"status": "success", "message": _("Flow '{0}' deleted successfully.").format(flow_id)}


@frappe.whitelist()
def delete_bot_channel(channel_name: str) -> Dict[str, Any]:
    """Delete a Bot Channel and its associated Bot Deployment."""
    frappe.has_permission("Bot Channel", "delete", throw=True)
    ch_id = (channel_name or "").strip()
    if not ch_id or not frappe.db.exists("Bot Channel", ch_id):
        return {"status": "success", "message": _("Channel already removed.")}

    ch_doc = frappe.get_doc("Bot Channel", ch_id)
    dep_name = ch_doc.deployment or getattr(ch_doc, "bot_deployment", None)

    # Also look for any deployment referencing this channel
    linked_deps = frappe.get_all("Bot Deployment", filters={"channel": ch_id}, pluck="name")
    if dep_name and dep_name not in linked_deps:
        linked_deps.append(dep_name)

    # Break bidirectional links first so Frappe delete_doc won't throw LinkExistsError
    frappe.db.set_value("Bot Channel", ch_id, "deployment", None, update_modified=False)
    for d_name in linked_deps:
        if frappe.db.exists("Bot Deployment", d_name):
            frappe.db.set_value("Bot Deployment", d_name, "channel", None, update_modified=False)

    # Delete deployments
    for d_name in linked_deps:
        if frappe.db.exists("Bot Deployment", d_name):
            frappe.delete_doc("Bot Deployment", d_name, force=1, ignore_permissions=True)

    # Delete the channel
    frappe.delete_doc("Bot Channel", ch_id, force=1, ignore_permissions=True)
    frappe.db.commit()

    return {"status": "success", "message": _("Channel '{0}' deleted successfully.").format(ch_id)}
