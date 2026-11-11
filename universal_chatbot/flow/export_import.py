"""Flow Configuration Export & Import Utility.

Provides serialization and deserialization of complete Chatbot Flows
(metadata, nodes, transitions, and variables) into and out of standard JSON schemas.
Strictly decoupled: no direct UI logic, fully testable.
"""

import json
from typing import Any, Dict, Optional, Union
import frappe
from frappe import _
from universal_chatbot.api.v1.flow_designer import (
    load_visual_flow,
    save_visual_flow,
    validate_flow_structure,
)


EXPORT_SCHEMA_VERSION = "1.0"


@frappe.whitelist()
def export_flow_json(flow_name: str) -> Dict[str, Any]:
    """Serialize a complete Chatbot Flow into a clean, downloadable JSON schema.

    Contains:
    - schema_version
    - exported_at
    - metadata (flow_name, bot, title, description, version, status)
    - nodes (node_id, node_type, configuration, x, y)
    - transitions (source_node, target_node, condition)
    - variables (variable_name, data_type, default_value)
    """
    frappe.has_permission("Chatbot Flow", "read", throw=True)

    flow_name = (flow_name or "").strip()
    if not flow_name:
        frappe.throw(_("Missing required parameter 'flow_name'."), exc=frappe.MandatoryError)

    if not frappe.db.exists("Chatbot Flow", flow_name):
        frappe.throw(_("Chatbot Flow '{0}' not found.").format(flow_name), exc=frappe.DoesNotExistError)

    flow_doc = frappe.get_doc("Chatbot Flow", flow_name)
    raw_graph = load_visual_flow(flow_name)

    # Clean nodes (omit internal docnames)
    clean_nodes = []
    for n in raw_graph.get("nodes", []):
        cfg = dict(n.get("configuration") or {})
        # Remove UI duplicates if already extracted
        clean_nodes.append({
            "node_id": n.get("node_id"),
            "node_type": n.get("node_type"),
            "configuration": cfg,
            "x": n.get("x", cfg.get("ui_x", 100)),
            "y": n.get("y", cfg.get("ui_y", 100)),
        })

    # Clean transitions (omit internal docnames)
    clean_transitions = []
    for t in raw_graph.get("transitions", []):
        clean_transitions.append({
            "source_node": t.get("source_node"),
            "target_node": t.get("target_node"),
            "condition": t.get("condition") or "",
        })

    # Clean variables (omit internal docnames)
    clean_variables = []
    for v in raw_graph.get("variables", []):
        clean_variables.append({
            "variable_name": v.get("variable_name"),
            "data_type": v.get("data_type", "String"),
            "default_value": v.get("default_value", ""),
        })

    payload = {
        "$schema": "https://universal-chatbot.frappe.cloud/schemas/flow.v1.json",
        "schema_version": EXPORT_SCHEMA_VERSION,
        "exported_at": frappe.utils.now(),
        "metadata": {
            "flow_name": flow_doc.flow_name,
            "title": flow_doc.flow_name.replace("_", " ").title(),
            "description": flow_doc.description or "",
            "bot": flow_doc.bot,
            "version": flow_doc.version or "1.0.0",
            "status": flow_doc.status or "Draft",
        },
        "nodes": clean_nodes,
        "transitions": clean_transitions,
        "variables": clean_variables,
    }

    return payload


@frappe.whitelist()
def import_flow_json(
    flow_json: Union[str, Dict[str, Any]],
    bot_slug: Optional[str] = None,
    overwrite: Union[bool, int, str] = False,
) -> Dict[str, Any]:
    """Validate and provision a Chatbot Flow and its nodes/transitions/variables from a JSON payload.

    Args:
        flow_json: JSON string or parsed dictionary of the exported flow schema.
        bot_slug: Optional target bot to link this flow to. If omitted, uses metadata.bot.
        overwrite: If True, updates an existing flow with the same name.
                   If False and the flow exists, throws an error or requires rename.

    Returns:
        Dict with status, flow_name, nodes_count, transitions_count, variables_count.
    """
    frappe.has_permission("Chatbot Flow", "write", throw=True)

    if isinstance(flow_json, str):
        try:
            payload = json.loads(flow_json)
        except Exception as e:
            frappe.throw(_("Invalid JSON format for flow import: {0}").format(str(e)))
    elif isinstance(flow_json, dict):
        payload = flow_json
    else:
        frappe.throw(_("flow_json must be a JSON string or dictionary."))

    if not isinstance(payload, dict):
        frappe.throw(_("Flow payload must be a JSON object."))

    # Extract metadata
    metadata = payload.get("metadata") or {}
    flow_slug = (metadata.get("flow_name") or payload.get("flow_name") or "").strip()
    if not flow_slug:
        flow_slug = f"imported_flow_{frappe.generate_hash(length=8)}"

    target_bot = (bot_slug or metadata.get("bot") or "").strip()
    if not target_bot:
        frappe.throw(_("Target bot slug must be provided either in metadata or as 'bot_slug' parameter."))

    if not frappe.db.exists("Chatbot", target_bot):
        frappe.throw(_("Target Chatbot '{0}' does not exist.").format(target_bot), exc=frappe.DoesNotExistError)

    # Determine unique or target flow docname
    actual_flow_docname = f"{target_bot}-{flow_slug}"

    is_overwrite = frappe.utils.cint(overwrite) if not isinstance(overwrite, bool) else (1 if overwrite else 0)

    flow_exists = frappe.db.exists("Chatbot Flow", actual_flow_docname)
    if flow_exists and not is_overwrite:
        frappe.throw(
            _("Chatbot Flow '{0}' already exists. Pass overwrite=True to update it.").format(actual_flow_docname),
            exc=frappe.DuplicateEntryError,
        )

    # Validate graph structure before mutating database
    nodes = payload.get("nodes", [])
    transitions = payload.get("transitions", [])
    variables = payload.get("variables", [])

    validate_flow_structure({"nodes": nodes, "transitions": transitions, "variables": variables})

    # Create or update parent Chatbot Flow
    if not flow_exists:
        flow_doc = frappe.get_doc({
            "doctype": "Chatbot Flow",
            "name": actual_flow_docname,
            "flow_name": flow_slug,
            "bot": target_bot,
            "status": metadata.get("status") or "Draft",
            "version": metadata.get("version") or "1.0.0",
            "description": metadata.get("description") or f"Imported flow {flow_slug}",
        }).insert(ignore_permissions=True)
    else:
        flow_doc = frappe.get_doc("Chatbot Flow", actual_flow_docname)
        if metadata.get("description"):
            flow_doc.description = metadata.get("description")
        if metadata.get("version"):
            flow_doc.version = metadata.get("version")
        flow_doc.save(ignore_permissions=True)

    # Persist graph nodes, transitions, variables via save_visual_flow
    flow_data = {
        "nodes": nodes,
        "transitions": transitions,
        "variables": variables,
    }
    save_result = save_visual_flow(actual_flow_docname, flow_data)

    return {
        "status": "success",
        "flow_name": actual_flow_docname,
        "bot": target_bot,
        "nodes_count": save_result.get("nodes_count", len(nodes)),
        "transitions_count": save_result.get("transitions_count", len(transitions)),
        "variables_count": save_result.get("variables_count", len(variables)),
        "message": _("Flow '{0}' successfully imported into bot '{1}'.").format(actual_flow_docname, target_bot),
    }
