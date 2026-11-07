# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from universal_chatbot.universal_chatbot.doctype.bot_settings.bot_settings import get_bot_settings


class TestBotSettings(FrappeTestCase):
    def test_bot_settings_retrieval(self):
        settings = get_bot_settings()
        self.assertIsNotNone(settings)
        self.assertIn(settings.log_level, ["DEBUG", "INFO", "WARNING", "ERROR"])
