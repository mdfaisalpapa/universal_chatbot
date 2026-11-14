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


@frappe.whitelist()
def get_bot_integrations(bot_slug: str) -> List[Dict[str, Any]]:
    """Retrieve all Chatbot Integrations and Actions available and/or linked to this bot's flows."""
    frappe.has_permission("Chatbot", "read", throw=True)
    slug = (bot_slug or "").strip()
    if not slug:
        return []

    # 1. Identify which actions are referenced in this bot's flows
    flows = frappe.get_all("Chatbot Flow", filters={"bot": slug}, pluck="name")
    used_action_names = set()
    if flows:
        nodes = frappe.get_all(
            "Flow Node",
            filters={"flow": ["in", flows], "node_type": "Call Action"},
            fields=["configuration"],
        )
        for n in nodes:
            if n.configuration:
                try:
                    cfg = json.loads(n.configuration) if isinstance(n.configuration, str) else n.configuration
                    act = cfg.get("action_name")
                    if act:
                        used_action_names.add(act)
                except Exception:
                    pass

    # 2. Get integrations: prioritize integrations explicitly linked to this bot, or unlinked integrations
    filters = {}
    if slug:
        filters = {"chatbot": ["in", [slug, "", None]]}

    integrations = frappe.get_all(
        "Chatbot Integration",
        filters=filters,
        fields=["name", "integration_name", "integration_type", "status", "base_url", "timeout", "description", "chatbot"],
        order_by="creation desc",
    )

    results = []
    for integ in integrations:
        # Check credentials
        cred_name = frappe.db.get_value("Integration Credential", {"integration": integ.name}, "name")
        auth_type = "None"
        has_credentials = False
        api_key_masked = ""
        if cred_name:
            cred_doc = frappe.get_doc("Integration Credential", cred_name)
            auth_type = cred_doc.authentication_type or "Token"
            has_credentials = bool(cred_doc.api_key or cred_doc.get_decrypted_secret())
            if cred_doc.api_key:
                api_key_masked = f"{cred_doc.api_key[:4]}...{cred_doc.api_key[-4:]}" if len(cred_doc.api_key) > 8 else "****"

        # Get linked actions
        actions = frappe.get_all(
            "Integration Action",
            filters={"integration": integ.name},
            fields=["name", "action_name", "method", "operation", "input_schema", "output_mapping"],
        )

        actions_list = []
        is_used_by_bot = False
        for a in actions:
            is_used = (
                (a.action_name in used_action_names)
                or (a.name in used_action_names)
                or any(u.endswith(f"-{a.action_name}") for u in used_action_names)
            )
            if is_used:
                is_used_by_bot = True
            actions_list.append({
                "name": a.name,
                "action_name": a.action_name,
                "method": a.get("method") or "POST",
                "operation": a.operation or "",
                "input_schema": a.input_schema or "{}",
                "output_mapping": a.output_mapping or "{}",
                "is_used": is_used,
            })

        results.append({
            "name": integ.name,
            "integration_name": integ.integration_name,
            "integration_type": integ.integration_type,
            "status": integ.status or "Active",
            "base_url": integ.base_url,
            "timeout": integ.timeout or 15,
            "description": integ.description or "",
            "chatbot": integ.chatbot or "",
            "auth_type": auth_type,
            "has_credentials": has_credentials,
            "api_key_masked": api_key_masked,
            "actions": actions_list,
            "actions_count": len(actions_list),
            "is_used_by_bot": is_used_by_bot,
        })

    return results


