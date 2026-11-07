# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.exceptions import ValidationError


class TestConversationState(FrappeTestCase):
    def setUp(self):
        if not frappe.db.exists("Chatbot", "state_bot"):
            frappe.get_doc({
                "doctype": "Chatbot",
                "bot_name": "state_bot",
                "title": "State Bot",
            }).insert(ignore_permissions=True)

        if not frappe.db.exists("Bot Channel", "State Channel"):
            frappe.get_doc({
                "doctype": "Bot Channel",
                "channel_name": "State Channel",
                "channel_type": "Web Widget",
            }).insert(ignore_permissions=True)

        deployment = frappe.get_doc({
            "doctype": "Bot Deployment",
            "deployment_name": "State Deploy",
            "chatbot": "state_bot",
            "channel": "State Channel",
        }).insert(ignore_permissions=True)

        contact = frappe.get_doc({
            "doctype": "Chat Contact",
            "display_name": "State User",
        }).insert(ignore_permissions=True)

        self.conv = frappe.get_doc({
            "doctype": "Chat Conversation",
            "bot": "state_bot",
            "deployment": deployment.name,
            "contact": contact.name,
            "channel": "web",
        }).insert(ignore_permissions=True)

    def tearDown(self):
        frappe.db.rollback()

    def test_save_and_load_state(self):
        variables = {"user_choice": "order_lookup", "order_id": "ORD-99"}
        context = {"retry_count": 0}

        state = frappe.get_doc({
            "doctype": "Conversation State",
            "conversation": self.conv.name,
            "current_node": "node_ask_order_id",
            "variables": json.dumps(variables),
            "context": json.dumps(context),
        }).insert(ignore_permissions=True)

        self.assertEqual(state.name, f"STATE-{self.conv.name}")
        self.assertEqual(state.current_node, "node_ask_order_id")

        loaded_vars = json.loads(state.variables)
        self.assertEqual(loaded_vars["order_id"], "ORD-99")

    def test_invalid_json_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            frappe.get_doc({
                "doctype": "Conversation State",
                "conversation": self.conv.name,
                "variables": "not_valid_json",
            }).insert(ignore_permissions=True)
