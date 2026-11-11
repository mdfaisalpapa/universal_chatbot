"""Backend API for the Visual Flow Designer.

Provides whitelisted endpoints for loading, validating, saving,
and publishing graphical conversation flows.
"""

import json
from typing import Any, Dict, List, Optional
import frappe
from frappe import _
from universal_chatbot.flow.evaluator import SafeConditionEvaluator
from universal_chatbot.flow.schema import FlowNodeType


NODE_TYPE_MAP = {
    "start": "Start",
    "send_message": "Send Message",
    "ask_question": "Ask Question",
    "multiple_choice": "Multiple Choice",
    "condition": "Condition",
    "set_variable": "Set Variable",
    "call_action": "Call Action",
    "end": "End",
    "start node": "Start",
    "end node": "End",
}


def normalize_node_type(raw_type: str) -> str:
    """Normalize node type string to standard FlowNodeType value."""
    key = str(raw_type or "").strip().lower()
    return NODE_TYPE_MAP.get(key, raw_type)


def validate_flow_structure(flow_data: Dict[str, Any]) -> None:
    """Validate that the flow graph satisfies Phase 1 integrity rules."""
    nodes = flow_data.get("nodes", [])
    if isinstance(nodes, dict):
        nodes = list(nodes.values())

    if not nodes:
        frappe.throw(_("Flow must contain at least one node."))

    start_nodes = [n for n in nodes if normalize_node_type(n.get("node_type")) == FlowNodeType.START.value]
    if len(start_nodes) != 1:
        frappe.throw(
            _("Flow must have exactly one Start node. Found {0}.").format(len(start_nodes))
        )

    # Ensure all nodes have valid unique node_ids
    node_ids = set()
    for n in nodes:
        nid = (n.get("node_id") or "").strip()
        if not nid:
            frappe.throw(_("All flow nodes must have a non-empty Node ID."))
        if nid in node_ids:
            frappe.throw(_("Duplicate Node ID '{0}' found.").format(nid))
        node_ids.add(nid)

    # Validate transitions
    transitions = flow_data.get("transitions", [])
    for t in transitions:
        src = t.get("source_node")
        tgt = t.get("target_node")
        if src not in node_ids:
            frappe.throw(_("Transition source node '{0}' does not exist.").format(src))
        if tgt not in node_ids:
            frappe.throw(_("Transition target node '{0}' does not exist.").format(tgt))

        # Check condition syntax if provided
        cond = t.get("condition")
        if cond and isinstance(cond, str) and cond.strip().startswith("{"):
            try:
                json.loads(cond)
            except Exception as e:
                frappe.throw(_("Condition JSON for transition {0} -> {1} is invalid: {2}").format(src, tgt, str(e)))


@frappe.whitelist()
def load_visual_flow(flow_name: str) -> Dict[str, Any]:
    """Retrieve full visual graph data for a Chatbot Flow."""
    frappe.has_permission("Chatbot Flow", "read", throw=True)

    if not frappe.db.exists("Chatbot Flow", flow_name):
        frappe.throw(_("Chatbot Flow '{0}' not found.").format(flow_name), exc=frappe.DoesNotExistError)

    flow_doc = frappe.get_doc("Chatbot Flow", flow_name)

    # Load Nodes
    node_docs = frappe.get_all(
        "Flow Node",
        filters={"flow": flow_name},
        fields=["name", "node_id", "node_type", "configuration"],
    )

    nodes = []
    doc_name_to_node_id = {}
    for n in node_docs:
        doc_name_to_node_id[n.name] = n.node_id
        cfg = {}
        if n.configuration:
            try:
                cfg = json.loads(n.configuration)
            except Exception:
                cfg = {}

        nodes.append({
            "docname": n.name,
            "node_id": n.node_id,
            "node_type": n.node_type,
            "configuration": cfg,
            "x": cfg.get("ui_x", 100),
            "y": cfg.get("ui_y", 100),
        })

    # Load Transitions
    transitions = []
    if doc_name_to_node_id:
        trans_docs = frappe.get_all(
            "Flow Transition",
            filters={"source_node": ["in", list(doc_name_to_node_id.keys())]},
            fields=["name", "source_node", "target_node", "condition"],
        )
        for t in trans_docs:
            src = doc_name_to_node_id.get(t.source_node)
            tgt = doc_name_to_node_id.get(t.target_node)
            if src and tgt:
                transitions.append({
                    "name": t.name,
                    "source_node": src,
                    "target_node": tgt,
                    "condition": t.condition or "",
                })

    # Load Variables
    var_docs = frappe.get_all(
        "Flow Variable",
        filters={"flow": flow_name},
        fields=["name", "variable_name", "data_type", "default_value"],
    )
    variables = []
    for v in var_docs:
        variables.append({
            "name": v.name,
            "variable_name": v.variable_name,
            "data_type": v.data_type,
            "default_value": v.default_value,
        })

    return {
        "flow_name": flow_doc.name,
        "bot": flow_doc.bot,
        "version": flow_doc.version,
        "status": flow_doc.status,
        "nodes": nodes,
        "transitions": transitions,
        "variables": variables,
    }


