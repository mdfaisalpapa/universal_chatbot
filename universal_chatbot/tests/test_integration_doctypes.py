# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import json
import unittest
import frappe


class TestIntegrationDocTypes(unittest.TestCase):
    def setUp(self):
        frappe.set_user("Administrator")
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

    def test_discover_and_import_actions(self):
        from universal_chatbot.api.v1.wizard import (
            discover_remote_actions,
            import_discovered_actions,
            save_integration_action,
        )

        iname = "Test Discovery ERP"
        if frappe.db.exists("Chatbot Integration", iname):
            frappe.delete_doc("Chatbot Integration", iname, force=1, ignore_permissions=True)

        integration = frappe.get_doc({
            "doctype": "Chatbot Integration",
            "integration_name": iname,
            "integration_type": "Frappe REST",
            "base_url": "http://127.0.0.1:8000",
            "status": "Active",
        }).insert(ignore_permissions=True)

        # 1. Discover actions for a standard DocType (Customer)
        res = discover_remote_actions(iname, source_type="frappe", identifier_or_url="Customer")
        self.assertEqual(res.get("status"), "success")
        self.assertGreaterEqual(res.get("candidates_count"), 3)

        candidates = res.get("candidates")
        action_names = [c["action_name"] for c in candidates]
        self.assertIn("get_customer", action_names)
        self.assertIn("list_customer", action_names)
        self.assertIn("create_customer", action_names)

        # Check candidate structure
        get_act = next(c for c in candidates if c["action_name"] == "get_customer")
        self.assertEqual(get_act["method"], "GET")
        self.assertEqual(get_act["operation"], "/api/resource/Customer/{name}")
        self.assertIn("name", get_act["input_schema"].get("required", []))

        # 2. Discover actions for Frappe RPC module (society_erp.api)
        rpc_res = discover_remote_actions(iname, source_type="rpc", identifier_or_url="society_erp.api")
        self.assertEqual(rpc_res.get("status"), "success")
        self.assertGreaterEqual(rpc_res.get("candidates_count"), 1)
        rpc_candidates = rpc_res.get("candidates")
        rpc_action_names = [c["action_name"] for c in rpc_candidates]
        self.assertIn("get_maintenance_dues", rpc_action_names)

        dues_act = next(c for c in rpc_candidates if c["action_name"] == "get_maintenance_dues")
        self.assertEqual(dues_act["method"], "POST")
        self.assertEqual(dues_act["operation"], "/api/method/society_erp.api.get_maintenance_dues")
        self.assertIn("flat_number", dues_act["input_schema"]["properties"])

        # 3. Import discovered actions
        import_res = import_discovered_actions(iname, [get_act, dues_act])
        self.assertEqual(import_res.get("status"), "success")
        self.assertIn("get_customer", import_res.get("imported_actions"))
        self.assertIn("get_maintenance_dues", import_res.get("imported_actions"))

        # Verify persisted action docs
        self.assertTrue(frappe.db.exists("Integration Action", f"{iname}-get_customer"))
        self.assertTrue(frappe.db.exists("Integration Action", f"{iname}-get_maintenance_dues"))
        dues_doc = frappe.get_doc("Integration Action", f"{iname}-get_maintenance_dues")
        self.assertEqual(dues_doc.method, "POST")
        self.assertEqual(dues_doc.operation, "/api/method/society_erp.api.get_maintenance_dues")

        # 4. Update action via save_integration_action with explicit method
        save_integration_action(
            integration=iname,
            action_name="get_customer",
            method="GET",
            operation="/api/resource/Customer/{name}",
            input_schema={"type": "object", "required": ["name"]},
            output_mapping={"name": "name"},
        )
        act_doc = frappe.get_doc("Integration Action", f"{iname}-get_customer")
        self.assertEqual(act_doc.method, "GET")

