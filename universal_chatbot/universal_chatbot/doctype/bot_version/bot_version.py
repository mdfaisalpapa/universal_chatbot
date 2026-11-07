# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime
from frappe import _


class BotVersion(Document):
    def validate(self):
        self.validate_json()
        if self.status == "Published" and not self.published_at:
            self.published_at = now_datetime()
            self.published_by = frappe.session.user if hasattr(frappe, "session") else "Administrator"

    def validate_json(self):
        if self.flow_definition:
            try:
                json.loads(self.flow_definition)
            except Exception as e:
                frappe.throw(_("Flow definition must be valid JSON: {0}").format(str(e)))
