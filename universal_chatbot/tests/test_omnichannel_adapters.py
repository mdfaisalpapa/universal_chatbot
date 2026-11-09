"""Unit tests for Omnichannel Adapters (Telegram & WhatsApp) and Channel Gateway.

Pure Python unit tests validating normalization, response formatting, and gateway routing
without requiring Frappe runtime dependencies.
"""

import unittest
from unittest.mock import MagicMock, patch
from universal_chatbot.channels.base import BaseChannelAdapter
from universal_chatbot.channels.gateway import ChannelGateway, get_channel_gateway
from universal_chatbot.channels.telegram.adapter import TelegramChannelAdapter
from universal_chatbot.channels.whatsapp.adapter import WhatsAppChannelAdapter
from universal_chatbot.core.exceptions import SecurityValidationError
from universal_chatbot.core.protocol import IncomingMessage, OutgoingResponse, SessionStatus


class TestTelegramChannelAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = TelegramChannelAdapter()

    def test_normalize_message_standard_text_update(self):
        telegram_payload = {
            "update_id": 998877,
            "message": {
                "message_id": 4321,
                "from": {
                    "id": 987654321,
                    "is_bot": False,
                    "first_name": "Alice",
                    "last_name": "Smith",
                    "username": "alicesmith",
                    "language_code": "en",
                },
                "chat": {
                    "id": 987654321,
                    "first_name": "Alice",
                    "username": "alicesmith",
                    "type": "private",
                },
                "date": 1699999999,
                "text": "Check my maintenance dues",
            },
            "deployment_key": "dep_tg_test_key",
        }

        incoming = self.adapter.normalize_message(telegram_payload)

        self.assertIsInstance(incoming, IncomingMessage)
        self.assertEqual(incoming.channel, "telegram")
        self.assertEqual(incoming.external_user_id, "987654321")
        self.assertEqual(incoming.deployment_id, "dep_tg_test_key")
        self.assertEqual(incoming.message["text"], "Check my maintenance dues")
        self.assertEqual(incoming.message["message_id"], "4321")
        self.assertEqual(incoming.metadata["username"], "alicesmith")
        self.assertEqual(incoming.metadata["first_name"], "Alice")
        self.assertEqual(incoming.metadata["chat_id"], 987654321)
        self.assertEqual(incoming.metadata["language"], "en")

    def test_normalize_message_callback_query_update(self):
        telegram_payload = {
            "update_id": 998878,
            "callback_query": {
                "id": "cb_query_112233",
                "from": {
                    "id": 987654321,
                    "first_name": "Alice",
                    "username": "alicesmith",
                },
                "message": {
                    "message_id": 4322,
                    "chat": {"id": 987654321},
                },
                "data": "pay_dues_action",
            },
            "deployment_key": "dep_tg_test_key",
        }

        incoming = self.adapter.normalize_message(telegram_payload)

        self.assertIsInstance(incoming, IncomingMessage)
        self.assertEqual(incoming.channel, "telegram")
        self.assertEqual(incoming.external_user_id, "987654321")
        self.assertEqual(incoming.message["text"], "pay_dues_action")
        self.assertEqual(incoming.message["message_id"], "cb_query_112233")
        self.assertTrue(incoming.metadata["is_callback"])

    def test_normalize_message_missing_user_raises(self):
        bad_payload = {"update_id": 1, "message": {"text": "hello"}}
        with self.assertRaises(SecurityValidationError):
            self.adapter.normalize_message(bad_payload)

    def test_format_response_plain_text(self):
        resp = OutgoingResponse.create(
            conversation_id="conv_tg_01",
            text="Hello from bot!",
            response_type="text",
            actions=[],
        )

        formatted = self.adapter.format_response(resp, recipient="987654321")

        self.assertEqual(formatted["chat_id"], "987654321")
        self.assertEqual(formatted["text"], "Hello from bot!")
        self.assertNotIn("reply_markup", formatted)

    def test_format_response_with_inline_keyboard(self):
        flow_dict = {
            "conversation_id": "conv_tg_02",
            "messages": [
                {
                    "type": "options",
                    "text": "Choose an option:",
                    "options": [
                        {"label": "Maintenance", "value": "dues"},
                        {"label": "Visitor Pass", "value": "visitor"},
                    ],
                }
            ],
        }

        formatted = self.adapter.format_response(flow_dict, recipient=987654321)

        self.assertEqual(formatted["chat_id"], 987654321)
        self.assertEqual(formatted["text"], "Choose an option:")
        self.assertIn("reply_markup", formatted)
        keyboard = formatted["reply_markup"]["inline_keyboard"]
        self.assertEqual(len(keyboard), 1)  # 2 buttons grouped in rows
        self.assertEqual(len(keyboard[0]), 2)
        self.assertEqual(keyboard[0][0]["text"], "Maintenance")
        self.assertEqual(keyboard[0][0]["callback_data"], "dues")
        self.assertEqual(keyboard[0][1]["text"], "Visitor Pass")
        self.assertEqual(keyboard[0][1]["callback_data"], "visitor")

    @patch("requests.post")
    def test_send_telegram_message(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"ok": True}
        mock_post.return_value = mock_resp

        payload = {"chat_id": 12345, "text": "Hi"}
        result = self.adapter.send_telegram_message(bot_token="123456:ABC-DEF", payload=payload)

        mock_post.assert_called_once_with(
            "https://api.telegram.org/bot123456:ABC-DEF/sendMessage",
            json=payload,
            timeout=10,
        )
        self.assertEqual(result.status_code, 200)


class TestWhatsAppChannelAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = WhatsAppChannelAdapter()

    def test_normalize_message_meta_cloud_api_payload(self):
        meta_payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "WABA_ID_001",
                    "changes": [
                        {
                            "field": "messages",
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "15550254583",
                                    "phone_number_id": "100609346426371",
                                },
                                "contacts": [
                                    {
                                        "profile": {"name": "Bob Builder"},
                                        "wa_id": "919876543210",
                                    }
                                ],
                                "messages": [
                                    {
                                        "from": "919876543210",
                                        "id": "wamid.HBgLMTY...",
                                        "timestamp": "1603059201",
                                        "type": "text",
                                        "text": {"body": "Outstanding dues TB2-203"},
                                    }
                                ],
                            },
                        }
                    ],
                }
            ],
            "deployment_key": "dep_wa_test_key",
        }

        incoming = self.adapter.normalize_message(meta_payload)

        self.assertIsInstance(incoming, IncomingMessage)
        self.assertEqual(incoming.channel, "whatsapp")
        self.assertEqual(incoming.external_user_id, "919876543210")
        self.assertEqual(incoming.deployment_id, "dep_wa_test_key")
        self.assertEqual(incoming.message["text"], "Outstanding dues TB2-203")
        self.assertEqual(incoming.message["message_id"], "wamid.HBgLMTY...")
        self.assertEqual(incoming.metadata["phone_number_id"], "100609346426371")
        self.assertEqual(incoming.metadata["profile_name"], "Bob Builder")

    def test_normalize_message_interactive_button_reply(self):
        interactive_payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "metadata": {"phone_number_id": "100609346426371"},
                                "contacts": [{"wa_id": "919876543210", "profile": {"name": "Bob"}}],
                                "messages": [
                                    {
                                        "from": "919876543210",
                                        "id": "wamid.BTN_01",
                                        "type": "interactive",
                                        "interactive": {
                                            "type": "button_reply",
                                            "button_reply": {
                                                "id": "btn_pay_now",
                                                "title": "Pay Now",
                                            },
                                        },
                                    }
                                ],
                            }
                        }
                    ]
                }
            ],
            "deployment_key": "dep_wa_test_key",
        }

        incoming = self.adapter.normalize_message(interactive_payload)
        self.assertEqual(incoming.message["text"], "btn_pay_now")
        self.assertEqual(incoming.external_user_id, "919876543210")

    def test_normalize_message_flat_mock_payload(self):
        flat_payload = {
            "deployment_key": "dep_wa_test_key",
            "from": "919876543210",
            "text": "Hello bot",
            "phone_number_id": "100609346426371",
        }

        incoming = self.adapter.normalize_message(flat_payload)
        self.assertEqual(incoming.channel, "whatsapp")
        self.assertEqual(incoming.external_user_id, "919876543210")
        self.assertEqual(incoming.message["text"], "Hello bot")

    def test_normalize_message_missing_sender_raises(self):
        bad_payload = {"deployment_key": "dep_123", "text": "Hello"}
        with self.assertRaises(SecurityValidationError):
            self.adapter.normalize_message(bad_payload)

    def test_format_response_plain_text(self):
        resp = OutgoingResponse.create(
            conversation_id="conv_wa_01",
            text="Your outstanding dues are ₹ 2,940.00",
            response_type="text",
            actions=[],
        )

        formatted = self.adapter.format_response(resp, recipient="919876543210")

        self.assertEqual(formatted["messaging_product"], "whatsapp")
        self.assertEqual(formatted["to"], "919876543210")
        self.assertEqual(formatted["type"], "text")
        self.assertEqual(formatted["text"]["body"], "Your outstanding dues are ₹ 2,940.00")

    def test_format_response_with_buttons(self):
        flow_dict = {
            "conversation_id": "conv_wa_02",
            "messages": [
                {
                    "type": "options",
                    "text": "Select action:",
                    "options": [
                        {"label": "Pay Now", "value": "pay"},
                        {"label": "Details", "value": "details"},
                    ],
                }
            ],
        }

        formatted = self.adapter.format_response(flow_dict, recipient="919876543210")

        self.assertEqual(formatted["type"], "interactive")
        self.assertEqual(formatted["interactive"]["type"], "button")
        self.assertEqual(formatted["interactive"]["body"]["text"], "Select action:")
        buttons = formatted["interactive"]["action"]["buttons"]
        self.assertEqual(len(buttons), 2)
        self.assertEqual(buttons[0]["reply"]["id"], "pay")
        self.assertEqual(buttons[0]["reply"]["title"], "Pay Now")

    def test_format_response_with_list(self):
        # When more than 3 options exist, WhatsApp requires interactive list
        flow_dict = {
            "conversation_id": "conv_wa_03",
            "messages": [
                {
                    "type": "options",
                    "text": "Select flat:",
                    "options": [
                        {"label": "TB2-101", "value": "TB2-101"},
                        {"label": "TB2-102", "value": "TB2-102"},
                        {"label": "TB2-103", "value": "TB2-103"},
                        {"label": "TB2-104", "value": "TB2-104"},
                    ],
                }
            ],
        }

        formatted = self.adapter.format_response(flow_dict, recipient="919876543210")

        self.assertEqual(formatted["type"], "interactive")
        self.assertEqual(formatted["interactive"]["type"], "list")
        rows = formatted["interactive"]["action"]["sections"][0]["rows"]
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0]["id"], "TB2-101")

    @patch("requests.post")
    def test_send_whatsapp_message(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"messages": [{"id": "wamid.12345"}]}
        mock_post.return_value = mock_resp

        payload = {"messaging_product": "whatsapp", "to": "919876543210", "type": "text"}
        result = self.adapter.send_whatsapp_message(
            phone_number_id="100609346426371",
            access_token="EAABxyz123",
            payload=payload,
        )

        mock_post.assert_called_once_with(
            "https://graph.facebook.com/v19.0/100609346426371/messages",
            headers={"Authorization": "Bearer EAABxyz123", "Content-Type": "application/json"},
            json=payload,
            timeout=10,
        )
        self.assertEqual(result.status_code, 200)


