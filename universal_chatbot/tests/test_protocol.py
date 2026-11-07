"""Pure Python unit tests for the Common Message Protocol data classes.

Zero external dependencies or database connections.
"""

import unittest
from universal_chatbot.core.protocol import (
    IncomingMessage,
    OutgoingResponse,
    SessionStatus,
    OptionItem,
    MessageRole,
    MessageType,
    EventType,
)


class TestCommonMessageProtocol(unittest.TestCase):
    def test_incoming_message_valid(self):
        msg = IncomingMessage(
            bot_id="bot_123",
            deployment_id="dep_456",
            channel="web",
            external_user_id="user_789",
            message={"message_id": "m1", "type": "text", "text": "Hello bot"},
            metadata={"language": "en", "timezone": "Asia/Kolkata"},
            tenant_id="tenant_abc",
            conversation_id="conv_001",
        )
        self.assertEqual(msg.bot_id, "bot_123")
        self.assertEqual(msg.message["text"], "Hello bot")
        self.assertEqual(msg.metadata["language"], "en")
        self.assertEqual(msg.tenant_id, "tenant_abc")

    def test_incoming_message_create_helper(self):
        msg = IncomingMessage.create(
            bot_id="bot_123",
            deployment_id="dep_456",
            channel="web",
            external_user_id="user_789",
            text="How can I track my order?",
            language="es",
            tz="America/New_York",
            extra_metadata={"client": "browser"},
        )
        self.assertEqual(msg.message["text"], "How can I track my order?")
        self.assertEqual(msg.metadata["language"], "es")
        self.assertEqual(msg.metadata["timezone"], "America/New_York")
        self.assertEqual(msg.metadata["client"], "browser")
        self.assertIsNotNone(msg.message.get("message_id"))

    def test_incoming_message_serialization(self):
        msg = IncomingMessage.create(
            bot_id="bot_1",
            deployment_id="dep_1",
            channel="web",
            external_user_id="u1",
            text="test msg",
            conversation_id="conv_1",
        )
        data = msg.to_dict()
        self.assertEqual(data["bot_id"], "bot_1")
        self.assertEqual(data["conversation_id"], "conv_1")
        self.assertEqual(data["message"]["text"], "test msg")

        restored = IncomingMessage.from_dict(data)
        self.assertEqual(restored.bot_id, msg.bot_id)
        self.assertEqual(restored.message, msg.message)
        self.assertEqual(restored.metadata, msg.metadata)

    def test_incoming_message_missing_required_fields_raises(self):
        with self.assertRaises(ValueError):
            # Missing text in message
            IncomingMessage(
                bot_id="b",
                deployment_id="d",
                channel="c",
                external_user_id="u",
                message={"message_id": "1", "type": "text"},
                metadata={"language": "en", "timezone": "UTC"},
            )

        with self.assertRaises(ValueError):
            # Missing timezone in metadata
            IncomingMessage(
                bot_id="b",
                deployment_id="d",
                channel="c",
                external_user_id="u",
                message={"message_id": "1", "type": "text", "text": "hi"},
                metadata={"language": "en"},
            )

        with self.assertRaises(ValueError):
            # Empty bot_id
            IncomingMessage(
                bot_id="",
                deployment_id="d",
                channel="c",
                external_user_id="u",
                message={"message_id": "1", "type": "text", "text": "hi"},
                metadata={"language": "en", "timezone": "UTC"},
            )

    def test_outgoing_response_valid(self):
        resp = OutgoingResponse(
            conversation_id="conv_100",
            response={"type": "text", "text": "Your order #123 is on the way."},
            actions=[{"type": "link", "url": "https://track.example.com"}],
            session_status=SessionStatus.ACTIVE.value,
        )
        self.assertEqual(resp.conversation_id, "conv_100")
        self.assertEqual(resp.response["text"], "Your order #123 is on the way.")
        self.assertEqual(len(resp.actions), 1)
        self.assertEqual(resp.session_status, "active")

    def test_outgoing_response_create_helper(self):
        resp = OutgoingResponse.create(
            conversation_id="conv_101",
            text="Please select an option",
            response_type="options",
            actions=[{"type": "quick_reply", "text": "Yes"}],
            session_status="paused",
        )
        self.assertEqual(resp.response["type"], "options")
        self.assertEqual(resp.session_status, "paused")

    def test_outgoing_response_serialization(self):
        resp = OutgoingResponse.create(
            conversation_id="conv_102",
            text="Session complete",
            session_status=SessionStatus.COMPLETED.value,
        )
        data = resp.to_dict()
        self.assertEqual(data["conversation_id"], "conv_102")
        self.assertEqual(data["session_status"], "completed")

        restored = OutgoingResponse.from_dict(data)
        self.assertEqual(restored.conversation_id, resp.conversation_id)
        self.assertEqual(restored.response, resp.response)
        self.assertEqual(restored.session_status, resp.session_status)

    def test_outgoing_response_validation_errors(self):
        with self.assertRaises(ValueError):
            # Missing text in response dict
            OutgoingResponse(
                conversation_id="c1",
                response={"type": "text"},
                actions=[],
                session_status="active",
            )

        with self.assertRaises(ValueError):
            # Non-list actions
            OutgoingResponse(
                conversation_id="c1",
                response={"type": "text", "text": "ok"},
                actions="not-a-list",  # type: ignore
                session_status="active",
            )


if __name__ == "__main__":
    unittest.main()
