# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import json
from typing import Any, Dict, Optional
import frappe
from frappe.model.document import Document
from frappe import _


class BotChannel(Document):
    @property
    def bot_deployment(self):
        return self.deployment

    @bot_deployment.setter
    def bot_deployment(self, value):
        self.deployment = value

    def validate(self):
        if getattr(self, "bot_deployment", None) and not self.deployment:
            self.deployment = self.bot_deployment

        # Auto-detect matching deployment if not populated on view/edit save
        if not self.deployment and self.chatbot:
            matching = frappe.db.get_value("Bot Deployment", {"channel": self.name}, "name")
            if not matching and self.channel_type:
                matching = frappe.db.get_value(
                    "Bot Deployment",
                    {"chatbot": self.chatbot, "deployment_name": ["like", f"%{self.channel_type}%"]},
                    "name",
                )
            if matching:
                self.deployment = matching

        self.validate_config_json()
        self.sync_deployment_link()

    def validate_config_json(self):
        if self.config:
            try:
                json.loads(self.config)
            except Exception as e:
                frappe.throw(_("Channel config must be valid JSON: {0}").format(str(e)))

    def sync_deployment_link(self):
        """Ensure bidirectional link between Bot Deployment and Bot Channel."""
        if self.deployment and frappe.db.exists("Bot Deployment", self.deployment):
            dep_channel = frappe.db.get_value("Bot Deployment", self.deployment, "channel")
            if dep_channel != self.name:
                frappe.db.set_value("Bot Deployment", self.deployment, "channel", self.name)

    def on_update(self):
        self.sync_deployment_link()

    def get_credentials(self) -> Dict[str, Any]:
        """Securely retrieve decrypted channel credentials."""
        creds: Dict[str, Any] = {}
        cfg: Dict[str, Any] = {}
        if self.config:
            try:
                cfg = json.loads(self.config)
            except Exception:
                cfg = {}

        if self.channel_type == "WhatsApp":
            access_token = ""
            if self.whatsapp_access_token:
                try:
                    access_token = self.get_password("whatsapp_access_token")
                except Exception:
                    access_token = self.whatsapp_access_token
            creds = {
                "phone_number_id": self.whatsapp_phone_number_id or cfg.get("phone_number_id", ""),
                "access_token": access_token or cfg.get("access_token", ""),
                "verify_token": self.whatsapp_verify_token or cfg.get("verify_token", ""),
            }

        elif self.channel_type == "Telegram":
            bot_token = ""
            if self.telegram_bot_token:
                try:
                    bot_token = self.get_password("telegram_bot_token")
                except Exception:
                    bot_token = self.telegram_bot_token
            creds = {
                "bot_token": bot_token or cfg.get("bot_token", ""),
                "webhook_secret": self.telegram_webhook_secret or cfg.get("webhook_secret", ""),
            }

        return creds

    @classmethod
    def get_channel_by_deployment(
        cls, deployment_key_or_name: str, channel_type: Optional[str] = None
    ) -> Optional["BotChannel"]:
        """Retrieve the Bot Channel linked to a deployment."""
        if not deployment_key_or_name:
            return None

        # 1. Check if argument is deployment_name or deployment_key
        dep_name = frappe.db.get_value(
            "Bot Deployment", {"deployment_key": deployment_key_or_name}, "name"
        ) or (
            deployment_key_or_name
            if frappe.db.exists("Bot Deployment", deployment_key_or_name)
            else None
        )

        if not dep_name:
            return None

        # Check channel linked on deployment
        channel_name = frappe.db.get_value("Bot Deployment", dep_name, "channel")
        if channel_name and frappe.db.exists("Bot Channel", channel_name):
            channel_doc = frappe.get_doc("Bot Channel", channel_name)
            if not channel_type or channel_doc.channel_type == channel_type:
                return channel_doc

        # Or channel linking back to deployment
        filters = {"deployment": dep_name}
        if channel_type:
            filters["channel_type"] = channel_type
        cname = frappe.db.get_value("Bot Channel", filters, "name")
        if cname:
            return frappe.get_doc("Bot Channel", cname)

        return None
