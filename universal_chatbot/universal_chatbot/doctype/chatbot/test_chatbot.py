# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.exceptions import ValidationError


class TestChatbot(FrappeTestCase):
    def tearDown(self):
        frappe.db.rollback()

    def test_create_valid_chatbot(self):
        bot = frappe.get_doc({
            "doctype": "Chatbot",
            "bot_name": "support_agent_01",
            "title": "Support Agent",
            "status": "Draft",
            "default_language": "en",
            "greeting_message": "Hello from Support Agent!",
        }).insert(ignore_permissions=True)

        self.assertEqual(bot.name, "support_agent_01")
        self.assertEqual(bot.status, "Draft")
        self.assertEqual(bot.greeting_message, "Hello from Support Agent!")

    def test_invalid_slug_raises_error(self):
        bot = frappe.get_doc({
            "doctype": "Chatbot",
            "bot_name": "Invalid Slug With Spaces!",
            "title": "Invalid Bot",
            "status": "Draft",
        })
        with self.assertRaises(ValidationError):
            bot.insert(ignore_permissions=True)

    def test_publish_sets_active_status(self):
        bot = frappe.get_doc({
            "doctype": "Chatbot",
            "bot_name": "sales_bot",
            "title": "Sales Bot",
            "status": "Draft",
            "is_published": 1,
        }).insert(ignore_permissions=True)

        self.assertEqual(bot.status, "Active")
