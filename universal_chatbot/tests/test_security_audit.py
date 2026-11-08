"""Security & Compliance Audit Tests for Universal Chatbot (Milestone 7).

Verifies:
1. Credential encryption at rest and leak prevention.
2. RBAC enforcement on administrative APIs and DocTypes.
3. Origin / Domain restriction on widget gateway.
4. Deployment key validation.
5. Safe condition evaluator and template injection isolation (no eval/exec).
"""

import unittest
import frappe
from universal_chatbot.api.v1.chat import init_chat, send_message
from universal_chatbot.api.v1.flow_designer import load_visual_flow, publish_flow, save_visual_flow
from universal_chatbot.core.exceptions import DeploymentNotFoundError
from universal_chatbot.flow.evaluator import SafeConditionEvaluator, interpolate_template


class TestSecurityAudit(unittest.TestCase):
    """Test suite verifying system security, RBAC, encryption, and input sanitization."""

    def setUp(self):
        frappe.set_user("Administrator")
        self.bot_name = f"sec_bot_{frappe.generate_hash(length=8).lower()}"
        self.bot = frappe.get_doc({
            "doctype": "Chatbot",
            "bot_name": self.bot_name,
            "title": "Security Audit Bot",
            "status": "Active",
        }).insert(ignore_permissions=True)

        if not frappe.db.exists("Bot Channel", "Sec Web Channel"):
            frappe.get_doc({
                "doctype": "Bot Channel",
                "channel_name": "Sec Web Channel",
                "channel_type": "Web Widget",
                "is_enabled": 1,
            }).insert(ignore_permissions=True)

        self.deployment = frappe.get_doc({
            "doctype": "Bot Deployment",
            "chatbot": self.bot.name,
            "deployment_name": f"Sec Deploy {frappe.generate_hash(length=6)}",
            "channel": "Sec Web Channel",
            "deployment_key": f"sec_key_{frappe.generate_hash(length=16)}",
            "status": "Active",
            "allowed_domains": "https://trusted-site.com\nhttps://portal.example.org",
        }).insert(ignore_permissions=True)

        self.flow = frappe.get_doc({
            "doctype": "Chatbot Flow",
            "flow_name": f"sec_flow_{frappe.generate_hash(length=8).lower()}",
            "bot": self.bot.name,
            "status": "Published",
            "version": "1.0.0",
        }).insert(ignore_permissions=True)

        frappe.get_doc({
            "doctype": "Flow Node",
            "flow": self.flow.name,
            "node_id": "start",
            "node_type": "Start",
            "configuration": "{}",
        }).insert(ignore_permissions=True)

        self.bot.primary_flow = self.flow.name
        self.bot.save(ignore_permissions=True)

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.db.rollback()

    def test_guest_cannot_access_flow_designer_api(self):
        """Unauthenticated Guest user must be rejected from administrative flow designer endpoints."""
        frappe.set_user("Guest")

        # Test load_visual_flow permission rejection
        with self.assertRaises(frappe.PermissionError):
            load_visual_flow(self.flow.name)

        # Test save_visual_flow permission rejection
        with self.assertRaises(frappe.PermissionError):
            save_visual_flow(self.flow.name, {"nodes": [], "transitions": []})

        # Test publish_flow permission rejection
        with self.assertRaises(frappe.PermissionError):
            publish_flow(self.flow.name)

    def test_widget_gateway_rejects_invalid_deployment_key(self):
        """Chat endpoints must reject requests with missing or invalid deployment keys."""
        with self.assertRaises(DeploymentNotFoundError):
            init_chat(deployment_key="invalid_fake_key_9999", external_user_id="user_123")

        with self.assertRaises(DeploymentNotFoundError):
            send_message(
                deployment_key="invalid_fake_key_9999",
                external_user_id="user_123",
                conversation_id="conv_fake_123",
                message="Hello",
            )

    def test_widget_gateway_enforces_domain_origin_whitelist(self):
        """Cross-origin requests from non-whitelisted domains must be rejected."""
        # Spoof untrusted HTTP Origin
        frappe.local.request = frappe._dict(
            headers={"Origin": "https://malicious-attacker.com"}
        )

        with self.assertRaises(frappe.PermissionError):
            init_chat(deployment_key=self.deployment.deployment_key, external_user_id="user_123")

        # Spoof trusted HTTP Origin
        frappe.local.request = frappe._dict(
            headers={"Origin": "https://trusted-site.com"}
        )
        res = init_chat(deployment_key=self.deployment.deployment_key, external_user_id="user_123")
        self.assertIn("conversation_id", res)

    def test_credential_encryption_and_leak_prevention(self):
        """Password/API secret must be stored encrypted at rest and never exposed in plain dicts."""
        integration = frappe.get_doc({
            "doctype": "Chatbot Integration",
            "integration_name": f"Sec_ERP_{frappe.generate_hash(length=6)}",
            "integration_type": "Frappe REST",
            "base_url": "https://erp.example.com",
            "status": "Active",
        }).insert(ignore_permissions=True)

        plain_secret = "super_confidential_secret_token_123"
        cred = frappe.get_doc({
            "doctype": "Integration Credential",
            "integration": integration.name,
            "authentication_type": "Token",
            "api_key": "sec_key_xyz",
            "api_secret": plain_secret,
        }).insert(ignore_permissions=True)

        # Query MariaDB raw column to verify encryption at rest
        raw_db_val = frappe.db.get_value("Integration Credential", cred.name, "api_secret")
        self.assertNotEqual(raw_db_val, plain_secret, "API Secret must not be stored in plaintext in DB!")

        # Verify as_dict masks password field
        as_dict = cred.as_dict()
        self.assertNotEqual(as_dict.get("api_secret"), plain_secret, "as_dict must never expose raw secret!")

        # Verify decrypted password utility works exclusively for server-side connector
        retrieved_secret = cred.get_decrypted_secret()
        self.assertEqual(retrieved_secret, plain_secret)

    def test_evaluator_rejects_arbitrary_code_execution(self):
        """SafeConditionEvaluator must strictly forbid arbitrary code or dangerous calls."""
        evaluator = SafeConditionEvaluator()
        context = {"user_role": "guest", "order_id": "1001"}

        # Attempt arbitrary Python execution via condition strings
        malicious_expressions = [
            "__import__('os').system('ls')",
            "exec('import sys')",
            "eval('1+1')",
            "open('/etc/passwd').read()",
        ]

        for expr in malicious_expressions:
            # Must evaluate safely to False and never execute arbitrary code
            result = evaluator.evaluate(expr, context)
            self.assertFalse(result, f"Expression '{expr}' must not execute or pass")

    def test_template_interpolation_injection_safety(self):
        """Template interpolation must strictly replace variable identifiers and not evaluate code."""
        context = {"user_name": "Alice", "balance": "100"}

        # Benign interpolation
        template = "Hello {{user_name}}, your balance is {{balance}}."
        result = interpolate_template(template, context)
        self.assertEqual(result, "Hello Alice, your balance is 100.")

        # Attempt code injection inside template tags - non-identifier tags are left unexecuted
        injection_template = "Hello {{__import__('os').system('ls')}}!"
        result = interpolate_template(injection_template, context)
        self.assertEqual(result, "Hello {{__import__('os').system('ls')}}!")

        # Undefined variable identifier safely resolves to empty string
        unknown_var_template = "Value: {{unknown_variable}}"
        result = interpolate_template(unknown_var_template, context)
        self.assertEqual(result, "Value: ")