class TestChannelGateway(unittest.TestCase):
    def setUp(self):
        self.gateway = ChannelGateway()

    def test_default_adapters_registered(self):
        self.assertTrue(self.gateway.has_adapter("web"))
        self.assertTrue(self.gateway.has_adapter("telegram"))
        self.assertTrue(self.gateway.has_adapter("whatsapp"))

    def test_get_adapter_instances(self):
        self.assertIsInstance(self.gateway.get_adapter("web"), BaseChannelAdapter)
        self.assertIsInstance(self.gateway.get_adapter("telegram"), TelegramChannelAdapter)
        self.assertIsInstance(self.gateway.get_adapter("whatsapp"), WhatsAppChannelAdapter)

    def test_custom_adapter_registration(self):
        class SlackChannelAdapter(BaseChannelAdapter):
            channel_type = "slack"
            def normalize_message(self, raw_payload, headers=None):
                return IncomingMessage.create(
                    bot_id="b1", deployment_id="d1", channel="slack",
                    external_user_id="U123", text="hi"
                )
            def format_response(self, response, **kwargs):
                return {"text": "slack_msg"}

        self.gateway.register_adapter("slack", SlackChannelAdapter)
        self.assertTrue(self.gateway.has_adapter("slack"))
        self.assertEqual(self.gateway.get_adapter("slack").channel_type, "slack")

    def test_unknown_channel_raises(self):
        with self.assertRaises(ValueError):
            self.gateway.get_adapter("unknown_channel_xyz")


