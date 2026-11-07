"""Frappe database repository adapter for Universal Chatbot.

Implements ConversationRepositoryInterface to isolate frappe dependencies
from the core conversational and flow engines.
"""

import json
from typing import Any, Dict, List, Optional
import frappe
from frappe.utils import now_datetime
from universal_chatbot.core.exceptions import (
    ConversationNotFoundError,
    FlowExecutionError,
    SecurityValidationError,
)
from universal_chatbot.core.interfaces import ConversationRepositoryInterface
from universal_chatbot.flow.schema import (
    FlowDefinition,
    NodeDefinition,
    TransitionDefinition,
    VariableDefinition,
)


class FrappeConversationRepository(ConversationRepositoryInterface):
    """Frappe ORM adapter implementing ConversationRepositoryInterface."""

    def get_or_create_contact(
        self,
        display_name: str,
        contact_status: str = "Active",
        email: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new contact.

        Identity linking across channels is strictly explicit—contacts are NEVER
        merged automatically based on display name or channel properties.
        """
        doc = frappe.get_doc({
            "doctype": "Chat Contact",
            "display_name": display_name,
            "contact_status": contact_status,
            "email": email,
            "phone": phone,
        }).insert(ignore_permissions=True)
        return doc.as_dict()

    def get_or_create_channel_identity(
        self,
        contact_id: str,
        channel: str,
        external_user_id: str,
        verification_status: str = "Anonymous",
    ) -> Dict[str, Any]:
        """Explicitly maps an external channel identity to a contact.

        If already bound to a different contact, raises SecurityValidationError
        to guarantee strict identity isolation.
        """
        existing_identity = frappe.db.get_value(
            "Channel Identity",
            {"channel": channel, "external_user_id": external_user_id},
            ["name", "contact", "verification_status"],
            as_dict=True,
        )
        if existing_identity:
            if existing_identity.contact != contact_id:
                raise SecurityValidationError(
                    f"Channel identity {channel}:{external_user_id} is already mapped to {existing_identity.contact}, not {contact_id}"
                )
            return existing_identity

        doc = frappe.get_doc({
            "doctype": "Channel Identity",
            "contact": contact_id,
            "channel": channel,
            "external_user_id": external_user_id,
            "verification_status": verification_status,
        }).insert(ignore_permissions=True)
        return doc.as_dict()

    def get_contact_by_channel_identity(
        self, channel: str, external_user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Lookup contact linked to an external channel user identity."""
        contact_id = frappe.db.get_value(
            "Channel Identity",
            {"channel": channel, "external_user_id": external_user_id},
            "contact",
        )
        if not contact_id:
            return None
        contact = frappe.get_doc("Chat Contact", contact_id)
        return contact.as_dict()

    def create_conversation(
        self,
        bot: str,
        deployment: str,
        contact: str,
        channel: str,
        status: str = "Active",
    ) -> Dict[str, Any]:
        """Create a new conversation session."""
        doc = frappe.get_doc({
            "doctype": "Chat Conversation",
            "bot": bot,
            "deployment": deployment,
            "contact": contact,
            "channel": channel,
            "status": status,
            "started_at": now_datetime(),
            "last_activity": now_datetime(),
        }).insert(ignore_permissions=True)
        return doc.as_dict()

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        if not frappe.db.exists("Chat Conversation", conversation_id):
            return None
        doc = frappe.get_doc("Chat Conversation", conversation_id)
        return doc.as_dict()

    def update_conversation_status(self, conversation_id: str, status: str) -> None:
        if not frappe.db.exists("Chat Conversation", conversation_id):
            raise ConversationNotFoundError(conversation_id)
        frappe.db.set_value(
            "Chat Conversation",
            conversation_id,
            {"status": status, "last_activity": now_datetime()},
            update_modified=True,
        )

    def touch_conversation(self, conversation_id: str) -> None:
        if frappe.db.exists("Chat Conversation", conversation_id):
            frappe.db.set_value(
                "Chat Conversation",
                conversation_id,
                "last_activity",
                now_datetime(),
                update_modified=False,
            )

    def save_state(
        self,
        conversation_id: str,
        current_node: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        active_flow_version: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Save or update flow execution state for pause/resume."""
        if not frappe.db.exists("Chat Conversation", conversation_id):
            raise ConversationNotFoundError(conversation_id)

        vars_json = json.dumps(variables or {})
        ctx_json = json.dumps(context or {})

        existing_name = frappe.db.get_value(
            "Conversation State", {"conversation": conversation_id}, "name"
        )
        if existing_name:
            doc = frappe.get_doc("Conversation State", existing_name)
            if current_node is not None:
                doc.current_node = current_node
            doc.variables = vars_json
            doc.context = ctx_json
            if active_flow_version:
                doc.active_flow_version = active_flow_version
            doc.save(ignore_permissions=True)
        else:
            doc = frappe.get_doc({
                "doctype": "Conversation State",
                "conversation": conversation_id,
                "current_node": current_node or "",
                "variables": vars_json,
                "context": ctx_json,
                "active_flow_version": active_flow_version,
            }).insert(ignore_permissions=True)

        return {
            "conversation": doc.conversation,
            "current_node": doc.current_node,
            "variables": json.loads(doc.variables or "{}"),
            "context": json.loads(doc.context or "{}"),
            "active_flow_version": doc.active_flow_version,
        }

    def get_state(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        state_data = frappe.db.get_value(
            "Conversation State",
            {"conversation": conversation_id},
            ["name", "current_node", "variables", "context", "active_flow_version"],
            as_dict=True,
        )
        if not state_data:
            return None
        return {
            "name": state_data.name,
            "conversation": conversation_id,
            "current_node": state_data.current_node,
            "variables": json.loads(state_data.variables or "{}"),
            "context": json.loads(state_data.context or "{}"),
            "active_flow_version": state_data.active_flow_version,
        }

    def log_message(
        self,
        conversation_id: str,
        direction: str,
        message_type: str,
        content: str,
        external_message_id: Optional[str] = None,
        status: str = "Sent",
    ) -> Dict[str, Any]:
        """Persist message and update conversation last_activity."""
        if not frappe.db.exists("Chat Conversation", conversation_id):
            raise ConversationNotFoundError(conversation_id)

        msg_doc = frappe.get_doc({
            "doctype": "Chat Message",
            "conversation": conversation_id,
            "direction": direction,
            "message_type": message_type,
            "content": content,
            "external_message_id": external_message_id,
            "status": status,
            "timestamp": now_datetime(),
        }).insert(ignore_permissions=True)

        self.touch_conversation(conversation_id)
        return msg_doc.as_dict()

    def get_messages(
        self, conversation_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        return frappe.get_all(
            "Chat Message",
            filters={"conversation": conversation_id},
            fields=[
                "name",
                "conversation",
                "direction",
                "message_type",
                "content",
                "external_message_id",
                "status",
                "timestamp",
            ],
            order_by="timestamp asc",
            limit=limit,
        )

    def record_event(
        self,
        conversation_id: str,
        event_type: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Record an audit trail event."""
        if not frappe.db.exists("Chat Conversation", conversation_id):
            raise ConversationNotFoundError(conversation_id)

        event_doc = frappe.get_doc({
            "doctype": "Conversation Event",
            "conversation": conversation_id,
            "event_type": event_type,
            "details": json.dumps(details or {}),
            "timestamp": now_datetime(),
        }).insert(ignore_permissions=True)

        return event_doc.as_dict()

    def get_events(
        self, conversation_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        events = frappe.get_all(
            "Conversation Event",
            filters={"conversation": conversation_id},
            fields=["name", "conversation", "event_type", "details", "timestamp"],
            order_by="timestamp asc",
            limit=limit,
        )
        for ev in events:
            if isinstance(ev.get("details"), str):
                try:
                    ev["details"] = json.loads(ev["details"])
                except Exception:
                    pass
        return events

    def get_flow_definition(self, flow_id: str) -> FlowDefinition:
        """Fetch a Chatbot Flow with its Nodes, Transitions, and Variables

        translated into a pure Python FlowDefinition.
        """
        if not frappe.db.exists("Chatbot Flow", flow_id):
            raise FlowExecutionError(f"Chatbot Flow '{flow_id}' not found")

        flow_doc = frappe.get_doc("Chatbot Flow", flow_id)

        # 1. Fetch nodes
        node_docs = frappe.get_all(
            "Flow Node",
            filters={"flow": flow_doc.name},
            fields=["name", "node_id", "node_type", "configuration"],
        )

        nodes: Dict[str, NodeDefinition] = {}
        doc_name_to_node_id: Dict[str, str] = {}
        start_node_id = None

        for n in node_docs:
            nid = n.node_id
            doc_name_to_node_id[n.name] = nid
            cfg = {}
            if n.configuration:
                try:
                    cfg = json.loads(n.configuration)
                except Exception:
                    cfg = {}

            nodes[nid] = NodeDefinition(
                node_id=nid,
                node_type=n.node_type,
                configuration=cfg,
            )
            if n.node_type == "Start" and not start_node_id:
                start_node_id = nid

        # 2. Fetch transitions
        node_doc_names = list(doc_name_to_node_id.keys())
        transitions: List[TransitionDefinition] = []

        if node_doc_names:
            trans_docs = frappe.get_all(
                "Flow Transition",
                filters={"source_node": ["in", node_doc_names]},
                fields=["source_node", "target_node", "condition"],
            )

            for t in trans_docs:
                src_id = doc_name_to_node_id.get(t.source_node)
                tgt_id = doc_name_to_node_id.get(t.target_node)
                if not src_id or not tgt_id:
                    continue

                cond = t.condition
                if cond and isinstance(cond, str) and cond.strip().startswith("{"):
                    try:
                        cond = json.loads(cond)
                    except Exception:
                        pass

                transitions.append(
                    TransitionDefinition(
                        source_node=src_id,
                        target_node=tgt_id,
                        condition=cond,
                    )
                )

        # 3. Fetch variables
        var_docs = frappe.get_all(
            "Flow Variable",
            filters={"flow": flow_doc.name},
            fields=["variable_name", "data_type", "default_value"],
        )

        variables: Dict[str, VariableDefinition] = {}
        for v in var_docs:
            variables[v.variable_name] = VariableDefinition(
                name=v.variable_name,
                data_type=v.data_type or "String",
                default_value=v.default_value,
            )

        return FlowDefinition(
            flow_id=flow_doc.name,
            name=flow_doc.flow_name,
            version=flow_doc.version or "1.0.0",
            nodes=nodes,
            transitions=transitions,
            variables=variables,
            start_node_id=start_node_id,
        )

    def save_flow_execution(
        self,
        conversation_id: str,
        flow_id: str,
        current_node: Optional[str],
        status: str,
        execution_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Upsert flow execution record."""
        # Normalize status to Title Case to match DocType Select options
        status_map = {
            "running": "Running",
            "paused": "Paused",
            "completed": "Completed",
            "failed": "Failed",
        }
        normalized_status = status_map.get(status.lower(), status.capitalize())

        ctx_json = json.dumps(execution_context or {})
        existing = frappe.db.get_value(
            "Flow Execution",
            {"conversation": conversation_id, "flow": flow_id},
            "name",
        )
        if existing:
            doc = frappe.get_doc("Flow Execution", existing)
            doc.current_node = current_node or ""
            doc.status = normalized_status
            doc.execution_context = ctx_json
            doc.save(ignore_permissions=True)
        else:
            doc = frappe.get_doc({
                "doctype": "Flow Execution",
                "conversation": conversation_id,
                "flow": flow_id,
                "current_node": current_node or "",
                "status": normalized_status,
                "execution_context": ctx_json,
            }).insert(ignore_permissions=True)

        return doc.as_dict()
