# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.model.document import Document
from frappe import _


class FlowNode(Document):
    def validate(self):
        if self.configuration:
            try:
                json.loads(self.configuration)
            except Exception as e:
                frappe.throw(_("Configuration must be valid JSON: {0}").format(str(e)))
