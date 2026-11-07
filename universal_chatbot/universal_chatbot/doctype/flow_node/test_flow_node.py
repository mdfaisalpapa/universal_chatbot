# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.exceptions import ValidationError


class TestFlowNode(FrappeTestCase):
    def setUp(self):
        if not frappe.db.exists("Chatbot", "node_test_bot"):
            frappe.get_doc({
                "doctype": "Chatbot",
                "bot_name": "node_test_bot",
                "title": "Node Test Bot",
            }).insert(ignore_permissions=True)

        if not frappe.db.exists("Chatbot Flow", "node_test_bot-sample_flow"):
            self.flow = frappe.get_doc({
                "doctype": "Chatbot Flow",
                "bot": "node_test_bot",
                "flow_name": "sample_flow",
            }).insert(ignore_permissions=True)
        else:
            self.flow = frappe.get_doc("Chatbot Flow", "node_test_bot-sample_flow")

    def tearDown(self):
        frappe.db.rollback()

    def test_create_flow_node(self):
        config = {"text": "Hello there!"}
        node = frappe.get_doc({
            "doctype": "Flow Node",
            "flow": self.flow.name,
            "node_id": "welcome_node",
            "node_type": "Send Message",
            "configuration": json.dumps(config),
        }).insert(ignore_permissions=True)

        self.assertEqual(node.name, f"{self.flow.name}-welcome_node")
        self.assertEqual(node.node_type, "Send Message")

    def test_invalid_config_json_raises(self):
        with self.assertRaises(ValidationError):
            frappe.get_doc({
                "doctype": "Flow Node",
                "flow": self.flow.name,
                "node_id": "broken_node",
                "node_type": "Start",
                "configuration": "{bad_json",
            }).insert(ignore_permissions=True)
