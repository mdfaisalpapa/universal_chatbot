# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import json
import secrets
import frappe
from frappe.model.document import Document
from frappe import _


class BotDeployment(Document):
    def before_insert(self):
        if not self.deployment_key:
            self.deployment_key = secrets.token_hex(16)

    def validate(self):
        if not self.deployment_key:
            self.deployment_key = secrets.token_hex(16)
        self.validate_json()
        self.sync_channel_link()

    def on_update(self):
        self.sync_channel_link()

    def sync_channel_link(self):
        """Ensure bidirectional link between Bot Deployment and Bot Channel."""
        if self.channel and frappe.db.exists("Bot Channel", self.channel):
            ch_dep = frappe.db.get_value("Bot Channel", self.channel, "deployment")
            if ch_dep != self.name:
                frappe.db.set_value("Bot Channel", self.channel, "deployment", self.name)

    def validate_json(self):
        if self.theme_config:
            try:
                json.loads(self.theme_config)
            except Exception as e:
                frappe.throw(_("Theme Config must be valid JSON: {0}").format(str(e)))
