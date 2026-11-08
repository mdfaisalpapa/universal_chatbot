"""Pure Python unit tests for WebChannelAdapter.

Verifies bidirectional translation between HTTP JSON payloads and the
common message protocol without Frappe imports.
"""

import unittest
from universal_chatbot.channels.web.adapter import WebChannelAdapter
from universal_chatbot.core.exceptions import SecurityValidationError
from universal_chatbot.core.protocol import IncomingMessage, OutgoingResponse, SessionStatus


class TestWebChannelAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = WebChannelAdapter()

    def test_normalize_message_valid_payload(self):
        raw_payload = {
            "deployment_key": "dep_secret_123",
            "external_user_id": "usr_browser_456",
            "conversation_id": "conv_789",
            "bot_id": "support_bot",
            "content": "Hello, I need assistance",
            "metadata": {"language": "en", "timezone": "Europe/London"},
        }
        headers = {
            "origin": "https://client-store.com",
            "user-agent": "Mozilla/5.0",
        }

        incoming = self.adapter.normalize_message(raw_payload, headers)

        self.assertIsInstance(incoming, IncomingMessage)
        self.assertEqual(incoming.deployment_id, "dep_secret_123")
        self.assertEqual(incoming.external_user_id, "usr_browser_456")
        self.assertEqual(incoming.conversation_id, "conv_789")
        self.assertEqual(incoming.channel, "web")
        self.assertEqual(incoming.message["text"], "Hello, I need assistance")
        self.assertEqual(incoming.metadata["language"], "en")
        self.assertEqual(incoming.metadata["origin"], "https://client-store.com")

    def test_normalize_message_missing_deployment_key_raises(self):
        raw_payload = {
            "external_user_id": "usr_456",
            "content": "Hello",
        }
        with self.assertRaises(SecurityValidationError):
            self.adapter.normalize_message(raw_payload)

    def test_normalize_message_missing_user_id_raises(self):
        raw_payload = {
            "deployment_key": "dep_123",
            "content": "Hello",
        }
        with self.assertRaises(SecurityValidationError):
            self.adapter.normalize_message(raw_payload)

    def test_format_response_from_outgoing_response(self):
        resp = OutgoingResponse.create(
            conversation_id="conv_100",
            text="How can I help you?",
            response_type="text",
            actions=[{"type": "quick_reply", "label": "Orders", "value": "orders"}],
            session_status=SessionStatus.ACTIVE.value,
        )

        formatted = self.adapter.format_response(resp)

        self.assertEqual(formatted["status"], "success")
        self.assertEqual(formatted["conversation_id"], "conv_100")
        self.assertEqual(formatted["session_status"], "active")
        self.assertEqual(formatted["response"]["text"], "How can I help you?")
        self.assertEqual(len(formatted["actions"]), 1)
        self.assertEqual(formatted["actions"][0]["value"], "orders")

    def test_format_response_from_flow_result_dict(self):
        flow_dict = {
            "conversation_id": "conv_200",
            "status": "paused",
            "current_node_id": "ask_choice",
            "messages": [
                {
                    "type": "options",
                    "text": "Select department:",
                    "options": [{"label": "Sales", "value": "sales"}],
                }
            ],
            "variables": {"step": 2},
            "context": {},
        }

        formatted = self.adapter.format_response(flow_dict)

        self.assertEqual(formatted["status"], "success")
        self.assertEqual(formatted["conversation_id"], "conv_200")
        self.assertEqual(formatted["session_status"], "paused")
        self.assertEqual(formatted["current_node_id"], "ask_choice")
        self.assertEqual(formatted["response"]["text"], "Select department:")
        self.assertEqual(len(formatted["actions"]), 1)
        self.assertEqual(formatted["actions"][0]["value"], "sales")


if __name__ == "__main__":
    unittest.main()
