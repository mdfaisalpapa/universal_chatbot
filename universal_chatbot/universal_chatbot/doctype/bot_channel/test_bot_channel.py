# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.exceptions import ValidationError


class TestBotChannel(FrappeTestCase):
    def tearDown(self):
        frappe.db.rollback()

    def test_create_bot_channel(self):
        channel = frappe.get_doc({
            "doctype": "Bot Channel",
            "channel_name": "Web Widget Main",
            "channel_type": "Web Widget",
            "is_enabled": 1,
            "config": json.dumps({"theme": "dark", "position": "bottom-right"}),
        }).insert(ignore_permissions=True)

        self.assertEqual(channel.channel_name, "Web Widget Main")
        self.assertEqual(channel.channel_type, "Web Widget")
        self.assertEqual(channel.is_enabled, 1)

    def test_invalid_config_json_raises_error(self):
        channel = frappe.get_doc({
            "doctype": "Bot Channel",
            "channel_name": "Web Widget Broken",
            "channel_type": "Web Widget",
            "config": "{invalid_json: 123",
        })
        with self.assertRaises(ValidationError):
            channel.insert(ignore_permissions=True)