class TestBotChannelCredentials(unittest.TestCase):
    def test_whatsapp_credentials_retrieval(self):
        from universal_chatbot.universal_chatbot.doctype.bot_channel.bot_channel import BotChannel
        channel = BotChannel({
            "doctype": "Bot Channel",
            "channel_name": "Test WA Channel",
            "channel_type": "WhatsApp",
            "whatsapp_phone_number_id": "10987654321",
            "whatsapp_access_token": "EAAB_mock_token",
            "whatsapp_verify_token": "verify_secret_123",
            "config": None,
        })

        creds = channel.get_credentials()
        self.assertEqual(creds["phone_number_id"], "10987654321")
        self.assertEqual(creds["access_token"], "EAAB_mock_token")
        self.assertEqual(creds["verify_token"], "verify_secret_123")

    def test_telegram_credentials_retrieval(self):
        from universal_chatbot.universal_chatbot.doctype.bot_channel.bot_channel import BotChannel
        channel = BotChannel({
            "doctype": "Bot Channel",
            "channel_name": "Test TG Channel",
            "channel_type": "Telegram",
            "telegram_bot_token": "987654:ABC-mock-token",
            "telegram_webhook_secret": "secret_webhook_pass",
            "config": None,
        })

        creds = channel.get_credentials()
        self.assertEqual(creds["bot_token"], "987654:ABC-mock-token")
        self.assertEqual(creds["webhook_secret"], "secret_webhook_pass")

    def test_credentials_fallback_to_config_json(self):
        from universal_chatbot.universal_chatbot.doctype.bot_channel.bot_channel import BotChannel
        import json
        channel = BotChannel({
            "doctype": "Bot Channel",
            "channel_name": "Test Config WA Channel",
            "channel_type": "WhatsApp",
            "whatsapp_phone_number_id": None,
            "whatsapp_access_token": None,
            "whatsapp_verify_token": None,
            "config": json.dumps({
                "phone_number_id": "cfg_phone_id",
                "access_token": "cfg_token",
                "verify_token": "cfg_verify"
            }),
        })

        creds = channel.get_credentials()
        self.assertEqual(creds["phone_number_id"], "cfg_phone_id")
        self.assertEqual(creds["access_token"], "cfg_token")
        self.assertEqual(creds["verify_token"], "cfg_verify")


class TestWebhookEndpoints(unittest.TestCase):
    @patch("universal_chatbot.channels.gateway.ChannelGateway.process_and_execute")
    def test_telegram_webhook_execution(self, mock_process):
        from universal_chatbot.channels.telegram.adapter import telegram_webhook
        import frappe

        mock_process.return_value = {
            "conversation_id": "conv_tg_live_01",
            "status": "completed",
            "deployment": MagicMock(name="DEP-01"),
            "formatted_response": {"chat_id": "123", "text": "hello"},
        }

        mock_req = MagicMock()
        mock_req.get_json.return_value = {
            "update_id": 1,
            "message": {"message_id": 1, "from": {"id": 123}, "text": "test"}
        }
        mock_req.args = {"deployment_key": "dep_123"}
        mock_req.headers = {}
        frappe.local.request = mock_req

        with patch("universal_chatbot.universal_chatbot.doctype.bot_channel.bot_channel.BotChannel.get_channel_by_deployment", return_value=None):
            res = telegram_webhook(deployment_key="dep_123")
            self.assertEqual(res["status"], "ok")
            self.assertEqual(res["conversation_id"], "conv_tg_live_01")

    def test_whatsapp_webhook_get_verification(self):
        from universal_chatbot.channels.whatsapp.adapter import whatsapp_webhook
        import frappe

        mock_req = MagicMock()
        mock_req.method = "GET"
        mock_req.args = {
            "hub.mode": "subscribe",
            "hub.challenge": "1158201444",
            "hub.verify_token": "my_meta_secret_token",
        }
        mock_req.headers = {}
        frappe.local.request = mock_req
        frappe.local.form_dict = {}

        with patch("frappe.db.get_value", return_value="CH-WA-01"):
            resp = whatsapp_webhook()
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.get_data(as_text=True), "1158201444")


if __name__ == "__main__":
    unittest.main()
