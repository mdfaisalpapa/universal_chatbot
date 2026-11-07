# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.model.document import Document
from frappe import _


class BotChannel(Document):
    def validate(self):
        if self.config:
            try:
                json.loads(self.config)
            except Exception as e:
                frappe.throw(_("Channel config must be valid JSON: {0}").format(str(e)))