@frappe.whitelist()
def save_chatbot_integration(
    integration_name: str,
    integration_type: str = "Frappe REST",
    base_url: str = "",
    status: str = "Active",
    timeout: int = 15,
    auth_type: str = "Token",
    api_key: str = "",
    api_secret: str = "",
    chatbot: Optional[str] = None,
    actions: Optional[Any] = None,
    old_integration_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Create or update a Chatbot Integration with Credentials and Actions.
    Supports renaming an integration and smoothly cascading to linked credentials, actions, and flows.
    """
    frappe.has_permission("Chatbot Integration", "write", throw=True)

    iname = (integration_name or "").strip()
    if not iname:
        frappe.throw(_("Integration Name is required."))

    burl = (base_url or "").strip().rstrip("/")
    if not burl:
        frappe.throw(_("Base URL is required."))

    old_name = (old_integration_name or "").strip()

    # Handle Renaming: If old_integration_name provided and differs, rename the document
    if old_name and old_name != iname and frappe.db.exists("Chatbot Integration", old_name):
        frappe.rename_doc("Chatbot Integration", old_name, iname, force=True)
        # Update and rename linked Integration Credential so encrypted api_secret is preserved
        old_cred = f"CRED-{old_name}"
        new_cred = f"CRED-{iname}"
        if frappe.db.exists("Integration Credential", old_cred) and not frappe.db.exists("Integration Credential", new_cred):
            frappe.rename_doc("Integration Credential", old_cred, new_cred, force=True)
            frappe.db.set_value("Integration Credential", new_cred, "integration", iname)
        else:
            for c in frappe.get_all("Integration Credential", filters={"integration": old_name}, pluck="name"):
                frappe.db.set_value("Integration Credential", c, "integration", iname)

        # Update linked Integration Actions
        for a in frappe.get_all("Integration Action", filters={"integration": old_name}, fields=["name", "action_name"]):
            frappe.db.set_value("Integration Action", a.name, "integration", iname)
            new_action_docname = f"{iname}-{a.action_name}"
            if a.name != new_action_docname and not frappe.db.exists("Integration Action", new_action_docname):
                frappe.rename_doc("Integration Action", a.name, new_action_docname, force=True)

    # 1. Upsert Chatbot Integration
    if frappe.db.exists("Chatbot Integration", iname):
        integ_doc = frappe.get_doc("Chatbot Integration", iname)
        integ_doc.integration_type = integration_type
        integ_doc.base_url = burl
        integ_doc.status = status
        integ_doc.timeout = frappe.utils.cint(timeout) or 15
        if chatbot:
            integ_doc.chatbot = chatbot
        integ_doc.save(ignore_permissions=True)
    else:
        integ_doc = frappe.get_doc({
            "doctype": "Chatbot Integration",
            "integration_name": iname,
            "chatbot": chatbot or "",
            "integration_type": integration_type,
            "base_url": burl,
            "status": status,
            "timeout": frappe.utils.cint(timeout) or 15,
        }).insert(ignore_permissions=True)

    # 2. Upsert Integration Credential if authentication details provided
    cred_name = frappe.db.get_value("Integration Credential", {"integration": iname}, "name")
    if cred_name:
        cred_doc = frappe.get_doc("Integration Credential", cred_name)
        cred_doc.authentication_type = auth_type
        if api_key:
            cred_doc.api_key = api_key.strip()
        if api_secret:
            cred_doc.api_secret = api_secret.strip()
        cred_doc.save(ignore_permissions=True)
    else:
        if auth_type != "None" or api_key or api_secret:
            frappe.get_doc({
                "doctype": "Integration Credential",
                "integration": iname,
                "authentication_type": auth_type or "Token",
                "api_key": api_key.strip() if api_key else "",
                "api_secret": api_secret.strip() if api_secret else "",
            }).insert(ignore_permissions=True)

    # 3. Upsert Actions if provided
    if actions:
        if isinstance(actions, str):
            try:
                actions = json.loads(actions)
            except Exception:
                actions = []
        if isinstance(actions, list):
            for a in actions:
                act_name = (a.get("action_name") or "").strip()
                if not act_name:
                    continue
                full_act_name = f"{iname}-{act_name}"
                op = (a.get("operation") or "").strip()
                method = (a.get("method") or "POST").strip().upper()
                in_schema = a.get("input_schema") or "{}"
                out_map = a.get("output_mapping") or "{}"

                if isinstance(in_schema, dict):
                    in_schema = json.dumps(in_schema)
                if isinstance(out_map, dict):
                    out_map = json.dumps(out_map)

                if frappe.db.exists("Integration Action", full_act_name):
                    act_doc = frappe.get_doc("Integration Action", full_act_name)
                    act_doc.operation = op
                    act_doc.method = method
                    act_doc.input_schema = in_schema
                    act_doc.output_mapping = out_map
                    act_doc.save(ignore_permissions=True)
                else:
                    frappe.get_doc({
                        "doctype": "Integration Action",
                        "integration": iname,
                        "action_name": act_name,
                        "method": method,
                        "operation": op,
                        "input_schema": in_schema,
                        "output_mapping": out_map,
                    }).insert(ignore_permissions=True)

    frappe.db.commit()
    return {
        "status": "success",
        "message": _("Integration '{0}' saved successfully.").format(iname),
        "integration_name": iname,
    }


@frappe.whitelist()
def delete_chatbot_integration(integration_name: str) -> Dict[str, Any]:
    """Delete a Chatbot Integration, its credentials, and linked actions."""
    frappe.has_permission("Chatbot Integration", "delete", throw=True)
    iname = (integration_name or "").strip()
    if not iname or not frappe.db.exists("Chatbot Integration", iname):
        return {"status": "success", "message": _("Integration already removed.")}

    # Delete linked actions
    actions = frappe.get_all("Integration Action", filters={"integration": iname}, pluck="name")
    for a in actions:
        frappe.delete_doc("Integration Action", a, force=1, ignore_permissions=True)

    # Delete linked credentials
    creds = frappe.get_all("Integration Credential", filters={"integration": iname}, pluck="name")
    for c in creds:
        frappe.delete_doc("Integration Credential", c, force=1, ignore_permissions=True)

    # Delete integration doc
    frappe.delete_doc("Chatbot Integration", iname, force=1, ignore_permissions=True)
    frappe.db.commit()

    return {"status": "success", "message": _("Integration '{0}' deleted successfully.").format(iname)}


@frappe.whitelist()
def save_integration_action(
    integration: str,
    action_name: str,
    operation: str,
    method: str = "POST",
    input_schema: Optional[Any] = None,
    output_mapping: Optional[Any] = None,
) -> Dict[str, Any]:
    """Create or update a single Integration Action."""
    frappe.has_permission("Integration Action", "write", throw=True)
    integ = (integration or "").strip()
    aname = (action_name or "").strip()
    op = (operation or "").strip()
    meth = (method or "POST").strip().upper()

    if not integ or not frappe.db.exists("Chatbot Integration", integ):
        frappe.throw(_("Chatbot Integration '{0}' does not exist.").format(integ), exc=frappe.DoesNotExistError)
    if not aname:
        frappe.throw(_("Action Name is required."))
    if not op:
        frappe.throw(_("Endpoint / Operation is required."))

    full_name = f"{integ}-{aname}"
    in_schema_str = input_schema if isinstance(input_schema, str) else json.dumps(input_schema or {})
    out_map_str = output_mapping if isinstance(output_mapping, str) else json.dumps(output_mapping or {})

    # Validate JSON syntax
    try:
        json.loads(in_schema_str)
    except Exception as e:
        frappe.throw(_("Invalid JSON for Input Schema: {0}").format(str(e)))

    try:
        json.loads(out_map_str)
    except Exception as e:
        frappe.throw(_("Invalid JSON for Output Mapping: {0}").format(str(e)))

    if frappe.db.exists("Integration Action", full_name):
        doc = frappe.get_doc("Integration Action", full_name)
        doc.method = meth
        doc.operation = op
        doc.input_schema = in_schema_str
        doc.output_mapping = out_map_str
        doc.save(ignore_permissions=True)
    else:
        frappe.get_doc({
            "doctype": "Integration Action",
            "integration": integ,
            "action_name": aname,
            "method": meth,
            "operation": op,
            "input_schema": in_schema_str,
            "output_mapping": out_map_str,
        }).insert(ignore_permissions=True)

    frappe.db.commit()
    return {"status": "success", "message": _("Action '{0}' saved successfully.").format(aname), "name": full_name}


@frappe.whitelist()
def delete_integration_action(action_name: str) -> Dict[str, Any]:
    """Delete an Integration Action."""
    frappe.has_permission("Integration Action", "delete", throw=True)
    aname = (action_name or "").strip()
    if not aname or not frappe.db.exists("Integration Action", aname):
        return {"status": "success", "message": _("Action already removed.")}

    frappe.delete_doc("Integration Action", aname, force=1, ignore_permissions=True)
    frappe.db.commit()
    return {"status": "success", "message": _("Action '{0}' deleted successfully.").format(aname)}


@frappe.whitelist()
def bulk_delete_integration_actions(action_names: Any) -> Dict[str, Any]:
    """Bulk delete multiple Integration Actions at once."""
    frappe.has_permission("Integration Action", "delete", throw=True)
    names = []
    if isinstance(action_names, str):
        try:
            names = json.loads(action_names)
        except Exception:
            names = [s.strip() for s in action_names.split(",") if s.strip()]
    elif isinstance(action_names, (list, tuple)):
        names = list(action_names)

    deleted_count = 0
    for aname in names:
        aname_clean = str(aname).strip()
        if aname_clean and frappe.db.exists("Integration Action", aname_clean):
            frappe.delete_doc("Integration Action", aname_clean, force=1, ignore_permissions=True)
            deleted_count += 1

    frappe.db.commit()
    return {
        "status": "success",
        "deleted_count": deleted_count,
        "message": _("Successfully deleted {0} action(s).").format(deleted_count),
    }


@frappe.whitelist()
def discover_remote_actions(
    integration_name: str,
    source_type: str = "frappe",
    identifier_or_url: str = "",
) -> Dict[str, Any]:
    """Introspect remote API (Frappe DocType or OpenAPI specification)

    and return candidate action definitions with automatically generated input schemas and output mappings.
    """
    frappe.has_permission("Chatbot Integration", "read", throw=True)
    iname = (integration_name or "").strip()
    if not iname or not frappe.db.exists("Chatbot Integration", iname):
        frappe.throw(_("Chatbot Integration '{0}' does not exist.").format(iname), exc=frappe.DoesNotExistError)

    integ_doc = frappe.get_doc("Chatbot Integration", iname)
    base_url = (integ_doc.base_url or "").rstrip("/")

    # Retrieve credentials if configured
    cred_name = frappe.db.get_value("Integration Credential", {"integration": iname}, "name")
    credentials = {}
    if cred_name:
        cred_doc = frappe.get_doc("Integration Credential", cred_name)
        credentials = {
            "authentication_type": cred_doc.authentication_type,
            "api_key": cred_doc.api_key or "",
            "api_secret": cred_doc.get_decrypted_secret() or "",
        }

    import requests

    headers = {"Accept": "application/json"}
    if credentials.get("authentication_type") == "Token" and credentials.get("api_key") and credentials.get("api_secret"):
        headers["Authorization"] = f"token {credentials['api_key']}:{credentials['api_secret']}"
    elif credentials.get("authentication_type") == "Bearer" and credentials.get("api_key"):
        headers["Authorization"] = f"Bearer {credentials['api_key']}"

    candidates: List[Dict[str, Any]] = []

    # -------------------------------------------------------------
    # 1. Frappe RPC / Python Module Introspection (e.g. society_erp.api)
    # -------------------------------------------------------------
    if source_type.lower() in ("rpc", "python", "module"):
        module_name = (identifier_or_url or "").strip()
        if module_name.endswith(".py"):
            module_name = module_name[:-3]
        if not module_name:
            frappe.throw(_("Please provide a Python module path to introspect (e.g. 'society_erp.api')."))

        import inspect
        import importlib
        import pkgutil
        import ast

        target_module = None
        # Attempt to import locally from bench apps
        try:
            target_module = importlib.import_module(module_name)
        except Exception:
            pass

        # If not imported directly, try fallback variants
        if not target_module and not module_name.endswith(".api"):
            try:
                target_module = importlib.import_module(f"{module_name}.api")
                module_name = f"{module_name}.api"
            except Exception:
                pass

        if not target_module:
            frappe.throw(_("Could not import module '{0}'. Ensure the app is installed in the bench or the module path is correct.").format(module_name))

        # Collect target modules: if target is a package, scan submodules as well
        modules_to_inspect = [(module_name, target_module)]
        if hasattr(target_module, "__path__"):
            for _, sub_name, is_pkg in pkgutil.iter_modules(target_module.__path__):
                if sub_name.startswith("_") or sub_name.endswith("_summary"):
                    continue
                full_sub_name = f"{module_name}.{sub_name}"
                try:
                    sub_mod = importlib.import_module(full_sub_name)
                    modules_to_inspect.append((full_sub_name, sub_mod))
                except Exception:
                    pass

        seen_operations = set()

        for curr_mod_name, curr_mod_obj in modules_to_inspect:
            functions = inspect.getmembers(curr_mod_obj, inspect.isfunction)
            for fn_name, fn_obj in functions:
                if fn_name.startswith("_"):
                    continue

                # Only consider functions defined directly in this module or whitelisted
                if getattr(fn_obj, "__module__", "") != curr_mod_obj.__name__ and (fn_obj not in getattr(frappe, "whitelisted", [])):
                    continue

                # Check if function is whitelisted in Frappe
                is_whitelisted = (
                    fn_obj in getattr(frappe, "whitelisted", [])
                    or getattr(fn_obj, "_whitelisted", False)
                    or getattr(fn_obj, "whitelisted", False)
                )

                # Include if in an API module namespace
                if not is_whitelisted and "api" in curr_mod_name.lower():
                    is_whitelisted = True

                if not is_whitelisted:
                    continue

                operation_path = f"/api/method/{curr_mod_name}.{fn_name}"
                if operation_path in seen_operations:
                    continue
                seen_operations.add(operation_path)

                # Extract parameter signature
                in_props: Dict[str, Any] = {}
                in_required: List[str] = []

                try:
                    sig = inspect.signature(fn_obj)
                    for p_name, p_param in sig.parameters.items():
                        if p_name in ("self", "cls"):
                            continue

                        ann_type = "string"
                        if p_param.annotation in (int, "int"):
                            ann_type = "integer"
                        elif p_param.annotation in (float, "float"):
                            ann_type = "number"
                        elif p_param.annotation in (bool, "bool"):
                            ann_type = "boolean"
                        elif p_param.annotation in (dict, "dict"):
                            ann_type = "object"

                        in_props[p_name] = {
                            "type": ann_type,
                            "title": p_name.replace("_", " ").title(),
                        }

                        # In Frappe, if param has no default or default is None, it is often required by callers
                        if p_param.default == inspect.Parameter.empty:
                            in_required.append(p_name)
                except Exception:
                    pass

                # AST Analysis: Parse function source code to discover frappe.form_dict parameters,
                # returned dictionary payloads, and frappe.response keys
                ast_dict_keys: List[str] = []
                try:
                    fn_src = inspect.getsource(fn_obj)
                    fn_tree = ast.parse(fn_src)

                    # 1. Discover any parameters read via frappe.form_dict.get("param") or frappe.local.form_dict.get("param")
                    for node in ast.walk(fn_tree):
                        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get":
                            if isinstance(node.func.value, ast.Attribute) and node.func.value.attr == "form_dict":
                                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                                    fd_param = node.args[0].value
                                    if fd_param not in in_props and fd_param not in ("cmd", "data"):
                                        in_props[fd_param] = {
                                            "type": "string",
                                            "title": fd_param.replace("_", " ").title(),
                                        }
                                        in_required.append(fd_param)

                    # 2. Discover return dictionary keys
                    return_var_names: List[str] = []
                    for node in ast.walk(fn_tree):
                        if isinstance(node, ast.Return) and node.value:
                            if isinstance(node.value, ast.Name):
                                return_var_names.append(node.value.id)
                            elif isinstance(node.value, ast.Dict):
                                for k in node.value.keys:
                                    if isinstance(k, ast.Constant) and isinstance(k.value, str):
                                        if k.value not in ast_dict_keys:
                                            ast_dict_keys.append(k.value)

                    # Find assignments to returned variable names e.g. resp_payload = {...}
                    if return_var_names:
                        for node in ast.walk(fn_tree):
                            if isinstance(node, ast.Assign):
                                for t in node.targets:
                                    if isinstance(t, ast.Name) and t.id in return_var_names:
                                        if isinstance(node.value, ast.Dict):
                                            for k in node.value.keys:
                                                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                                                    if k.value not in ast_dict_keys:
                                                        ast_dict_keys.append(k.value)

                    # 3. Discover frappe.response["key"] assignments
                    for node in ast.walk(fn_tree):
                        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute) and node.value.attr == "response":
                            if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                                r_key = node.slice.value
                                if r_key not in ("filecontent",) and r_key not in ast_dict_keys:
                                    ast_dict_keys.append(r_key)
                except Exception:
                    pass

                # Extract summary/description from docstring
                docstring = inspect.getdoc(fn_obj) or ""
                doc_lines = [l.strip() for l in docstring.split("\n") if l.strip()]
                sub_label = curr_mod_name.split(".")[-1] if "." in curr_mod_name else curr_mod_name
                summary = doc_lines[0] if doc_lines else f"[{sub_label}] Execute {fn_name}"

                # Build Output Mapping from discovered keys
                out_map: Dict[str, str] = {}
                if ast_dict_keys:
                    for k in ast_dict_keys:
                        if k not in ("message", "filecontent"):
                            out_map[k] = k
                    if not out_map and "message" in ast_dict_keys:
                        out_map["message"] = "message"
                else:
                    if "dues" in fn_name.lower() or "maintenance" in fn_name.lower():
                        out_map = {
                            "owner_name": "owner_name",
                            "flat_details": "flat_details",
                            "tenant_name": "tenant_name",
                            "outstanding_amount": "outstanding_amount",
                        }
                    elif "user" in fn_name.lower() or "customer" in fn_name.lower():
                        out_map = {"name": "name", "email": "email", "status": "status"}
                    else:
                        out_map = {"message": "message", "status": "status"}

                candidates.append({
                    "action_name": fn_name,
                    "method": "POST",
                    "operation": operation_path,
                    "description": summary,
                    "input_schema": {
                        "type": "object",
                        "required": in_required,
                        "properties": in_props,
                    },
                    "output_mapping": out_map,
                })

    # -------------------------------------------------------------
    # 2. Frappe REST DocType Introspection
    # -------------------------------------------------------------
    elif source_type.lower() == "frappe" or (source_type.lower() == "doctype" and integ_doc.integration_type == "Frappe REST"):
        doctype = (identifier_or_url or "").strip()
        if not doctype:
            frappe.throw(_("Please provide a DocType name to introspect (e.g. 'Customer', 'Sales Order', 'Item')."))

        # Try fetching DocType schema via Frappe API
        # First attempt: desk form load method frappe.desk.form.load.getdoctype
        meta_url = f"{base_url}/api/method/frappe.desk.form.load.getdoctype?doctype={doctype}"
        fields_data = []
        doc_title = doctype
        try:
            resp = requests.get(meta_url, headers=headers, timeout=integ_doc.timeout or 15)
            if resp.status_code == 200:
                body = resp.json().get("docs", [])
                if body and len(body) > 0:
                    dt_meta = body[0]
                    fields_data = dt_meta.get("fields", [])
                    doc_title = dt_meta.get("name") or doctype
            else:
                # Second attempt: sample an existing record from /api/resource/{doctype}?limit=1
                sample_url = f"{base_url}/api/resource/{doctype}?limit=1"
                sample_resp = requests.get(sample_url, headers=headers, timeout=integ_doc.timeout or 15)
                if sample_resp.status_code == 200:
                    data_list = sample_resp.json().get("data", [])
                    if data_list and isinstance(data_list, list) and len(data_list) > 0:
                        first_docname = data_list[0].get("name")
                        if first_docname:
                            detail_url = f"{base_url}/api/resource/{doctype}/{first_docname}"
                            detail_resp = requests.get(detail_url, headers=headers, timeout=integ_doc.timeout or 15)
                            if detail_resp.status_code == 200:
                                rec_data = detail_resp.json().get("data", {})
                                for k, v in rec_data.items():
                                    if k in ("doctype", "docstatus", "idx"):
                                        continue
                                    fields_data.append({
                                        "fieldname": k,
                                        "label": k.replace("_", " ").title(),
                                        "fieldtype": "Int" if isinstance(v, int) else ("Float" if isinstance(v, float) else "Data"),
                                        "reqd": 0,
                                    })
                elif sample_resp.status_code in (401, 403):
                    # Check if local frappe site knows about this doctype
                    if frappe.db.exists("DocType", doctype):
                        local_meta = frappe.get_meta(doctype)
                        for f in local_meta.fields:
                            fields_data.append({
                                "fieldname": f.fieldname,
                                "label": f.label or f.fieldname,
                                "fieldtype": f.fieldtype,
                                "reqd": f.reqd,
                            })
                    else:
                        frappe.throw(_("Authentication failed connecting to {0} (HTTP {1})").format(base_url, sample_resp.status_code))
        except requests.RequestException as e:
            frappe.throw(_("Failed to connect to remote server: {0}").format(str(e)))

        # Build schema from discovered fields
        doc_slug = re.sub(r"[^a-zA-Z0-9_]+", "_", doctype.lower()).strip("_")
        props: Dict[str, Any] = {}
        required_fields: List[str] = []
        out_map: Dict[str, str] = {"name": "name"}

        for f in fields_data:
            fname = f.get("fieldname")
            ftype = f.get("fieldtype")
            if not fname or ftype in ("Section Break", "Column Break", "Tab Break", "HTML", "Button"):
                continue

            json_type = "string"
            if ftype in ("Int", "Check"):
                json_type = "integer"
            elif ftype in ("Float", "Currency", "Percent"):
                json_type = "number"

            props[fname] = {
                "type": json_type,
                "title": f.get("label") or fname,
            }
            if f.get("reqd"):
                required_fields.append(fname)
            # Add top fields to default output mapping
            if len(out_map) < 10 and fname not in out_map:
                out_map[fname] = fname

        # If no fields could be introspected (e.g. empty doctype or permissions), provide clean defaults
        if not props:
            props = {"name": {"type": "string", "title": "Document Name / ID"}}
            required_fields = ["name"]
            out_map = {"name": "name", "owner": "owner", "modified": "modified"}

        # Candidate 1: Get Single Document
        candidates.append({
            "action_name": f"get_{doc_slug}",
            "method": "GET",
            "operation": f"/api/resource/{doctype}/{{name}}",
            "description": f"Fetch a single {doctype} by document name/ID",
            "input_schema": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string", "title": "Document Name / ID"}
                }
            },
            "output_mapping": out_map,
        })

        # Candidate 2: List Documents
        candidates.append({
            "action_name": f"list_{doc_slug}",
            "method": "GET",
            "operation": f"/api/resource/{doctype}",
            "description": f"List {doctype} records with optional filtering",
            "input_schema": {
                "type": "object",
                "properties": {
                    "limit_page_length": {"type": "integer", "default": 20, "title": "Limit"},
                }
            },
            "output_mapping": {"data": "data"},
        })

        # Candidate 3: Create Document
        candidates.append({
            "action_name": f"create_{doc_slug}",
            "method": "POST",
            "operation": f"/api/resource/{doctype}",
            "description": f"Create a new {doctype} record",
            "input_schema": {
                "type": "object",
                "required": required_fields,
                "properties": props,
            },
            "output_mapping": {"name": "name"},
        })

    # -------------------------------------------------------------
    # 2. OpenAPI / Swagger 2.0 / 3.0 Introspection
    # -------------------------------------------------------------
    else:
        spec_url = (identifier_or_url or "").strip()
        if not spec_url:
            spec_url = f"{base_url}/openapi.json"

        # If relative URL, prefix with base_url
        if not (spec_url.startswith("http://") or spec_url.startswith("https://")):
            spec_url = f"{base_url}/{spec_url.lstrip('/')}"

        try:
            resp = requests.get(spec_url, headers=headers, timeout=integ_doc.timeout or 15)
            if resp.status_code != 200:
                frappe.throw(_("Could not fetch OpenAPI spec from {0} (HTTP {1})").format(spec_url, resp.status_code))
            spec = resp.json()
        except requests.RequestException as e:
            frappe.throw(_("Failed to fetch OpenAPI specification: {0}").format(str(e)))

        paths = spec.get("paths", {})
        for path_url, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
            for method, op_data in path_item.items():
                if method.lower() not in ("get", "post", "put", "delete", "patch") or not isinstance(op_data, dict):
                    continue

                method_upper = method.upper()
                op_id = op_data.get("operationId")
                summary = op_data.get("summary") or op_data.get("description") or f"{method_upper} {path_url}"

                if not op_id:
                    # Synthesize action name from method and path
                    clean_path = re.sub(r"[{}\-./]+", "_", path_url).strip("_")
                    op_id = f"{method.lower()}_{clean_path}"

                # Extract parameters
                params = op_data.get("parameters", [])
                in_props: Dict[str, Any] = {}
                in_required: List[str] = []

                for p in params:
                    pname = p.get("name")
                    if not pname:
                        continue
                    schema = p.get("schema", {})
                    ptype = schema.get("type") or p.get("type", "string")
                    in_props[pname] = {
                        "type": ptype,
                        "description": p.get("description") or "",
                    }
                    if p.get("required"):
                        in_required.append(pname)

                # Extract request body for POST/PUT/PATCH
                req_body = op_data.get("requestBody", {})
                if req_body:
                    content = req_body.get("content", {})
                    json_schema = content.get("application/json", {}).get("schema", {})
                    body_props = json_schema.get("properties", {})
                    for bp_name, bp_data in body_props.items():
                        if bp_name not in in_props:
                            in_props[bp_name] = {
                                "type": bp_data.get("type", "string"),
                                "description": bp_data.get("description") or "",
                            }
                    for req_field in json_schema.get("required", []):
                        if req_field not in in_required:
                            in_required.append(req_field)

                # Extract response schema
                out_map: Dict[str, str] = {}
                responses = op_data.get("responses", {})
                resp_200 = responses.get("200") or responses.get(200) or responses.get("201") or responses.get(201) or {}
                if isinstance(resp_200, dict):
                    resp_schema = resp_200.get("content", {}).get("application/json", {}).get("schema", {})
                    if not resp_schema and "schema" in resp_200:
                        resp_schema = resp_200["schema"]
                    resp_props = resp_schema.get("properties", {})
                    for r_name in resp_props.keys():
                        if len(out_map) < 8:
                            out_map[r_name] = r_name

                if not out_map:
                    out_map = {"data": "data", "status": "status"}

                candidates.append({
                    "action_name": op_id,
                    "method": method_upper,
                    "operation": path_url,
                    "description": summary,
                    "input_schema": {
                        "type": "object",
                        "required": in_required,
                        "properties": in_props,
                    },
                    "output_mapping": out_map,
                })

    return {
        "status": "success",
        "integration": iname,
        "source_type": source_type,
        "candidates_count": len(candidates),
        "candidates": candidates,
    }


@frappe.whitelist()
def import_discovered_actions(
    integration_name: str,
    actions: Any,
) -> Dict[str, Any]:
    """Bulk import selected discovered actions into Integration Action DocTypes."""
    frappe.has_permission("Integration Action", "write", throw=True)
    iname = (integration_name or "").strip()
    if not iname or not frappe.db.exists("Chatbot Integration", iname):
        frappe.throw(_("Chatbot Integration '{0}' does not exist.").format(iname), exc=frappe.DoesNotExistError)

    if isinstance(actions, str):
        try:
            actions = json.loads(actions)
        except Exception as e:
            frappe.throw(_("Invalid JSON for actions: {0}").format(str(e)))

    if not isinstance(actions, list) or len(actions) == 0:
        frappe.throw(_("No actions provided to import."))

    imported_names: List[str] = []
    for a in actions:
        aname = (a.get("action_name") or "").strip()
        if not aname:
            continue
        full_act_name = f"{iname}-{aname}"
        op = (a.get("operation") or "").strip()
        method = (a.get("method") or "POST").strip().upper()
        in_schema = a.get("input_schema") or "{}"
        out_map = a.get("output_mapping") or "{}"

        in_schema_str = in_schema if isinstance(in_schema, str) else json.dumps(in_schema)
        out_map_str = out_map if isinstance(out_map, str) else json.dumps(out_map)

        if frappe.db.exists("Integration Action", full_act_name):
            act_doc = frappe.get_doc("Integration Action", full_act_name)
            act_doc.method = method
            act_doc.operation = op
            act_doc.input_schema = in_schema_str
            act_doc.output_mapping = out_map_str
            act_doc.save(ignore_permissions=True)
        else:
            frappe.get_doc({
                "doctype": "Integration Action",
                "integration": iname,
                "action_name": aname,
                "method": method,
                "operation": op,
                "input_schema": in_schema_str,
                "output_mapping": out_map_str,
            }).insert(ignore_permissions=True)

        imported_names.append(aname)

    frappe.db.commit()
    return {
        "status": "success",
        "message": _("Successfully imported {0} action(s).").format(len(imported_names)),
        "imported_actions": imported_names,
    }



