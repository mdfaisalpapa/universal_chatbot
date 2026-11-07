# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.model.document import Document
from frappe import _


class FlowExecution(Document):
    def validate(self):
        if self.execution_context:
            try:
                json.loads(self.execution_context)
            except Exception as e:
                frappe.throw(_("Execution context must be valid JSON: {0}").format(str(e)))