@frappe.whitelist()
def save_visual_flow(flow_name: str, flow_data: Any) -> Dict[str, Any]:
    """Persist graph structure, nodes, transitions, and variables."""
    frappe.has_permission("Chatbot Flow", "write", throw=True)

    if not frappe.db.exists("Chatbot Flow", flow_name):
        frappe.throw(_("Chatbot Flow '{0}' not found.").format(flow_name), exc=frappe.DoesNotExistError)

    if isinstance(flow_data, str):
        try:
            flow_data = json.loads(flow_data)
        except Exception as e:
            frappe.throw(_("flow_data must be valid JSON: {0}").format(str(e)))

    # 1. Structural validation
    validate_flow_structure(flow_data)

    flow_doc = frappe.get_doc("Chatbot Flow", flow_name)
    nodes_input = flow_data.get("nodes", [])
    if isinstance(nodes_input, dict):
        nodes_input = list(nodes_input.values())

    # 2. Sync Flow Nodes (Upsert retained nodes)
    existing_nodes = {
        n.node_id: n.name
        for n in frappe.get_all("Flow Node", filters={"flow": flow_name}, fields=["name", "node_id"])
    }
    retained_node_names = set()
    node_id_to_docname = {}

    for n in nodes_input:
        nid = n["node_id"]
        cfg = n.get("configuration") or {}
        if isinstance(cfg, str):
            try:
                cfg = json.loads(cfg)
            except Exception:
                cfg = {}
        # Embed UI coordinates in configuration
        cfg["ui_x"] = n.get("x", cfg.get("ui_x", 100))
        cfg["ui_y"] = n.get("y", cfg.get("ui_y", 100))

        norm_type = normalize_node_type(n["node_type"])
        if nid in existing_nodes:
            docname = existing_nodes[nid]
            node_doc = frappe.get_doc("Flow Node", docname)
            node_doc.node_type = norm_type
            node_doc.configuration = json.dumps(cfg)
            node_doc.save(ignore_permissions=True)
        else:
            node_doc = frappe.get_doc({
                "doctype": "Flow Node",
                "flow": flow_name,
                "node_id": nid,
                "node_type": norm_type,
                "configuration": json.dumps(cfg),
            }).insert(ignore_permissions=True)

        retained_node_names.add(node_doc.name)
        node_id_to_docname[nid] = node_doc.name

    # 3. Clean up Flow Transitions FIRST before deleting any Flow Nodes
    # This prevents LinkExistsError when a node linked to transitions is removed
    all_existing_node_docnames = list(existing_nodes.values())
    if all_existing_node_docnames:
        existing_source_transitions = frappe.get_all(
            "Flow Transition",
            filters={"source_node": ["in", all_existing_node_docnames]},
            fields=["name"],
        )
        existing_target_transitions = frappe.get_all(
            "Flow Transition",
            filters={"target_node": ["in", all_existing_node_docnames]},
            fields=["name"],
        )
        all_trans_names = set(t.name for t in existing_source_transitions) | set(t.name for t in existing_target_transitions)
        for t_name in all_trans_names:
            frappe.delete_doc("Flow Transition", t_name, ignore_permissions=True, force=1)

    # 4. Now safely delete orphaned/removed Flow Nodes
    for nid, dname in existing_nodes.items():
        if dname not in retained_node_names:
            frappe.delete_doc("Flow Node", dname, ignore_permissions=True, force=1)

    # 5. Insert new Flow Transitions for the active graph
    transitions_input = flow_data.get("transitions", [])
    created_transitions = 0
    for t in transitions_input:
        src_id = t["source_node"]
        tgt_id = t["target_node"]
        src_docname = node_id_to_docname.get(src_id)
        tgt_docname = node_id_to_docname.get(tgt_id)

        if src_docname and tgt_docname:
            cond = t.get("condition")
            if isinstance(cond, dict):
                cond = json.dumps(cond)

            frappe.get_doc({
                "doctype": "Flow Transition",
                "source_node": src_docname,
                "target_node": tgt_docname,
                "condition": cond or "",
            }).insert(ignore_permissions=True)
            created_transitions += 1

    # 6. Sync Flow Variables
    existing_vars = {
        v.variable_name: v.name
        for v in frappe.get_all("Flow Variable", filters={"flow": flow_name}, fields=["name", "variable_name"])
    }
    retained_vars = set()
    vars_input = flow_data.get("variables", [])
    if isinstance(vars_input, dict):
        vars_input = [
            {"variable_name": k, **(v if isinstance(v, dict) else {"default_value": v})}
            for k, v in vars_input.items()
        ]

    for v in vars_input:
        vname = v.get("variable_name") or v.get("name")
        if not vname:
            continue
        dtype = v.get("data_type", "String")
        dval = v.get("default_value", "")

        if vname in existing_vars:
            vdoc = frappe.get_doc("Flow Variable", existing_vars[vname])
            vdoc.data_type = dtype
            vdoc.default_value = str(dval) if dval is not None else ""
            vdoc.save(ignore_permissions=True)
        else:
            vdoc = frappe.get_doc({
                "doctype": "Flow Variable",
                "flow": flow_name,
                "variable_name": vname,
                "data_type": dtype,
                "default_value": str(dval) if dval is not None else "",
            }).insert(ignore_permissions=True)
        retained_vars.add(vdoc.name)

    for vname, dname in existing_vars.items():
        if dname not in retained_vars:
            frappe.delete_doc("Flow Variable", dname, ignore_permissions=True, force=1)

    # Update modified timestamp on Chatbot Flow and commit
    frappe.db.set_value("Chatbot Flow", flow_name, "modified", frappe.utils.now(), update_modified=False)
    frappe.db.commit()

    return {
        "status": "success",
        "flow_name": flow_name,
        "nodes_count": len(retained_node_names),
        "transitions_count": created_transitions,
        "variables_count": len(retained_vars),
    }


