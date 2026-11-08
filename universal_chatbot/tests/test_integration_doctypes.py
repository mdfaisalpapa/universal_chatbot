# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.tests.utils import FrappeTestCase


class TestIntegrationDocTypes(FrappeTestCase):
    def tearDown(self):
        frappe.db.rollback()

    def test_integration_and_encrypted_credential(self):
        # 1. Create Integration
        integration = frappe.get_doc({
            "doctype": "Chatbot Integration",
            "integration_name": "ERPNext Production",
            "integration_type": "Frappe REST",
            "base_url": "https://erp.example.com/",
            "status": "Active",
        }).insert(ignore_permissions=True)

        self.assertEqual(integration.name, "ERPNext Production")
        self.assertEqual(integration.base_url, "https://erp.example.com")  # trailing slash stripped

        # 2. Create Credential with sensitive api_secret
        cred = frappe.get_doc({
            "doctype": "Integration Credential",
            "integration": integration.name,
            "authentication_type": "Token",
            "api_key": "api_key_public_123",
            "api_secret": "super_secret_token_xyz_456",
        }).insert(ignore_permissions=True)

        self.assertEqual(cred.name, f"CRED-{integration.name}")

        # 3. Security Check: verify DB storage is encrypted and not plaintext
        raw_db_val = frappe.db.sql(
            "SELECT api_secret FROM `tabIntegration Credential` WHERE name = %s",
            cred.name,
        )[0][0]
        self.assertNotEqual(raw_db_val, "super_secret_token_xyz_456")
        self.assertNotEqual(raw_db_val, "")

        # 4. Security Check: standard as_dict() redacts/masks password and never returns plaintext
        cred_dict = cred.as_dict()
        self.assertNotEqual(cred_dict.get("api_secret"), "super_secret_token_xyz_456")
        self.assertTrue(
            cred_dict.get("api_secret") is None
            or set(str(cred_dict.get("api_secret"))) == {"*"}
        )

        # 5. Decryption only occurs via authenticated backend helper
        decrypted = cred.get_decrypted_secret()
        self.assertEqual(decrypted, "super_secret_token_xyz_456")

    def test_integration_action_and_execution_logging(self):
        integration = frappe.get_doc({
            "doctype": "Chatbot Integration",
            "integration_name": "Generic CRM API",
            "integration_type": "Generic REST",
            "base_url": "https://crm.example.com",
            "status": "Active",
        }).insert(ignore_permissions=True)

        action = frappe.get_doc({
            "doctype": "Integration Action",
            "integration": integration.name,
            "action_name": "get_customer",
            "operation": "/api/v1/customers/{customer_id}",
            "input_schema": json.dumps({"required": ["customer_id"]}),
            "output_mapping": json.dumps({"customer_name": "data.name"}),
        }).insert(ignore_permissions=True)

        self.assertEqual(action.name, f"{integration.name}-get_customer")

        # Action execution log (must not store sensitive payload data)
        # Setup conversation
        if not frappe.db.exists("Chatbot", "action_log_bot"):
            frappe.get_doc({
                "doctype": "Chatbot",
                "bot_name": "action_log_bot",
                "title": "Action Bot",
            }).insert(ignore_permissions=True)

        if not frappe.db.exists("Bot Channel", "Action Log Channel"):
            frappe.get_doc({
                "doctype": "Bot Channel",
                "channel_name": "Action Log Channel",
                "channel_type": "Web Widget",
            }).insert(ignore_permissions=True)

        dep = frappe.get_doc({
            "doctype": "Bot Deployment",
            "deployment_name": "Action Log Deploy",
            "chatbot": "action_log_bot",
            "channel": "Action Log Channel",
        }).insert(ignore_permissions=True)

        contact = frappe.get_doc({
            "doctype": "Chat Contact",
            "display_name": "Action User",
        }).insert(ignore_permissions=True)

        conv = frappe.get_doc({
            "doctype": "Chat Conversation",
            "bot": "action_log_bot",
            "deployment": dep.name,
            "contact": contact.name,
            "channel": "web",
        }).insert(ignore_permissions=True)

        exec_doc = frappe.get_doc({
            "doctype": "Action Execution",
            "action": action.name,
            "conversation": conv.name,
            "status": "Success",
            "execution_time": 0.145,
        }).insert(ignore_permissions=True)

        self.assertTrue(exec_doc.name.startswith("ACTX-"))
        self.assertEqual(exec_doc.status, "Success")
        # Ensure no sensitive output payload field exists in doc definition
        self.assertFalse(hasattr(exec_doc, "output_data"))
        self.assertFalse(hasattr(exec_doc, "response_payload"))
