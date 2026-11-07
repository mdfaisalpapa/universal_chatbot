# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class ChatMessage(Document):
    def before_insert(self):
        if not self.timestamp:
            self.timestamp = now_datetime()