@frappe.whitelist()
def publish_flow(flow_name: str, changelog: str = "Published from Visual Flow Designer") -> Dict[str, Any]:
    """Create an immutable Bot Version snapshot and set flow status to Published."""
    frappe.has_permission("Chatbot Flow", "write", throw=True)

    if not frappe.db.exists("Chatbot Flow", flow_name):
        frappe.throw(_("Chatbot Flow '{0}' not found.").format(flow_name), exc=frappe.DoesNotExistError)

    flow_doc = frappe.get_doc("Chatbot Flow", flow_name)
    graph_data = load_visual_flow(flow_name)

    # Validate prior to publishing
    validate_flow_structure(graph_data)

    bot_name = flow_doc.bot
    # Determine new version number
    latest_version = frappe.db.sql(
        "SELECT version_number FROM `tabBot Version` WHERE chatbot = %s ORDER BY creation DESC LIMIT 1",
        bot_name,
    )
    if latest_version and latest_version[0][0]:
        try:
            parts = [int(p) for p in str(latest_version[0][0]).lstrip("v").split(".")]
            parts[-1] += 1
            new_version_num = f"{parts[0]}.{parts[1]}.{parts[2]}"
        except Exception:
            new_version_num = "1.0.1"
    else:
        new_version_num = "1.0.0"

    version_doc = frappe.get_doc({
        "doctype": "Bot Version",
        "chatbot": bot_name,
        "version_number": new_version_num,
        "status": "Published",
        "flow_definition": json.dumps(graph_data),
        "changelog": changelog,
    }).insert(ignore_permissions=True)

    # Update flow status & primary flow
    flow_doc.status = "Published"
    flow_doc.version = new_version_num
    flow_doc.save(ignore_permissions=True)

    # Point chatbot to active version & primary flow
    frappe.db.set_value(
        "Chatbot",
        bot_name,
        {"active_version": version_doc.name, "primary_flow": flow_name, "is_published": 1, "status": "Active"},
    )

    return {
        "status": "success",
        "bot_version": version_doc.name,
        "version_number": new_version_num,
        "flow_name": flow_name,
    }


