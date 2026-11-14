"""Bot Configuration Export & Import Utility.

Provides full-package serialization and deserialization of complete Chatbots:
- Bot definition and settings
- Integrations, Integration Credentials, and Integration Actions
- All Chatbot Flows with complete node graphs, transitions, and variables
- Omnichannel Bot Channels (Telegram, WhatsApp, Web Widget) and Bot Deployments

Decoupled, portable, and cross-site compatible.
"""

import json
from typing import Any, Dict, List, Optional, Union
import frappe
from frappe import _
from frappe.utils.password import get_decrypted_password
from universal_chatbot.flow.export_import import export_flow_json, import_flow_json

BOT_PACKAGE_SCHEMA_VERSION = "1.0"


@frappe.whitelist()
def export_bot_package(
    bot_name: str,
    include_credentials: Union[bool, int, str] = False,
) -> Dict[str, Any]:
    """Serialize an entire Chatbot package into a portable JSON document.

    Args:
        bot_name: Identifier / slug of the Chatbot.
        include_credentials: If True, exports decrypted secrets (tokens, API secrets).
                             Defaults to False for safe public sharing.

    Returns:
        Structured package containing bot metadata, integrations, flows, channels, deployments.
    """
    frappe.has_permission("Chatbot", "read", throw=True)

    bot_name = (bot_name or "").strip()
    if not bot_name:
        frappe.throw(_("Missing required parameter 'bot_name'."), exc=frappe.MandatoryError)

    if not frappe.db.exists("Chatbot", bot_name):
        frappe.throw(_("Chatbot '{0}' not found.").format(bot_name), exc=frappe.DoesNotExistError)

    include_creds = frappe.utils.cint(include_credentials) if not isinstance(include_credentials, bool) else (1 if include_credentials else 0)

    # 1. Bot Metadata
    bot_doc = frappe.get_doc("Chatbot", bot_name)
    bot_dict = {
        "bot_name": bot_doc.bot_name,
        "title": bot_doc.title,
        "status": bot_doc.status or "Draft",
        "is_published": bot_doc.is_published or 0,
        "avatar": bot_doc.avatar or None,
        "default_language": bot_doc.default_language or "en",
        "starter_template": bot_doc.starter_template or "Blank Canvas",
        "greeting_message": bot_doc.greeting_message or "",
        "fallback_message": bot_doc.fallback_message or "",
        "description": bot_doc.description or "",
    }

    # 2. Integrations, Actions, and Credentials
    integrations_payload = []
    integration_docs = frappe.get_all(
        "Chatbot Integration",
        filters={"chatbot": bot_name},
        fields=["name", "integration_name", "integration_type", "status", "base_url", "timeout", "description"],
    )

    for integ in integration_docs:
        integ_data = {
            "integration_name": integ.integration_name,
            "integration_type": integ.integration_type,
            "status": integ.status or "Active",
            "base_url": integ.base_url or "",
            "timeout": integ.timeout or 15,
            "description": integ.description or "",
            "actions": [],
            "credentials": [],
        }

        # Actions
        actions = frappe.get_all(
            "Integration Action",
            filters={"integration": integ.name},
            fields=["action_name", "method", "operation", "input_schema", "output_mapping"],
        )
        for act in actions:
            in_schema = {}
            out_mapping = {}
            if act.input_schema:
                try:
                    in_schema = json.loads(act.input_schema) if isinstance(act.input_schema, str) else act.input_schema
                except Exception:
                    in_schema = {}
            if act.output_mapping:
                try:
                    out_mapping = json.loads(act.output_mapping) if isinstance(act.output_mapping, str) else act.output_mapping
                except Exception:
                    out_mapping = {}

            integ_data["actions"].append({
                "action_name": act.action_name,
                "method": act.method or "POST",
                "operation": act.operation or "",
                "input_schema": in_schema,
                "output_mapping": out_mapping,
            })

        # Credentials
        creds = frappe.get_all(
            "Integration Credential",
            filters={"integration": integ.name},
            fields=["name", "authentication_type", "api_key"],
        )
        for cred in creds:
            cred_dict = {
                "authentication_type": cred.authentication_type or "Token",
                "api_key": cred.api_key or "",
            }
            if include_creds:
                try:
                    cred_dict["api_secret"] = get_decrypted_password("Integration Credential", cred.name, "api_secret")
                except Exception:
                    cred_dict["api_secret"] = ""
            integ_data["credentials"].append(cred_dict)

        integrations_payload.append(integ_data)

    # 3. Flows (All conversation flows for this bot)
    flows_payload = []
    flow_names = frappe.get_all(
        "Chatbot Flow",
        filters={"bot": bot_name},
        pluck="name",
    )
    for fn in flow_names:
        flow_export = export_flow_json(fn)
        flows_payload.append(flow_export)

    # 4. Omnichannel Channels and Deployments
    deployments_payload = []
    dep_docs = frappe.get_all(
        "Bot Deployment",
        filters={"chatbot": bot_name},
        fields=[
            "name", "deployment_name", "channel", "bot_version", "status",
            "deployment_key", "auth_mode", "rate_limit_per_minute",
            "allowed_domains", "theme_config", "custom_css",
        ],
    )

    for dep in dep_docs:
        dep_dict = {
            "deployment_name": dep.deployment_name,
            "channel_ref": dep.channel,
            "status": dep.status or "Active",
            "deployment_key": dep.deployment_key,
            "auth_mode": dep.auth_mode or "Anonymous",
            "rate_limit_per_minute": dep.rate_limit_per_minute or 60,
            "allowed_domains": dep.allowed_domains or "*",
            "theme_config": dep.theme_config or None,
            "custom_css": dep.custom_css or None,
        }

        # Resolve associated Bot Channel
        channel_data = None
        if dep.channel and frappe.db.exists("Bot Channel", dep.channel):
            ch_doc = frappe.get_doc("Bot Channel", dep.channel)
            channel_data = {
                "channel_name": ch_doc.channel_name,
                "channel_type": ch_doc.channel_type,
                "is_enabled": ch_doc.is_enabled or 0,
                "description": ch_doc.description or "",
                "whatsapp_phone_number_id": ch_doc.whatsapp_phone_number_id or "",
                "whatsapp_verify_token": ch_doc.whatsapp_verify_token or "",
                "telegram_webhook_secret": ch_doc.telegram_webhook_secret or "",
                "config": ch_doc.config or None,
            }
            if include_creds:
                if ch_doc.whatsapp_access_token:
                    try:
                        channel_data["whatsapp_access_token"] = get_decrypted_password("Bot Channel", ch_doc.name, "whatsapp_access_token")
                    except Exception:
                        channel_data["whatsapp_access_token"] = ""
                if ch_doc.telegram_bot_token:
                    try:
                        channel_data["telegram_bot_token"] = get_decrypted_password("Bot Channel", ch_doc.name, "telegram_bot_token")
                    except Exception:
                        channel_data["telegram_bot_token"] = ""

        dep_dict["channel_details"] = channel_data
        deployments_payload.append(dep_dict)

    # 5. Determine primary flow slug relative to bot
    primary_flow_slug = ""
    if bot_doc.primary_flow:
        primary_flow_slug = bot_doc.primary_flow
        if primary_flow_slug.startswith(f"{bot_name}-"):
            primary_flow_slug = primary_flow_slug[len(bot_name) + 1:]
    bot_dict["primary_flow"] = primary_flow_slug

    package = {
        "$schema": "https://universal-chatbot.frappe.cloud/schemas/bot.v1.json",
        "schema_version": BOT_PACKAGE_SCHEMA_VERSION,
        "exported_at": frappe.utils.now(),
        "credentials_included": bool(include_creds),
        "bot": bot_dict,
        "integrations": integrations_payload,
        "flows": flows_payload,
        "deployments": deployments_payload,
    }

    return package


