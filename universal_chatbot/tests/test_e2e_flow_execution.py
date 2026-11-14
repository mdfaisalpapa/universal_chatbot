"""Formal Frappe End-to-End Flow Execution Integration Test.

Packages the full conversation simulation from run_e2e_demo.py into a repeatable,
hermetic Frappe test case with mocked external HTTP REST calls.
Verifies:
1. Multi-step conversation orchestration (Welcome -> Ask Question -> Paused -> User Input -> Call Action -> Template Interpolation).
2. Action Execution record logging with input/output payloads and execution timing.
3. Flow execution for both Owner-Occupied (TB2-203) and Tenant-Occupied (TA1-203) scenarios.
"""

from unittest.mock import MagicMock, patch
import unittest
import frappe
from universal_chatbot.api.v1.chat import init_chat, send_message


class TestE2EFlowExecution(unittest.TestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        self.deployment_key = "kvc3_web_live_demo_key"
        self.ensure_kvc3_fixtures()

    def ensure_kvc3_fixtures(self):
        """Ensure test bot, deployment, and channel are configured."""
        if not frappe.db.exists("Chatbot", "kvc3_bot"):
            frappe.get_doc({
                "doctype": "Chatbot",
                "bot_name": "kvc3_bot",
                "title": "KVC3 Test Bot",
                "status": "Active",
            }).insert(ignore_permissions=True)

        if not frappe.db.exists("Bot Channel", "Website Channel"):
            frappe.get_doc({
                "doctype": "Bot Channel",
                "channel_name": "Website Channel",
                "channel_type": "Web Widget",
                "is_enabled": 1,
            }).insert(ignore_permissions=True)

        dep_name = frappe.db.get_value("Bot Deployment", {"deployment_key": self.deployment_key}, "name")
        if not dep_name:
            frappe.get_doc({
                "doctype": "Bot Deployment",
                "deployment_name": "KVC3 Portal Assistant",
                "chatbot": "kvc3_bot",
                "channel": "Website Channel",
                "deployment_key": self.deployment_key,
                "status": "Active",
                "allowed_domains": "*",
            }).insert(ignore_permissions=True)
        else:
            dep = frappe.get_doc("Bot Deployment", dep_name)
            dep.status = "Active"
            dep.allowed_domains = "*"
            dep.chatbot = "kvc3_bot"
            dep.save(ignore_permissions=True)

    @patch("universal_chatbot.connectors.rest.frappe_connector.FrappeRestConnector.execute")
    def test_e2e_owner_occupied_flow(self, mock_execute):
        """Simulate resident TB2-203 checking maintenance dues (Owner Occupied)."""
        # Mock external ERP response from kvc3.local
        mock_execute.return_value = {
            "owner_name": "PRAVEEN KUMAR",
            "flat_details": "B2 Block, 2 BHK, 1133 sqft",
            "tenant_name": "None (Owner Occupied)",
            "outstanding_amount": "2,940.00",
        }

        user_id = "test_resident_tb2_203"

        # Step 1: User initiates chat
        init_res = init_chat(
            deployment_key=self.deployment_key,
            external_user_id=user_id,
        )
        self.assertEqual(init_res["status"], "success")
        self.assertIn("conversation_id", init_res)
        conv_id = init_res["conversation_id"]

        # Bot greeted user and paused at question
        messages = [m.get("text", "") for m in init_res.get("messages", [])]
        self.assertTrue(any("Apartment Maintenance Assistant" in t for t in messages))
        self.assertEqual(init_res.get("session_status"), "paused")
        self.assertEqual(init_res.get("current_node_id"), "ask_flat_node")

        # Step 2: User responds with flat number
        msg_res = send_message(
            deployment_key=self.deployment_key,
            external_user_id=user_id,
            conversation_id=conv_id,
            message="TB2-203",
        )
        self.assertEqual(msg_res["status"], "success")

        # Verify connector was called with flat_number
        mock_execute.assert_called()
        call_args = mock_execute.call_args[0]
        self.assertEqual(call_args[0], "get_maintenance_dues")
        self.assertEqual(call_args[1], {"flat_number": "TB2-203"})

        # Check outbound message formatting
        outbound = [m.get("text", "") for m in msg_res.get("messages", [])]
        self.assertTrue(any("details for flat TB2-203:" in t for t in outbound))
        self.assertTrue(any("👤 Owner: PRAVEEN KUMAR" in t for t in outbound))
        self.assertTrue(any("🏢 Details: B2 Block, 2 BHK, 1133 sqft" in t for t in outbound))
        self.assertTrue(any("👥 Tenant: None (Owner Occupied)" in t for t in outbound))
        self.assertTrue(any("💰 Outstanding Dues: ₹ 2,940.00" in t for t in outbound))

        # Verify Action Execution record created in database
        action_executions = frappe.get_all(
            "Action Execution",
            filters={"conversation": conv_id},
            fields=["name", "action", "status", "execution_time", "input_payload", "output_payload"],
        )
        self.assertGreaterEqual(len(action_executions), 1)
        ae = action_executions[0]
        self.assertEqual(ae.status, "Success")
        self.assertIn("TB2-203", ae.input_payload)
        self.assertIn("2,940.00", ae.output_payload)

    @patch("universal_chatbot.connectors.rest.frappe_connector.FrappeRestConnector.execute")
    def test_e2e_tenant_occupied_flow(self, mock_execute):
        """Simulate resident TA1-203 checking maintenance dues (Tenant Occupied)."""
        mock_execute.return_value = {
            "owner_name": "B BALAJI",
            "flat_details": "A1 Block, 1 BHK, 579 sqft",
            "tenant_name": "Mr. Devilal Reddy (Active)",
            "outstanding_amount": "1,555.00",
        }

        user_id = "test_resident_ta1_203"

        # Step 1: Init chat
        init_res = init_chat(
            deployment_key=self.deployment_key,
            external_user_id=user_id,
        )
        conv_id = init_res["conversation_id"]

        # Step 2: Send flat number
        msg_res = send_message(
            deployment_key=self.deployment_key,
            external_user_id=user_id,
            conversation_id=conv_id,
            message="TA1-203",
        )
        self.assertEqual(msg_res["status"], "success")

        outbound = [m.get("text", "") for m in msg_res.get("messages", [])]
        self.assertTrue(any("details for flat TA1-203:" in t for t in outbound))
        self.assertTrue(any("👤 Owner: B BALAJI" in t for t in outbound))
        self.assertTrue(any("🏢 Details: A1 Block, 1 BHK, 579 sqft" in t for t in outbound))
        self.assertTrue(any("👥 Tenant: Mr. Devilal Reddy (Active)" in t for t in outbound))
        self.assertTrue(any("💰 Outstanding Dues: ₹ 1,555.00" in t for t in outbound))
