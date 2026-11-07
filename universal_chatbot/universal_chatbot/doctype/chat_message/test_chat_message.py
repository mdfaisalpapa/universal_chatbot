# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestChatMessage(FrappeTestCase):
    def setUp(self):
        if not frappe.db.exists("Chatbot", "msg_bot"):
            frappe.get_doc({
                "doctype": "Chatbot",
                "bot_name": "msg_bot",
                "title": "Message Bot",
            }).insert(ignore_permissions=True)

        if not frappe.db.exists("Bot Channel", "Msg Channel"):
            frappe.get_doc({
                "doctype": "Bot Channel",
                "channel_name": "Msg Channel",
                "channel_type": "Web Widget",
            }).insert(ignore_permissions=True)

        deployment = frappe.get_doc({
            "doctype": "Bot Deployment",
            "deployment_name": "Msg Deploy",
            "chatbot": "msg_bot",
            "channel": "Msg Channel",
        }).insert(ignore_permissions=True)

        contact = frappe.get_doc({
            "doctype": "Chat Contact",
            "display_name": "Msg User",
        }).insert(ignore_permissions=True)

        self.conv = frappe.get_doc({
            "doctype": "Chat Conversation",
            "bot": "msg_bot",
            "deployment": deployment.name,
            "contact": contact.name,
            "channel": "web",
        }).insert(ignore_permissions=True)

    def tearDown(self):
        frappe.db.rollback()

    def test_log_inbound_and_outbound_messages(self):
        m1 = frappe.get_doc({
            "doctype": "Chat Message",
            "conversation": self.conv.name,
            "direction": "Inbound",
            "message_type": "Text",
            "content": "Hello",
            "external_message_id": "ext_001",
        }).insert(ignore_permissions=True)

        m2 = frappe.get_doc({
            "doctype": "Chat Message",
            "conversation": self.conv.name,
            "direction": "Outbound",
            "message_type": "Text",
            "content": "Hi there! How can I help?",
        }).insert(ignore_permissions=True)

        self.assertTrue(m1.name.startswith("MSG-"))
        self.assertEqual(m1.direction, "Inbound")
        self.assertEqual(m2.direction, "Outbound")
        self.assertIsNotNone(m1.timestamp)
