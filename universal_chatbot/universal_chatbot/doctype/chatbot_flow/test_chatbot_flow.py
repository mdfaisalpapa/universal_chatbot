# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestChatbotFlow(FrappeTestCase):
    def setUp(self):
        if not frappe.db.exists("Chatbot", "flow_test_bot"):
            frappe.get_doc({
                "doctype": "Chatbot",
                "bot_name": "flow_test_bot",
                "title": "Flow Test Bot",
            }).insert(ignore_permissions=True)

    def tearDown(self):
        frappe.db.rollback()

    def test_create_chatbot_flow(self):
        flow = frappe.get_doc({
            "doctype": "Chatbot Flow",
            "bot": "flow_test_bot",
            "flow_name": "onboarding_flow",
            "version": "1.0.0",
            "status": "Published",
            "description": "User onboarding journey",
        }).insert(ignore_permissions=True)

        self.assertEqual(flow.name, "flow_test_bot-onboarding_flow")
        self.assertEqual(flow.status, "Published")
