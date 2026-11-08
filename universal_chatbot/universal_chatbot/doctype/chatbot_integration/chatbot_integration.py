# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _


class ChatbotIntegration(Document):
    def validate(self):
        if self.base_url:
            self.base_url = self.base_url.rstrip("/")
