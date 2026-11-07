# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime
from frappe import _


class ConversationEvent(Document):
    def before_insert(self):
        if not self.timestamp:
            self.timestamp = now_datetime()

    def validate(self):
        if self.details:
            try:
                json.loads(self.details)
            except Exception as e:
                frappe.throw(_("Event details must be valid JSON: {0}").format(str(e)))
