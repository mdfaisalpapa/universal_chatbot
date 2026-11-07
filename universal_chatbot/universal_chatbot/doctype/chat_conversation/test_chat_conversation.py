# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestChatConversation(FrappeTestCase):
    def setUp(self):
        if not frappe.db.exists("Chatbot", "test_conv_bot"):
            frappe.get_doc({
                "doctype": "Chatbot",
                "bot_name": "test_conv_bot",
                "title": "Test Conv Bot",
            }).insert(ignore_permissions=True)

        if not frappe.db.exists("Bot Channel", "Test Conv Channel"):
            frappe.get_doc({
                "doctype": "Bot Channel",
                "channel_name": "Test Conv Channel",
                "channel_type": "Web Widget",
            }).insert(ignore_permissions=True)

        self.deployment = frappe.get_doc({
            "doctype": "Bot Deployment",
            "deployment_name": "Conv Deploy",
            "chatbot": "test_conv_bot",
            "channel": "Test Conv Channel",
        }).insert(ignore_permissions=True)

        self.contact = frappe.get_doc({
            "doctype": "Chat Contact",
            "display_name": "Conv User",
        }).insert(ignore_permissions=True)

    def tearDown(self):
        frappe.db.rollback()

    def test_create_conversation(self):
        conv = frappe.get_doc({
            "doctype": "Chat Conversation",
            "bot": "test_conv_bot",
            "deployment": self.deployment.name,
            "contact": self.contact.name,
            "channel": "web",
            "status": "Active",
        }).insert(ignore_permissions=True)

        self.assertTrue(conv.name.startswith("CONV-"))
        self.assertIsNotNone(conv.started_at)
        self.assertIsNotNone(conv.last_activity)

    def test_touch_conversation(self):
        conv = frappe.get_doc({
            "doctype": "Chat Conversation",
            "bot": "test_conv_bot",
            "deployment": self.deployment.name,
            "contact": self.contact.name,
            "channel": "web",
        }).insert(ignore_permissions=True)

        initial_activity = conv.last_activity
        conv.touch()
        conv.reload()
        self.assertGreaterEqual(conv.last_activity, initial_activity)
