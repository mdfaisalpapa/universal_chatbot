# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestFlowVariable(FrappeTestCase):
    def setUp(self):
        if not frappe.db.exists("Chatbot", "var_test_bot"):
            frappe.get_doc({
                "doctype": "Chatbot",
                "bot_name": "var_test_bot",
                "title": "Var Test Bot",
            }).insert(ignore_permissions=True)

        if not frappe.db.exists("Chatbot Flow", "var_test_bot-var_flow"):
            self.flow = frappe.get_doc({
                "doctype": "Chatbot Flow",
                "bot": "var_test_bot",
                "flow_name": "var_flow",
            }).insert(ignore_permissions=True)
        else:
            self.flow = frappe.get_doc("Chatbot Flow", "var_test_bot-var_flow")

    def tearDown(self):
        frappe.db.rollback()

    def test_create_flow_variable(self):
        var = frappe.get_doc({
            "doctype": "Flow Variable",
            "flow": self.flow.name,
            "variable_name": "order_number",
            "data_type": "String",
            "default_value": "ORD-000",
        }).insert(ignore_permissions=True)

        self.assertEqual(var.name, f"{self.flow.name}:order_number")
        self.assertEqual(var.data_type, "String")
        self.assertEqual(var.default_value, "ORD-000")
