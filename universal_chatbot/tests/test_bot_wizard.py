"""Unit tests for the Guided Bot Creation Wizard API."""

import json
import unittest
import frappe
from universal_chatbot.api.v1.wizard import (
    get_bot_templates,
    quick_create_bot,
    get_bot_config,
    update_bot_config,
    get_bot_flows,
    create_chatbot_flow,
    update_chatbot_flow_properties,
    delete_chatbot_flow,
    delete_bot_channel,
)


class TestBotWizard(unittest.TestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        self.cleanup_bots = []

    def tearDown(self):
        for bslug in self.cleanup_bots:
            # Delete deployments, channels, versions, flows, and chatbot
            deps = frappe.get_all("Bot Deployment", filters={"chatbot": bslug}, fields=["name"])
            for d in deps:
                frappe.delete_doc("Bot Deployment", d.name, force=1, ignore_permissions=True)

            chans = frappe.get_all("Bot Channel", filters={"chatbot": bslug}, fields=["name"])
            for c in chans:
                frappe.delete_doc("Bot Channel", c.name, force=1, ignore_permissions=True)

            vers = frappe.get_all("Bot Version", filters={"chatbot": bslug}, fields=["name"])
            for v in vers:
                frappe.delete_doc("Bot Version", v.name, force=1, ignore_permissions=True)

            flows = frappe.get_all("Chatbot Flow", filters={"bot": bslug}, fields=["name"])
            for f in flows:
                frappe.delete_doc("Chatbot Flow", f.name, force=1, ignore_permissions=True)

            if frappe.db.exists("Chatbot", bslug):
                frappe.delete_doc("Chatbot", bslug, force=1, ignore_permissions=True)

        frappe.db.commit()

    def test_get_bot_templates(self):
        """Verify available templates are returned with required fields."""
        templates = get_bot_templates()
        self.assertGreaterEqual(len(templates), 3)
        t_ids = [t["id"] for t in templates]
        self.assertIn("api_lookup", t_ids)
        self.assertIn("simple_faq", t_ids)
        self.assertIn("blank", t_ids)

    def test_quick_create_bot_api_lookup_and_omnichannel(self):
        """Verify atomic creation of Chatbot, Flow, Version, and all 3 channels."""
        slug = f"test_wizard_{frappe.generate_hash(length=6)}"
        self.cleanup_bots.append(slug)

        channels = [
            {"type": "web", "allowed_domains": "https://example.com"},
            {"type": "whatsapp", "phone_number_id": "999888777", "access_token": "secret_wa_tok", "verify_token": "wa_ver_123"},
            {"type": "telegram", "bot_token": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"},
        ]

        res = quick_create_bot(
            title="Wizard Test Bot",
            bot_slug=slug,
            template_id="api_lookup",
            channels=channels,
        )

        self.assertEqual(res["status"], "success")
        self.assertEqual(res["bot_slug"], slug)
        self.assertEqual(res["version_number"], "1.0.0")

        # 1. Verify Chatbot
        c_doc = frappe.get_doc("Chatbot", slug)
        self.assertEqual(c_doc.status, "Active")
        self.assertEqual(c_doc.is_published, 1)
        self.assertEqual(c_doc.primary_flow, res["flow_name"])
        self.assertEqual(c_doc.active_version, res["bot_version"])

        # 2. Verify Flow and Nodes
        flow_doc = frappe.get_doc("Chatbot Flow", res["flow_name"])
        self.assertEqual(flow_doc.status, "Published")

        nodes = frappe.get_all("Flow Node", filters={"flow": res["flow_name"]}, fields=["node_id", "node_type"])
        node_ids = [n.node_id for n in nodes]
        self.assertIn("start_node", node_ids)
        self.assertIn("ask_id_node", node_ids)
        self.assertIn("call_action_node", node_ids)
        self.assertIn("send_result_node", node_ids)

        # 3. Verify Deployments
        self.assertEqual(len(res["deployments"]), 3)
        ch_types = [d["channel_type"] for d in res["deployments"]]
        self.assertIn("Web Widget", ch_types)
        self.assertIn("WhatsApp", ch_types)
        self.assertIn("Telegram", ch_types)

        # Check WhatsApp details
        wa_dep = next(d for d in res["deployments"] if d["channel_type"] == "WhatsApp")
        self.assertIn("whatsapp_webhook", wa_dep["webhook_url"])
        self.assertEqual(wa_dep["verify_token"], "wa_ver_123")

        # 4. Verify that all Bot Channels have the deployment field populated
        for d in res["deployments"]:
            ch_doc = frappe.get_doc("Bot Channel", d["channel_name"])
            self.assertEqual(ch_doc.deployment, d["deployment_name"])

    def test_quick_create_bot_validates_required_title(self):
        """Empty title must be rejected with an exception."""
        with self.assertRaises(frappe.ValidationError):
            quick_create_bot(title="", bot_slug="invalid_bot")

    def test_quick_create_bot_rejects_duplicate_slug(self):
        """Duplicate bot slug must be rejected."""
        slug = f"dup_{frappe.generate_hash(length=6)}"
        self.cleanup_bots.append(slug)

        # Create first
        quick_create_bot(title="First Bot", bot_slug=slug, template_id="blank")

        # Attempt to create second with same slug
        with self.assertRaises(frappe.ValidationError):
            quick_create_bot(title="Second Bot", bot_slug=slug, template_id="blank")

    def test_quick_create_bot_template_alias(self):
        """Verify that passing template title alias (e.g. 'ERP & API Lookup') works."""
        slug = f"test_alias_{frappe.generate_hash(length=6)}"
        self.cleanup_bots.append(slug)

        res = quick_create_bot(
            title="Alias Test Bot",
            bot_slug=slug,
            template_id="ERP & API Lookup",
        )
        self.assertEqual(res["status"], "success")
        nodes = frappe.get_all("Flow Node", filters={"flow": res["flow_name"]}, fields=["node_id"])
        node_ids = [n.node_id for n in nodes]
        self.assertIn("call_action_node", node_ids)

    def test_get_and_update_bot_config(self):
        """Verify get_bot_config and update_bot_config for viewing and editing bot and channels."""
        slug = f"test_config_{frappe.generate_hash(length=6)}"
        self.cleanup_bots.append(slug)

        channels = [
            {"type": "web", "allowed_domains": "*"},
            {"type": "whatsapp", "phone_number_id": "111222333", "access_token": "token_init", "verify_token": "v_init"},
        ]

        quick_create_bot(title="Config Test Bot", bot_slug=slug, template_id="blank", channels=channels)

        # 1. Fetch config (view interface)
        cfg = get_bot_config(slug)
        self.assertEqual(cfg["bot_slug"], slug)
        self.assertEqual(cfg["title"], "Config Test Bot")
        self.assertIn("whatsapp", cfg["channels"])
        self.assertEqual(cfg["channels"]["whatsapp"]["whatsapp_phone_number_id"], "111222333")

        # 2. Update config (edit interface)
        updated_channels = [
            {"type": "web", "allowed_domains": "https://example.com"},
            {"type": "whatsapp", "phone_number_id": "999000111", "access_token": "token_updated", "verify_token": "v_updated"},
            {"type": "telegram", "bot_token": "987654:ABCdef"},
        ]
        up_cfg = update_bot_config(
            bot_slug=slug,
            title="Updated Title",
            channels=updated_channels,
        )
        self.assertEqual(up_cfg["title"], "Updated Title")
        self.assertEqual(up_cfg["channels"]["whatsapp"]["whatsapp_phone_number_id"], "999000111")
        self.assertEqual(up_cfg["channels"]["whatsapp"]["whatsapp_access_token"], "token_updated")
        self.assertIn("telegram", up_cfg["channels"])
        self.assertEqual(up_cfg["channels"]["telegram"]["telegram_bot_token"], "987654:ABCdef")

    def test_quick_create_bot_edit_mode(self):
        """Verify quick_create_bot with edit_mode=True updates existing bot, channels, and deployments without duplicate errors."""
        slug = f"test_editmode_{frappe.generate_hash(length=6)}"
        self.cleanup_bots.append(slug)

        initial_channels = [
            {"type": "web", "allowed_domains": "*"},
            {"type": "whatsapp", "phone_number_id": "123456", "access_token": "init_token"},
        ]

        # 1. Initial creation
        res1 = quick_create_bot(
            title="Initial Title",
            bot_slug=slug,
            template_id="blank",
            channels=initial_channels,
        )
        self.assertEqual(res1["status"], "success")

        # 2. Update with edit_mode=True
        updated_channels = [
            {"type": "web", "allowed_domains": "https://mysite.com"},
            {"type": "whatsapp", "phone_number_id": "654321", "access_token": "updated_token", "verify_token": "v_tok_99"},
            {"type": "telegram", "bot_token": "555:SecretTgToken"},
        ]

        res2 = quick_create_bot(
            title="Edited Title",
            bot_slug=slug,
            channels=updated_channels,
            edit_mode=True,
        )
        self.assertEqual(res2["status"], "success")
        self.assertEqual(res2["title"], "Edited Title")

        # 3. Verify in database
        bot_doc = frappe.get_doc("Chatbot", slug)
        self.assertEqual(bot_doc.title, "Edited Title")

        wa_ch_name = frappe.db.get_value("Bot Channel", {"chatbot": slug, "channel_type": "WhatsApp"}, "name")
        self.assertTrue(wa_ch_name)
        wa_doc = frappe.get_doc("Bot Channel", wa_ch_name)
        self.assertEqual(wa_doc.whatsapp_phone_number_id, "654321")
        self.assertEqual(wa_doc.get_credentials().get("access_token"), "updated_token")
        self.assertTrue(wa_doc.deployment)

        tg_ch_name = frappe.db.get_value("Bot Channel", {"chatbot": slug, "channel_type": "Telegram"}, "name")
        self.assertTrue(tg_ch_name)
        tg_doc = frappe.get_doc("Bot Channel", tg_ch_name)
        self.assertEqual(tg_doc.get_credentials().get("bot_token"), "555:SecretTgToken")
        self.assertTrue(tg_doc.deployment)

    def test_flow_management_crud(self):
        """Verify inline flow creation, listing, property editing, and safe deletion."""
        slug = f"test_flow_crud_{frappe.generate_hash(length=6)}"
        self.cleanup_bots.append(slug)

        # 1. Create a base chatbot
        quick_create_bot(title="Flow CRUD Bot", bot_slug=slug, template_id="blank")

        # 2. Test create_chatbot_flow
        res = create_chatbot_flow(
            bot_slug=slug,
            flow_name="faq_branch",
            title="FAQ Branch",
            description="Branch for answering common FAQs",
            set_as_primary=1,
        )
        self.assertEqual(res["status"], "success")
        flow_id = res["flow_name"]
        self.assertEqual(flow_id, f"{slug}-faq_branch")

        # Verify starter canvas nodes were seeded
        nodes = frappe.get_all("Flow Node", filters={"flow": flow_id})
        self.assertGreaterEqual(len(nodes), 2)

        # Verify chatbot doc primary_flow is updated
        bot_doc = frappe.get_doc("Chatbot", slug)
        self.assertEqual(bot_doc.primary_flow, flow_id)

        # 3. Test get_bot_flows
        flows = get_bot_flows(slug)
        flow_names = [f["name"] for f in flows]
        self.assertIn(flow_id, flow_names)
        target_f = next(f for f in flows if f["name"] == flow_id)
        self.assertTrue(target_f["is_primary"])
        self.assertEqual(target_f["version"], "1.0.0")
        self.assertGreaterEqual(target_f["node_count"], 2)

        # 4. Test update_chatbot_flow_properties
        up_res = update_chatbot_flow_properties(
            flow_name=flow_id,
            description="Updated branch description",
            status="Published",
            version="1.1.0",
            set_as_primary=0,
        )
        self.assertEqual(up_res["status"], "success")

        flow_doc = frappe.get_doc("Chatbot Flow", flow_id)
        self.assertEqual(flow_doc.description, "Updated branch description")
        self.assertEqual(flow_doc.status, "Published")
        self.assertEqual(flow_doc.version, "1.1.0")

        bot_doc.reload()
        self.assertIsNone(bot_doc.primary_flow)

        # 5. Test delete_chatbot_flow
        del_res = delete_chatbot_flow(flow_id)
        self.assertEqual(del_res["status"], "success")
        self.assertFalse(frappe.db.exists("Chatbot Flow", flow_id))
        self.assertEqual(frappe.db.count("Flow Node", {"flow": flow_id}), 0)

    def test_channel_management_delete(self):
        """Verify inline deletion of a Bot Channel and its linked Bot Deployment."""
        slug = f"test_ch_del_{frappe.generate_hash(length=6)}"
        self.cleanup_bots.append(slug)

        channels = [
            {"type": "whatsapp", "phone_number_id": "123123123", "access_token": "token123"},
        ]
        res = quick_create_bot(title="Channel Del Bot", bot_slug=slug, template_id="blank", channels=channels)
        wa_dep = next(d for d in res["deployments"] if d["channel_type"] == "WhatsApp")
        ch_name = wa_dep["channel_name"]
        dep_name = wa_dep["deployment_name"]

        self.assertTrue(frappe.db.exists("Bot Channel", ch_name))
        self.assertTrue(frappe.db.exists("Bot Deployment", dep_name))

        # Delete channel via delete_bot_channel
        del_res = delete_bot_channel(ch_name)
        self.assertEqual(del_res["status"], "success")

        # Verify both channel and deployment were deleted
        self.assertFalse(frappe.db.exists("Bot Channel", ch_name))
        self.assertFalse(frappe.db.exists("Bot Deployment", dep_name))
