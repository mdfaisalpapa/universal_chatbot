# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.exceptions import ValidationError


class TestFlowExecution(FrappeTestCase):
    def setUp(self):
        if not frappe.db.exists("Chatbot", "exec_test_bot"):
            frappe.get_doc({
                "doctype": "Chatbot",
                "bot_name": "exec_test_bot",
                "title": "Exec Test Bot",
            }).insert(ignore_permissions=True)

        if not frappe.db.exists("Bot Channel", "Exec Channel"):
            frappe.get_doc({
                "doctype": "Bot Channel",
                "channel_name": "Exec Channel",
                "channel_type": "Web Widget",
            }).insert(ignore_permissions=True)

        deployment = frappe.get_doc({
            "doctype": "Bot Deployment",
            "deployment_name": "Exec Deploy",
            "chatbot": "exec_test_bot",
            "channel": "Exec Channel",
        }).insert(ignore_permissions=True)

        contact = frappe.get_doc({
            "doctype": "Chat Contact",
            "display_name": "Exec User",
        }).insert(ignore_permissions=True)

        self.conv = frappe.get_doc({
            "doctype": "Chat Conversation",
            "bot": "exec_test_bot",
            "deployment": deployment.name,
            "contact": contact.name,
            "channel": "web",
        }).insert(ignore_permissions=True)

        self.flow = frappe.get_doc({
            "doctype": "Chatbot Flow",
            "bot": "exec_test_bot",
            "flow_name": "exec_flow",
        }).insert(ignore_permissions=True)

    def tearDown(self):
        frappe.db.rollback()

    def test_create_and_update_flow_execution(self):
        ctx = {"variables": {"score": 10}, "step": 1}
        exec_doc = frappe.get_doc({
            "doctype": "Flow Execution",
            "conversation": self.conv.name,
            "flow": self.flow.name,
            "current_node": "node_question_1",
            "status": "Running",
            "execution_context": json.dumps(ctx),
        }).insert(ignore_permissions=True)

        self.assertTrue(exec_doc.name.startswith("FLEX-"))
        self.assertEqual(exec_doc.status, "Running")

    def test_invalid_execution_context_raises(self):
        with self.assertRaises(ValidationError):
            frappe.get_doc({
                "doctype": "Flow Execution",
                "conversation": self.conv.name,
                "flow": self.flow.name,
                "execution_context": "invalid_json_string",
            }).insert(ignore_permissions=True)
