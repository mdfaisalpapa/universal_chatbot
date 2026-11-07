# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.model.document import Document
from frappe import _


class ConversationState(Document):
    def validate(self):
        self.validate_json()

    def validate_json(self):
        if self.variables:
            try:
                json.loads(self.variables)
            except Exception as e:
                frappe.throw(_("Variables must be valid JSON: {0}").format(str(e)))
        if self.context:
            try:
                json.loads(self.context)
            except Exception as e:
                frappe.throw(_("Context must be valid JSON: {0}").format(str(e)))
