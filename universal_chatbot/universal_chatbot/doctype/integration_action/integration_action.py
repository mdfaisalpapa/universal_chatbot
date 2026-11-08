# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.model.document import Document
from frappe import _


class IntegrationAction(Document):
    def validate(self):
        if self.input_schema:
            try:
                json.loads(self.input_schema)
            except Exception as e:
                frappe.throw(_("Input schema must be valid JSON: {0}").format(str(e)))

        if self.output_mapping:
            try:
                json.loads(self.output_mapping)
            except Exception as e:
                frappe.throw(_("Output mapping must be valid JSON: {0}").format(str(e)))