@frappe.whitelist()
def import_bot_package(
    package_json: Union[str, Dict[str, Any]],
    target_bot_slug: Optional[str] = None,
    overwrite: Union[bool, int, str] = False,
) -> Dict[str, Any]:
    """Import and provision a complete Chatbot with integrations, flows, channels, and deployments.

    Args:
        package_json: JSON string or dictionary representing the exported bot package.
        target_bot_slug: Optional slug for the bot. If omitted, uses bot.bot_name from payload.
        overwrite: If True, updates existing doc records with the same name.

    Returns:
        Summary dict containing status, counts of provisioned entities, and target bot name.
    """
    frappe.has_permission("Chatbot", "write", throw=True)

    if isinstance(package_json, str):
        try:
            payload = json.loads(package_json)
        except Exception as e:
            frappe.throw(_("Invalid JSON format for bot package import: {0}").format(str(e)))
    elif isinstance(package_json, dict):
        payload = package_json
    else:
        frappe.throw(_("package_json must be a JSON string or dictionary."))

    if not isinstance(payload, dict):
        frappe.throw(_("Bot package payload must be a JSON object."))

    bot_meta = payload.get("bot") or {}
    slug = (target_bot_slug or bot_meta.get("bot_name") or "").strip()
    if not slug:
        slug = f"imported_bot_{frappe.generate_hash(length=6).lower()}"

    is_overwrite = frappe.utils.cint(overwrite) if not isinstance(overwrite, bool) else (1 if overwrite else 0)

    bot_exists = frappe.db.exists("Chatbot", slug)
    if bot_exists and not is_overwrite:
        frappe.throw(
            _("Chatbot '{0}' already exists. Pass overwrite=True to update it.").format(slug),
            exc=frappe.DuplicateEntryError,
        )

    # 1. Provision / Update Chatbot Master
    if not bot_exists:
        bot_doc = frappe.get_doc({
            "doctype": "Chatbot",
            "bot_name": slug,
            "title": bot_meta.get("title") or slug.replace("_", " ").title(),
            "status": bot_meta.get("status") or "Active",
            "is_published": bot_meta.get("is_published", 1),
            "avatar": bot_meta.get("avatar") or None,
            "default_language": bot_meta.get("default_language") or "en",
            "starter_template": bot_meta.get("starter_template") or "ERP & API Lookup",
            "greeting_message": bot_meta.get("greeting_message") or "Hello!",
            "fallback_message": bot_meta.get("fallback_message") or "I did not understand.",
            "description": bot_meta.get("description") or f"Imported bot {slug}",
        }).insert(ignore_permissions=True)
    else:
        bot_doc = frappe.get_doc("Chatbot", slug)
        if bot_meta.get("title"):
            bot_doc.title = bot_meta.get("title")
        if bot_meta.get("status"):
            bot_doc.status = bot_meta.get("status")
        if "is_published" in bot_meta:
            bot_doc.is_published = bot_meta.get("is_published")
        if bot_meta.get("default_language"):
            bot_doc.default_language = bot_meta.get("default_language")
        if bot_meta.get("starter_template"):
            bot_doc.starter_template = bot_meta.get("starter_template")
        if bot_meta.get("greeting_message"):
            bot_doc.greeting_message = bot_meta.get("greeting_message")
        if bot_meta.get("fallback_message"):
            bot_doc.fallback_message = bot_meta.get("fallback_message")
        if bot_meta.get("description"):
            bot_doc.description = bot_meta.get("description")
        bot_doc.save(ignore_permissions=True)

    # 2. Provision Integrations, Actions, and Credentials
    integrations_count = 0
    actions_count = 0
    integrations_list = payload.get("integrations") or []
    for integ_data in integrations_list:
        raw_iname = integ_data.get("integration_name") or "default_integ"
        # If importing into a new/different bot slug, ensure the integration name is namespaced to avoid collision
        if slug != (bot_meta.get("bot_name") or ""):
            integ_name = f"{slug}_{raw_iname}"
        else:
            integ_name = raw_iname

        integ_exists = frappe.db.exists("Chatbot Integration", integ_name)
        if not integ_exists:
            integ_doc = frappe.get_doc({
                "doctype": "Chatbot Integration",
                "integration_name": integ_name,
                "chatbot": slug,
                "integration_type": integ_data.get("integration_type") or "Frappe REST",
                "status": integ_data.get("status") or "Active",
                "base_url": integ_data.get("base_url") or "",
                "timeout": integ_data.get("timeout") or 15,
                "description": integ_data.get("description") or "",
            }).insert(ignore_permissions=True)
        else:
            integ_doc = frappe.get_doc("Chatbot Integration", integ_name)
            integ_doc.chatbot = slug
            if integ_data.get("base_url"):
                integ_doc.base_url = integ_data.get("base_url")
            if integ_data.get("timeout"):
                integ_doc.timeout = integ_data.get("timeout")
            integ_doc.save(ignore_permissions=True)

        integrations_count += 1

        # Actions
        for act in integ_data.get("actions", []):
            act_name_raw = act.get("action_name")
            act_docname = f"{integ_name}-{act_name_raw}"
            in_schema_str = json.dumps(act.get("input_schema") or {})
            out_mapping_str = json.dumps(act.get("output_mapping") or {})

            if not frappe.db.exists("Integration Action", act_docname):
                frappe.get_doc({
                    "doctype": "Integration Action",
                    "action_name": act_name_raw,
                    "integration": integ_name,
                    "method": act.get("method") or "POST",
                    "operation": act.get("operation") or "",
                    "input_schema": in_schema_str,
                    "output_mapping": out_mapping_str,
                }).insert(ignore_permissions=True)
            else:
                act_doc = frappe.get_doc("Integration Action", act_docname)
                act_doc.method = act.get("method") or "POST"
                act_doc.operation = act.get("operation") or ""
                act_doc.input_schema = in_schema_str
                act_doc.output_mapping = out_mapping_str
                act_doc.save(ignore_permissions=True)

            actions_count += 1

        # Credentials
        for cred in integ_data.get("credentials", []):
            cred_name = f"CRED-{integ_name}"
            if not frappe.db.exists("Integration Credential", cred_name):
                c_doc = frappe.get_doc({
                    "doctype": "Integration Credential",
                    "integration": integ_name,
                    "authentication_type": cred.get("authentication_type") or "Token",
                    "api_key": cred.get("api_key") or "",
                })
                if cred.get("api_secret"):
                    c_doc.api_secret = cred.get("api_secret")
                c_doc.insert(ignore_permissions=True)
            else:
                c_doc = frappe.get_doc("Integration Credential", cred_name)
                if cred.get("api_key"):
                    c_doc.api_key = cred.get("api_key")
                if cred.get("api_secret"):
                    c_doc.api_secret = cred.get("api_secret")
                c_doc.save(ignore_permissions=True)

    # 3. Provision Flows
    flows_count = 0
    flows_list = payload.get("flows") or []
    for f in flows_list:
        import_flow_json(f, bot_slug=slug, overwrite=True)
        flows_count += 1

    # Link primary flow if present
    primary_flow_slug = bot_meta.get("primary_flow")
    if primary_flow_slug:
        candidate_primary = f"{slug}-{primary_flow_slug}"
        if frappe.db.exists("Chatbot Flow", candidate_primary):
            bot_doc.primary_flow = candidate_primary
        elif frappe.db.exists("Chatbot Flow", primary_flow_slug):
            bot_doc.primary_flow = primary_flow_slug
        bot_doc.save(ignore_permissions=True)

    # 4. Provision Channels & Omnichannel Deployments
    deployments_count = 0
    channels_count = 0
    deployments_list = payload.get("deployments") or []
    for dep_data in deployments_list:
        ch_details = dep_data.get("channel_details") or {}
        raw_ch_name = ch_details.get("channel_name") or f"{slug} Channel {frappe.generate_hash(length=4)}"
        # Ensure channel name is unique/namespaced to this bot
        if slug != (bot_meta.get("bot_name") or "") and not raw_ch_name.startswith(slug):
            final_ch_name = f"{slug} {raw_ch_name}"
        else:
            final_ch_name = raw_ch_name

        raw_dep_name = dep_data.get("deployment_name") or f"{slug} Deployment {frappe.generate_hash(length=4)}"
        if slug != (bot_meta.get("bot_name") or "") and not raw_dep_name.startswith(slug):
            final_dep_name = f"{slug} {raw_dep_name}"
        else:
            final_dep_name = raw_dep_name
        dep_docname = f"DEP-{slug}-{final_dep_name}"

        # Step 4a: Create or update Bot Channel (without deployment link initially to pass validation)
        if ch_details:
            if not frappe.db.exists("Bot Channel", final_ch_name):
                ch_doc = frappe.get_doc({
                    "doctype": "Bot Channel",
                    "channel_name": final_ch_name,
                    "channel_type": ch_details.get("channel_type") or "Web Widget",
                    "is_enabled": ch_details.get("is_enabled", 1),
                    "chatbot": slug,
                    "description": ch_details.get("description") or "",
                    "whatsapp_phone_number_id": ch_details.get("whatsapp_phone_number_id") or "",
                    "whatsapp_verify_token": ch_details.get("whatsapp_verify_token") or "",
                    "telegram_webhook_secret": ch_details.get("telegram_webhook_secret") or "",
                    "config": ch_details.get("config") or None,
                })
                if ch_details.get("whatsapp_access_token"):
                    ch_doc.whatsapp_access_token = ch_details.get("whatsapp_access_token")
                if ch_details.get("telegram_bot_token"):
                    ch_doc.telegram_bot_token = ch_details.get("telegram_bot_token")
                ch_doc.insert(ignore_permissions=True, ignore_links=True)
            else:
                ch_doc = frappe.get_doc("Bot Channel", final_ch_name)
                ch_doc.chatbot = slug
                ch_doc.is_enabled = ch_details.get("is_enabled", 1)
                if ch_details.get("whatsapp_phone_number_id"):
                    ch_doc.whatsapp_phone_number_id = ch_details.get("whatsapp_phone_number_id")
                if ch_details.get("whatsapp_verify_token"):
                    ch_doc.whatsapp_verify_token = ch_details.get("whatsapp_verify_token")
                if ch_details.get("telegram_webhook_secret"):
                    ch_doc.telegram_webhook_secret = ch_details.get("telegram_webhook_secret")
                if ch_details.get("whatsapp_access_token"):
                    ch_doc.whatsapp_access_token = ch_details.get("whatsapp_access_token")
                if ch_details.get("telegram_bot_token"):
                    ch_doc.telegram_bot_token = ch_details.get("telegram_bot_token")
                ch_doc.save(ignore_permissions=True)
            channels_count += 1

        # Step 4b: Create or update Bot Deployment linking to the channel
        raw_key = dep_data.get("deployment_key") or ""
        # If target bot slug is different, generate fresh unique deployment_key so it doesn't conflict
        if slug != (bot_meta.get("bot_name") or "") or not raw_key:
            prefix = "tg" if "telegram" in raw_dep_name.lower() else ("wa" if "whatsapp" in raw_dep_name.lower() else "web")
            dep_key = f"{prefix}_{frappe.generate_hash(length=12)}"
        else:
            dep_key = raw_key

        if not frappe.db.exists("Bot Deployment", dep_docname):
            frappe.get_doc({
                "doctype": "Bot Deployment",
                "deployment_name": final_dep_name,
                "chatbot": slug,
                "channel": final_ch_name if ch_details else (dep_data.get("channel_ref") or None),
                "status": dep_data.get("status") or "Active",
                "deployment_key": dep_key,
                "auth_mode": dep_data.get("auth_mode") or "Anonymous",
                "rate_limit_per_minute": dep_data.get("rate_limit_per_minute") or 60,
                "allowed_domains": dep_data.get("allowed_domains") or "*",
                "theme_config": dep_data.get("theme_config") or None,
                "custom_css": dep_data.get("custom_css") or None,
            }).insert(ignore_permissions=True)
        else:
            dep_doc = frappe.get_doc("Bot Deployment", dep_docname)
            dep_doc.chatbot = slug
            if ch_details:
                dep_doc.channel = final_ch_name
            dep_doc.status = dep_data.get("status") or "Active"
            dep_doc.rate_limit_per_minute = dep_data.get("rate_limit_per_minute") or 60
            dep_doc.allowed_domains = dep_data.get("allowed_domains") or "*"
            dep_doc.save(ignore_permissions=True)
        deployments_count += 1

        # Step 4c: Link channel back to deployment
        if ch_details and frappe.db.exists("Bot Channel", final_ch_name):
            frappe.db.set_value("Bot Channel", final_ch_name, "deployment", dep_docname)

    return {
        "status": "success",
        "bot_name": slug,
        "integrations_count": integrations_count,
        "actions_count": actions_count,
        "flows_count": flows_count,
        "channels_count": channels_count,
        "deployments_count": deployments_count,
        "message": _("Bot '{0}' fully provisioned with {1} integration(s), {2} action(s), {3} flow(s), and {4} deployment(s).").format(
            slug, integrations_count, actions_count, flows_count, deployments_count
        ),
    }
