# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.tests.utils import FrappeTestCase
from universal_chatbot.api.v1.chat import init_chat, send_message, validate_deployment_origin
from universal_chatbot.core.exceptions import DeploymentNotFoundError


class TestChatAPI(FrappeTestCase):
    def setUp(self):
        # 1. Setup Chatbot
        if not frappe.db.exists("Chatbot", "api_bot"):
            frappe.get_doc({
                "doctype": "Chatbot",
                "bot_name": "api_bot",
                "title": "API Helpdesk Bot",
                "status": "Active",
                "greeting_message": "Hello from API Bot!",
            }).insert(ignore_permissions=True)

        # 2. Setup Bot Channel
        if not frappe.db.exists("Bot Channel", "API Web Channel"):
            frappe.get_doc({
                "doctype": "Bot Channel",
                "channel_name": "API Web Channel",
                "channel_type": "Web Widget",
                "is_enabled": 1,
            }).insert(ignore_permissions=True)

        # 3. Setup Bot Deployment with restricted CORS domain
        self.deployment = frappe.get_doc({
            "doctype": "Bot Deployment",
            "deployment_name": "API Widget Deploy",
            "chatbot": "api_bot",
            "channel": "API Web Channel",
            "status": "Active",
            "allowed_domains": "https://trusted-site.com,http://localhost:8000",
            "theme_config": json.dumps({"primaryColor": "#3b82f6"}),
        }).insert(ignore_permissions=True)

        # 4. Setup Flow for Bot
        if not frappe.db.exists("Chatbot Flow", "api_bot-support"):
            self.flow = frappe.get_doc({
                "doctype": "Chatbot Flow",
                "bot": "api_bot",
                "flow_name": "support",
                "status": "Published",
                "version": "1.0.0",
            }).insert(ignore_permissions=True)

            # Node 1: Start
            n1 = frappe.get_doc({
                "doctype": "Flow Node",
                "flow": self.flow.name,
                "node_id": "start",
                "node_type": "Start",
                "configuration": json.dumps({"message": "Welcome to API support!"}),
            }).insert(ignore_permissions=True)

            # Node 2: Ask Question
            n2 = frappe.get_doc({
                "doctype": "Flow Node",
                "flow": self.flow.name,
                "node_id": "ask_query",
                "node_type": "Ask Question",
                "configuration": json.dumps({
                    "question": "How can we help you today?",
                    "save_to_variable": "user_query",
                }),
            }).insert(ignore_permissions=True)

            # Node 3: End
            n3 = frappe.get_doc({
                "doctype": "Flow Node",
                "flow": self.flow.name,
                "node_id": "finish",
                "node_type": "End",
                "configuration": json.dumps({"message": "We have recorded your query: {user_query}. Goodbye!"}),
            }).insert(ignore_permissions=True)

            # Transitions
            frappe.get_doc({
                "doctype": "Flow Transition",
                "source_node": n1.name,
                "target_node": n2.name,
            }).insert(ignore_permissions=True)

            frappe.get_doc({
                "doctype": "Flow Transition",
                "source_node": n2.name,
                "target_node": n3.name,
            }).insert(ignore_permissions=True)

    def tearDown(self):
        frappe.db.rollback()

    def test_init_chat_bootstrap_and_state_preservation(self):
        ext_user_id = "test_browser_user_001"

        # 1. Initialize chat session
        res = init_chat(
            deployment_key=self.deployment.deployment_key,
            external_user_id=ext_user_id,
        )

        self.assertEqual(res["status"], "success")
        self.assertIsNotNone(res["conversation_id"])
        self.assertEqual(res["bot_title"], "API Helpdesk Bot")
        self.assertEqual(res["session_status"], "paused")
        self.assertEqual(res["current_node_id"], "ask_query")
        self.assertGreaterEqual(len(res["messages"]), 2)
        conv_id = res["conversation_id"]

        # 2. Reconnect with existing conversation_id (simulate browser refresh)
        refresh_res = init_chat(
            deployment_key=self.deployment.deployment_key,
            external_user_id=ext_user_id,
            conversation_id=conv_id,
        )

        self.assertEqual(refresh_res["status"], "success")
        self.assertEqual(refresh_res["conversation_id"], conv_id)
        # Message history is preserved
        self.assertGreaterEqual(len(refresh_res["messages"]), 2)

    def test_send_message_flow_transition(self):
        ext_user_id = "test_browser_user_002"

        init_res = init_chat(
            deployment_key=self.deployment.deployment_key,
            external_user_id=ext_user_id,
        )
        conv_id = init_res["conversation_id"]

        # User replies to "ask_query"
        msg_res = send_message(
            deployment_key=self.deployment.deployment_key,
            external_user_id=ext_user_id,
            conversation_id=conv_id,
            message="Need help with billing invoice",
        )

        self.assertEqual(msg_res["status"], "success")
        self.assertEqual(msg_res["session_status"], "completed")
        self.assertIn("billing invoice", msg_res["response"]["text"])

        # Check conversation marked Closed upon completion
        conv = frappe.get_doc("Chat Conversation", conv_id)
        self.assertEqual(conv.status, "Closed")

    def test_reject_invalid_deployment_key(self):
        with self.assertRaises(DeploymentNotFoundError):
            init_chat(
                deployment_key="non_existent_key_999",
                external_user_id="user_any",
            )

    def test_cors_origin_validation(self):
        # 1. Trusted origin succeeds
        validate_deployment_origin(self.deployment, {"Origin": "https://trusted-site.com"})

        # 2. Untrusted origin is rejected with PermissionError
        with self.assertRaises(frappe.PermissionError):
            validate_deployment_origin(self.deployment, {"Origin": "https://malicious-site.com"})
