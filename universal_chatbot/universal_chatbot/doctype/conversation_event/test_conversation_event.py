# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.tests.utils import FrappeTestCase


class TestConversationEvent(FrappeTestCase):
    def setUp(self):
        if not frappe.db.exists("Chatbot", "evt_bot"):
            frappe.get_doc({
                "doctype": "Chatbot",
                "bot_name": "evt_bot",
                "title": "Event Bot",
            }).insert(ignore_permissions=True)

        if not frappe.db.exists("Bot Channel", "Evt Channel"):
            frappe.get_doc({
                "doctype": "Bot Channel",
                "channel_name": "Evt Channel",
                "channel_type": "Web Widget",
            }).insert(ignore_permissions=True)

        deployment = frappe.get_doc({
            "doctype": "Bot Deployment",
            "deployment_name": "Evt Deploy",
            "chatbot": "evt_bot",
            "channel": "Evt Channel",
        }).insert(ignore_permissions=True)

        contact = frappe.get_doc({
            "doctype": "Chat Contact",
            "display_name": "Event User",
        }).insert(ignore_permissions=True)

        self.conv = frappe.get_doc({
            "doctype": "Chat Conversation",
            "bot": "evt_bot",
            "deployment": deployment.name,
            "contact": contact.name,
            "channel": "web",
        }).insert(ignore_permissions=True)

    def tearDown(self):
        frappe.db.rollback()

    def test_record_audit_events(self):
        details = {"from_node": "start", "to_node": "ask_name"}
        evt = frappe.get_doc({
            "doctype": "Conversation Event",
            "conversation": self.conv.name,
            "event_type": "flow_transition",
            "details": json.dumps(details),
        }).insert(ignore_permissions=True)

        self.assertTrue(evt.name.startswith("EVT-"))
        self.assertEqual(evt.event_type, "flow_transition")
        self.assertIsNotNone(evt.timestamp)
