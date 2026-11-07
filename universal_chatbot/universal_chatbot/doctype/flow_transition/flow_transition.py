# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.model.document import Document


class FlowTransition(Document):
    def validate(self):
        if self.condition and self.condition.strip().startswith("{"):
            try:
                json.loads(self.condition)
            except Exception as e:
                frappe.throw(f"Condition JSON is invalid: {str(e)}")
