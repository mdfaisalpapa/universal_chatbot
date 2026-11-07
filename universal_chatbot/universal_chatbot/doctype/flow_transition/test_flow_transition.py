# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.exceptions import ValidationError


class TestFlowTransition(FrappeTestCase):
    def setUp(self):
        if not frappe.db.exists("Chatbot", "trans_test_bot"):
            frappe.get_doc({
                "doctype": "Chatbot",
                "bot_name": "trans_test_bot",
                "title": "Trans Test Bot",
            }).insert(ignore_permissions=True)

        if not frappe.db.exists("Chatbot Flow", "trans_test_bot-nav_flow"):
            self.flow = frappe.get_doc({
                "doctype": "Chatbot Flow",
                "bot": "trans_test_bot",
                "flow_name": "nav_flow",
            }).insert(ignore_permissions=True)
        else:
            self.flow = frappe.get_doc("Chatbot Flow", "trans_test_bot-nav_flow")

        self.node1 = frappe.get_doc({
            "doctype": "Flow Node",
            "flow": self.flow.name,
            "node_id": "step_1",
            "node_type": "Start",
        }).insert(ignore_permissions=True)

        self.node2 = frappe.get_doc({
            "doctype": "Flow Node",
            "flow": self.flow.name,
            "node_id": "step_2",
            "node_type": "End",
        }).insert(ignore_permissions=True)

    def tearDown(self):
        frappe.db.rollback()

    def test_create_transition(self):
        condition = json.dumps({"variable": "status", "operator": "==", "value": "active"})
        trans = frappe.get_doc({
            "doctype": "Flow Transition",
            "source_node": self.node1.name,
            "target_node": self.node2.name,
            "condition": condition,
        }).insert(ignore_permissions=True)

        self.assertIsNotNone(trans.name)
        self.assertEqual(trans.source_node, self.node1.name)
        self.assertEqual(trans.target_node, self.node2.name)

    def test_invalid_condition_json_raises(self):
        with self.assertRaises(ValidationError):
            frappe.get_doc({
                "doctype": "Flow Transition",
                "source_node": self.node1.name,
                "target_node": self.node2.name,
                "condition": "{invalid_json_condition",
            }).insert(ignore_permissions=True)
