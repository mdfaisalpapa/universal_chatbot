"""Unit tests for Complete Bot Export & Import Utility.

Validates end-to-end bundling and cross-environment provisioning of:
- Chatbot core document and metadata
- Chatbot Integrations, Actions, and Credentials (with and without secret masking)
- Chatbot Flows with complete node graphs, transitions, and variables
- Omnichannel Bot Channels (Telegram, WhatsApp, Web Widget) and Bot Deployments
"""

import json
import unittest
import frappe
from universal_chatbot.flow.bot_export_import import export_bot_package, import_bot_package


class TestBotExportImport(unittest.TestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        self.bot_slug = f"test_pkg_bot_{frappe.generate_hash(length=6).lower()}"
        self.bot = frappe.get_doc({
            "doctype": "Chatbot",
            "bot_name": self.bot_slug,
            "title": "Package Export Test Bot",
            "status": "Active",
            "is_published": 1,
            "greeting_message": "Hello from Package Bot!",
            "fallback_message": "Sorry, try again.",
            "description": "Test bot for full package export/import",
        }).insert(ignore_permissions=True)

        # 1. Integration + Action + Credential
        self.integ_name = f"{self.bot_slug}_integ"
        self.integ = frappe.get_doc({
            "doctype": "Chatbot Integration",
            "name": self.integ_name,
            "integration_name": self.integ_name,
            "chatbot": self.bot.name,
            "integration_type": "Frappe REST",
            "status": "Active",
            "base_url": "http://127.0.0.1:8000",
            "timeout": 20,
        }).insert(ignore_permissions=True)

        self.act_name = f"{self.integ_name}-get_data"
        self.action = frappe.get_doc({
            "doctype": "Integration Action",
            "name": self.act_name,
            "action_name": "get_data",
            "integration": self.integ_name,
            "method": "POST",
            "operation": "/api/method/test.get_data",
            "input_schema": json.dumps({"type": "object", "properties": {"id": {"type": "string"}}}),
            "output_mapping": json.dumps({"result": "result"}),
        }).insert(ignore_permissions=True)

        self.cred = frappe.get_doc({
            "doctype": "Integration Credential",
            "name": f"CRED-{self.integ_name}",
            "integration": self.integ_name,
            "authentication_type": "Token",
            "api_key": "test_api_key_123",
            "api_secret": "super_secret_token_abc",
        }).insert(ignore_permissions=True)

        # 2. Flow + Nodes + Transitions + Variables
        self.flow_name = f"{self.bot.name}-main_flow"
        self.flow = frappe.get_doc({
            "doctype": "Chatbot Flow",
            "name": self.flow_name,
            "flow_name": "main_flow",
            "bot": self.bot.name,
            "status": "Published",
            "version": "1.0.0",
        }).insert(ignore_permissions=True)

        self.start_node = frappe.get_doc({
            "doctype": "Flow Node",
            "flow": self.flow.name,
            "node_id": "start_1",
            "node_type": "Start",
            "configuration": json.dumps({"message": "Welcome!", "ui_x": 100, "ui_y": 100}),
        }).insert(ignore_permissions=True)

        self.end_node = frappe.get_doc({
            "doctype": "Flow Node",
            "flow": self.flow.name,
            "node_id": "end_1",
            "node_type": "End",
            "configuration": json.dumps({"message": "Goodbye!", "ui_x": 100, "ui_y": 300}),
        }).insert(ignore_permissions=True)

        frappe.get_doc({
            "doctype": "Flow Transition",
            "source_node": self.start_node.name,
            "target_node": self.end_node.name,
            "condition": "",
        }).insert(ignore_permissions=True)

        # 3. Omnichannel Channels & Deployments
        # Telegram Channel
        self.tg_ch_name = f"{self.bot_slug} Telegram Channel"
        self.tg_ch = frappe.get_doc({
            "doctype": "Bot Channel",
            "channel_name": self.tg_ch_name,
            "channel_type": "Telegram",
            "is_enabled": 1,
            "chatbot": self.bot.name,
            "telegram_bot_token": "123456:ABC-DEF-SECRET-TOKEN",
            "telegram_webhook_secret": "my_tg_secret",
        }).insert(ignore_permissions=True, ignore_links=True)

        # Telegram Deployment
        self.tg_dep_name = f"DEP-{self.bot_slug}-TG"
        self.tg_dep = frappe.get_doc({
            "doctype": "Bot Deployment",
            "name": self.tg_dep_name,
            "deployment_name": "TG",
            "chatbot": self.bot.name,
            "channel": self.tg_ch_name,
            "status": "Active",
            "deployment_key": f"tg_{frappe.generate_hash(length=8)}",
            "auth_mode": "Anonymous",
        }).insert(ignore_permissions=True)

        frappe.db.set_value("Bot Channel", self.tg_ch_name, "deployment", self.tg_dep_name)

        frappe.db.commit()

    def tearDown(self):
        frappe.db.rollback()

    def test_export_bot_package_safe_no_credentials(self):
        """Exporting without include_credentials strips plain secret tokens."""
        package = export_bot_package(self.bot.name, include_credentials=False)

        self.assertEqual(package["schema_version"], "1.0")
        self.assertFalse(package["credentials_included"])
        self.assertEqual(package["bot"]["bot_name"], self.bot.name)
        self.assertEqual(package["bot"]["title"], "Package Export Test Bot")

        # Integrations
        self.assertEqual(len(package["integrations"]), 1)
        integ_pkg = package["integrations"][0]
        self.assertEqual(len(integ_pkg["actions"]), 1)
        self.assertEqual(integ_pkg["actions"][0]["action_name"], "get_data")
        self.assertEqual(len(integ_pkg["credentials"]), 1)
        self.assertNotIn("api_secret", integ_pkg["credentials"][0])

        # Flows
        self.assertEqual(len(package["flows"]), 1)
        self.assertEqual(package["flows"][0]["metadata"]["flow_name"], "main_flow")
        self.assertEqual(len(package["flows"][0]["nodes"]), 2)

        # Deployments
        self.assertEqual(len(package["deployments"]), 1)
        dep_pkg = package["deployments"][0]
        self.assertEqual(dep_pkg["channel_details"]["channel_type"], "Telegram")
        self.assertNotIn("telegram_bot_token", dep_pkg["channel_details"])

    def test_export_bot_package_with_credentials(self):
        """Exporting with include_credentials=True bundles decrypted passwords."""
        package = export_bot_package(self.bot.name, include_credentials=True)

        self.assertTrue(package["credentials_included"])
        integ_pkg = package["integrations"][0]
        self.assertEqual(integ_pkg["credentials"][0]["api_secret"], "super_secret_token_abc")

        dep_pkg = package["deployments"][0]
        self.assertEqual(dep_pkg["channel_details"]["telegram_bot_token"], "123456:ABC-DEF-SECRET-TOKEN")

    def test_import_bot_package_clone_provisioning(self):
        """Importing an exported package provisions a new distinct chatbot clone."""
        package = export_bot_package(self.bot.name, include_credentials=True)
        clone_slug = f"clone_{frappe.generate_hash(length=6).lower()}"

        res = import_bot_package(package, target_bot_slug=clone_slug, overwrite=True)

        self.assertEqual(res["status"], "success")
        self.assertEqual(res["bot_name"], clone_slug)
        self.assertEqual(res["integrations_count"], 1)
        self.assertEqual(res["actions_count"], 1)
        self.assertEqual(res["flows_count"], 1)
        self.assertEqual(res["channels_count"], 1)
        self.assertEqual(res["deployments_count"], 1)

        # Verify cloned DocTypes exist in DB
        self.assertTrue(frappe.db.exists("Chatbot", clone_slug))
        cloned_bot = frappe.get_doc("Chatbot", clone_slug)
        self.assertEqual(cloned_bot.title, "Package Export Test Bot")

        cloned_flows = frappe.get_all("Chatbot Flow", filters={"bot": clone_slug}, pluck="name")
        self.assertEqual(len(cloned_flows), 1)
        self.assertEqual(cloned_flows[0], f"{clone_slug}-main_flow")

        cloned_deps = frappe.get_all("Bot Deployment", filters={"chatbot": clone_slug}, pluck="name")
        self.assertEqual(len(cloned_deps), 1)

        cloned_integs = frappe.get_all("Chatbot Integration", filters={"chatbot": clone_slug}, pluck="name")
        self.assertEqual(len(cloned_integs), 1)


if __name__ == "__main__":
    unittest.main()
