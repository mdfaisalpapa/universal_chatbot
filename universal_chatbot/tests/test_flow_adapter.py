# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.tests.utils import FrappeTestCase
from universal_chatbot.adapters.frappe_repository import FrappeConversationRepository
from universal_chatbot.flow.engine import FlowExecutor
from universal_chatbot.flow.schema import ExecutionStatus


class TestFlowAdapter(FrappeTestCase):
    def setUp(self):
        self.repo = FrappeConversationRepository()
        self.executor = FlowExecutor()

        if not frappe.db.exists("Chatbot", "adapter_bot"):
            frappe.get_doc({
                "doctype": "Chatbot",
                "bot_name": "adapter_bot",
                "title": "Adapter Bot",
            }).insert(ignore_permissions=True)

        if not frappe.db.exists("Bot Channel", "Adapter Channel"):
            frappe.get_doc({
                "doctype": "Bot Channel",
                "channel_name": "Adapter Channel",
                "channel_type": "Web Widget",
            }).insert(ignore_permissions=True)

        self.deployment = frappe.get_doc({
            "doctype": "Bot Deployment",
            "deployment_name": "Adapter Deploy",
            "chatbot": "adapter_bot",
            "channel": "Adapter Channel",
        }).insert(ignore_permissions=True)

        self.contact = frappe.get_doc({
            "doctype": "Chat Contact",
            "display_name": "Adapter User",
        }).insert(ignore_permissions=True)

        self.conv = frappe.get_doc({
            "doctype": "Chat Conversation",
            "bot": "adapter_bot",
            "deployment": self.deployment.name,
            "contact": self.contact.name,
            "channel": "web",
        }).insert(ignore_permissions=True)

    def tearDown(self):
        frappe.db.rollback()

    def test_translate_and_execute_frappe_flow(self):
        # 1. Create Flow DocType records
        flow = frappe.get_doc({
            "doctype": "Chatbot Flow",
            "bot": "adapter_bot",
            "flow_name": "support_inquiry",
            "version": "1.0.0",
            "status": "Published",
        }).insert(ignore_permissions=True)

        n1 = frappe.get_doc({
            "doctype": "Flow Node",
            "flow": flow.name,
            "node_id": "start_node",
            "node_type": "Start",
            "configuration": json.dumps({"message": "Hello from Frappe Flow!"}),
        }).insert(ignore_permissions=True)

        n2 = frappe.get_doc({
            "doctype": "Flow Node",
            "flow": flow.name,
            "node_id": "ask_email",
            "node_type": "Ask Question",
            "configuration": json.dumps({"question": "Please enter your email:", "save_to_variable": "email"}),
        }).insert(ignore_permissions=True)

        frappe.get_doc({
            "doctype": "Flow Transition",
            "source_node": n1.name,
            "target_node": n2.name,
        }).insert(ignore_permissions=True)

        frappe.get_doc({
            "doctype": "Flow Variable",
            "flow": flow.name,
            "variable_name": "email",
            "data_type": "String",
            "default_value": "guest@example.com",
        }).insert(ignore_permissions=True)

        # 2. Fetch and translate through repository adapter
        flow_def = self.repo.get_flow_definition(flow.name)
        self.assertEqual(flow_def.flow_id, flow.name)
        self.assertIn("start_node", flow_def.nodes)
        self.assertIn("ask_email", flow_def.nodes)
        self.assertEqual(len(flow_def.transitions), 1)
        self.assertEqual(flow_def.transitions[0].source_node, "start_node")
        self.assertEqual(flow_def.transitions[0].target_node, "ask_email")
        self.assertIn("email", flow_def.variables)

        # 3. Execute translated pure Python flow with FlowExecutor
        result = self.executor.execute(
            flow=flow_def,
            conversation_id=self.conv.name,
            state={},
        )

        self.assertEqual(result.status, ExecutionStatus.PAUSED)
        self.assertEqual(result.current_node_id, "ask_email")
        self.assertEqual(len(result.messages), 2)
        self.assertEqual(result.messages[0]["text"], "Hello from Frappe Flow!")
        self.assertEqual(result.messages[1]["text"], "Please enter your email:")

        # 4. Save flow execution record via repository
        exec_record = self.repo.save_flow_execution(
            conversation_id=self.conv.name,
            flow_id=flow.name,
            current_node=result.current_node_id,
            status=result.status.value,
            execution_context={"variables": result.variables},
        )
        self.assertEqual(exec_record["status"], "Paused")
        self.assertEqual(exec_record["current_node"], "ask_email")
