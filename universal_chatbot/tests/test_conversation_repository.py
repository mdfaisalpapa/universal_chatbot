# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from universal_chatbot.adapters.frappe_repository import FrappeConversationRepository
from universal_chatbot.core.exceptions import SecurityValidationError


class TestConversationRepository(FrappeTestCase):
    def setUp(self):
        self.repo = FrappeConversationRepository()

        if not frappe.db.exists("Chatbot", "repo_bot"):
            frappe.get_doc({
                "doctype": "Chatbot",
                "bot_name": "repo_bot",
                "title": "Repo Bot",
            }).insert(ignore_permissions=True)

        if not frappe.db.exists("Bot Channel", "Repo Channel"):
            frappe.get_doc({
                "doctype": "Bot Channel",
                "channel_name": "Repo Channel",
                "channel_type": "Web Widget",
            }).insert(ignore_permissions=True)

        self.deployment = frappe.get_doc({
            "doctype": "Bot Deployment",
            "deployment_name": "Repo Deploy",
            "chatbot": "repo_bot",
            "channel": "Repo Channel",
        }).insert(ignore_permissions=True)

    def tearDown(self):
        frappe.db.rollback()

    def test_contact_and_channel_identity_flow(self):
        # 1. Create contact
        contact = self.repo.get_or_create_contact(
            display_name="Sarah Connor",
            email="sarah@example.com",
            phone="+1987654321",
        )
        self.assertTrue(contact["name"].startswith("CONT-"))

        # 2. Map channel identity explicitly
        ident = self.repo.get_or_create_channel_identity(
            contact_id=contact["name"],
            channel="web",
            external_user_id="sarah_ext_1",
            verification_status="Verified",
        )
        self.assertEqual(ident["name"], "web:sarah_ext_1")

        # 3. Lookup contact by identity
        found_contact = self.repo.get_contact_by_channel_identity("web", "sarah_ext_1")
        self.assertIsNotNone(found_contact)
        self.assertEqual(found_contact["name"], contact["name"])

        # 4. Identity collision test across different contacts
        another_contact = self.repo.get_or_create_contact(display_name="John Doe")
        with self.assertRaises(SecurityValidationError):
            self.repo.get_or_create_channel_identity(
                contact_id=another_contact["name"],
                channel="web",
                external_user_id="sarah_ext_1",  # already mapped to Sarah
            )

    def test_conversation_lifecycle_and_state(self):
        contact = self.repo.get_or_create_contact(display_name="Bob")
        conv = self.repo.create_conversation(
            bot="repo_bot",
            deployment=self.deployment.name,
            contact=contact["name"],
            channel="web",
        )
        conv_id = conv["name"]
        self.assertTrue(conv_id.startswith("CONV-"))

        # Save state
        saved = self.repo.save_state(
            conversation_id=conv_id,
            current_node="ask_feedback",
            variables={"rating": 5},
            context={"step": 2},
        )
        self.assertEqual(saved["current_node"], "ask_feedback")
        self.assertEqual(saved["variables"]["rating"], 5)

        # Retrieve state
        loaded = self.repo.get_state(conv_id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["current_node"], "ask_feedback")
        self.assertEqual(loaded["variables"]["rating"], 5)
        self.assertEqual(loaded["context"]["step"], 2)

        # Update state partially
        updated = self.repo.save_state(
            conversation_id=conv_id,
            current_node="end_node",
            variables={"rating": 5, "comment": "Great!"},
        )
        self.assertEqual(updated["current_node"], "end_node")
        self.assertEqual(updated["variables"]["comment"], "Great!")

        # Status update
        self.repo.update_conversation_status(conv_id, "Closed")
        reloaded_conv = self.repo.get_conversation(conv_id)
        self.assertEqual(reloaded_conv["status"], "Closed")

    def test_messaging_and_events(self):
        contact = self.repo.get_or_create_contact(display_name="Charlie")
        conv = self.repo.create_conversation(
            bot="repo_bot",
            deployment=self.deployment.name,
            contact=contact["name"],
            channel="web",
        )
        conv_id = conv["name"]

        # Log inbound message
        in_msg = self.repo.log_message(
            conversation_id=conv_id,
            direction="Inbound",
            message_type="Text",
            content="Hello support",
            external_message_id="msg_ext_123",
        )
        self.assertEqual(in_msg["direction"], "Inbound")

        # Log outbound message
        out_msg = self.repo.log_message(
            conversation_id=conv_id,
            direction="Outbound",
            message_type="Text",
            content="Hello Charlie, how can I help?",
        )
        self.assertEqual(out_msg["direction"], "Outbound")

        # Get messages
        messages = self.repo.get_messages(conv_id)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["content"], "Hello support")
        self.assertEqual(messages[1]["content"], "Hello Charlie, how can I help?")

        # Record events
        self.repo.record_event(
            conversation_id=conv_id,
            event_type="conversation_started",
            details={"ip": "127.0.0.1"},
        )
        self.repo.record_event(
            conversation_id=conv_id,
            event_type="node_execution",
            details={"node": "welcome"},
        )

        events = self.repo.get_events(conv_id)
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]["event_type"], "conversation_started")
        self.assertEqual(events[0]["details"]["ip"], "127.0.0.1")
        self.assertEqual(events[1]["event_type"], "node_execution")
