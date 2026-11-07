# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class ChatConversation(Document):
    def before_insert(self):
        now = now_datetime()
        if not self.started_at:
            self.started_at = now
        if not self.last_activity:
            self.last_activity = now

    def touch(self):
        self.last_activity = now_datetime()
        self.db_set("last_activity", self.last_activity, update_modified=False)
