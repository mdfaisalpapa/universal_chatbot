# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.exceptions import ValidationError


class TestBotVersion(FrappeTestCase):
    def setUp(self):
        if not frappe.db.exists("Chatbot", "versioned_bot"):
            frappe.get_doc({
                "doctype": "Chatbot",
                "bot_name": "versioned_bot",
                "title": "Versioned Bot",
            }).insert(ignore_permissions=True)

    def tearDown(self):
        frappe.db.rollback()

    def test_create_and_publish_version(self):
        flow_json = json.dumps({"nodes": [{"id": "start", "type": "Start"}]})
        version = frappe.get_doc({
            "doctype": "Bot Version",
            "chatbot": "versioned_bot",
            "version_number": "1.0.0",
            "status": "Published",
            "flow_definition": flow_json,
            "changelog": "Initial release",
        }).insert(ignore_permissions=True)

        self.assertEqual(version.chatbot, "versioned_bot")
        self.assertEqual(version.version_number, "1.0.0")
        self.assertIsNotNone(version.published_at)

    def test_invalid_flow_json_raises_error(self):
        version = frappe.get_doc({
            "doctype": "Bot Version",
            "chatbot": "versioned_bot",
            "version_number": "1.0.1",
            "flow_definition": "{unclosed_json",
        })
        with self.assertRaises(ValidationError):
            version.insert(ignore_permissions=True)
