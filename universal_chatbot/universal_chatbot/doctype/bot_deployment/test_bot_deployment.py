# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.exceptions import ValidationError


class TestBotDeployment(FrappeTestCase):
    def setUp(self):
        if not frappe.db.exists("Chatbot", "deploy_bot"):
            frappe.get_doc({
                "doctype": "Chatbot",
                "bot_name": "deploy_bot",
                "title": "Deploy Bot",
            }).insert(ignore_permissions=True)

        if not frappe.db.exists("Bot Channel", "Deploy Web Channel"):
            frappe.get_doc({
                "doctype": "Bot Channel",
                "channel_name": "Deploy Web Channel",
                "channel_type": "Web Widget",
            }).insert(ignore_permissions=True)

    def tearDown(self):
        frappe.db.rollback()

    def test_create_bot_deployment_auto_key(self):
        theme = json.dumps({"primaryColor": "#10b981", "title": "Helpdesk"})
        deployment = frappe.get_doc({
            "doctype": "Bot Deployment",
            "deployment_name": "Production Widget",
            "chatbot": "deploy_bot",
            "channel": "Deploy Web Channel",
            "status": "Active",
            "allowed_domains": "https://example.com,https://shop.example.com",
            "theme_config": theme,
        }).insert(ignore_permissions=True)

        self.assertTrue(len(deployment.deployment_key) >= 16)
        self.assertEqual(deployment.status, "Active")
        self.assertEqual(deployment.chatbot, "deploy_bot")

    def test_invalid_theme_json_raises_error(self):
        deployment = frappe.get_doc({
            "doctype": "Bot Deployment",
            "deployment_name": "Broken Theme",
            "chatbot": "deploy_bot",
            "channel": "Deploy Web Channel",
            "theme_config": "not_valid_json",
        })
        with self.assertRaises(ValidationError):
            deployment.insert(ignore_permissions=True)