@frappe.whitelist()
def unpublish_flow(flow_name: str) -> Dict[str, Any]:
    """Revert a published flow status back to Draft."""
    frappe.has_permission("Chatbot Flow", "write", throw=True)

    if not frappe.db.exists("Chatbot Flow", flow_name):
        frappe.throw(_("Chatbot Flow '{0}' not found.").format(flow_name), exc=frappe.DoesNotExistError)

    flow_doc = frappe.get_doc("Chatbot Flow", flow_name)
    flow_doc.status = "Draft"
    flow_doc.save(ignore_permissions=True)

    frappe.db.commit()
    return {
        "status": "success",
        "message": _("Flow '{0}' has been unpublished and reverted to Draft.").format(flow_name),
        "flow_name": flow_name,
        "new_status": "Draft",
    }



@frappe.whitelist()
def get_available_integration_actions(bot: Optional[str] = None, flow_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return configured Integration Actions that are linked to the specific Bot and its active integrations

    for use in the Visual Flow Designer dropdown.
    """
    frappe.has_permission("Integration Action", "read", throw=True)

    target_bot = (bot or "").strip()
    if not target_bot and flow_name and frappe.db.exists("Chatbot Flow", flow_name):
        target_bot = frappe.db.get_value("Chatbot Flow", flow_name, "bot") or ""

    # Find active integrations linked to this bot (or shared unlinked integrations)
    if target_bot:
        linked_integrations = frappe.get_all(
            "Chatbot Integration",
            filters={"status": "Active", "chatbot": ["in", [target_bot, "", None]]},
            pluck="name",
        )
    else:
        linked_integrations = frappe.get_all(
            "Chatbot Integration",
            filters={"status": "Active"},
            pluck="name",
        )

    if not linked_integrations:
        return []

    actions = frappe.get_all(
        "Integration Action",
        filters={"integration": ["in", linked_integrations]},
        fields=["name", "action_name", "integration", "method", "operation", "input_schema", "output_mapping"],
        order_by="action_name asc",
    )

    results = []
    for a in actions:
        in_schema = {}
        out_map = {}
        if a.input_schema:
            try:
                in_schema = json.loads(a.input_schema) if isinstance(a.input_schema, str) else a.input_schema
            except Exception:
                in_schema = {}
        if a.output_mapping:
            try:
                out_map = json.loads(a.output_mapping) if isinstance(a.output_mapping, str) else a.output_mapping
            except Exception:
                out_map = {}

        results.append({
            "name": a.name,
            "action_name": a.action_name,
            "integration": a.integration,
            "method": a.method or "POST",
            "operation": a.operation or "",
            "input_schema": in_schema,
            "output_mapping": out_map,
        })

    return results


@frappe.whitelist()
def test_integration_action(action_name: str, sample_parameters: Any = None) -> Dict[str, Any]:
    """Execute a dry-run test of an Integration Action with sample parameters and return output schema data."""
    frappe.has_permission("Chatbot Flow", "write", throw=True)
    from universal_chatbot.adapters.frappe_repository import FrappeConversationRepository

    if isinstance(sample_parameters, str):
        try:
            sample_parameters = json.loads(sample_parameters)
        except Exception:
            sample_parameters = {}
    elif not isinstance(sample_parameters, dict):
        sample_parameters = {}

    repo = FrappeConversationRepository()
    try:
        result = repo.execute_action(action_name=action_name, parameters=sample_parameters)
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        frappe.log_error(f"Error testing integration action '{action_name}': {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


@frappe.whitelist()
def export_flow_json(flow_name: str) -> Dict[str, Any]:
    """Export flow configuration to standard downloadable JSON schema."""
    from universal_chatbot.flow.export_import import export_flow_json as _export
    return _export(flow_name=flow_name)


@frappe.whitelist()
def import_flow_json(
    flow_json: Any,
    bot_slug: Optional[str] = None,
    overwrite: Any = False,
) -> Dict[str, Any]:
    """Import and provision a flow configuration from a JSON schema."""
    from universal_chatbot.flow.export_import import import_flow_json as _import
    return _import(flow_json=flow_json, bot_slug=bot_slug, overwrite=overwrite)

