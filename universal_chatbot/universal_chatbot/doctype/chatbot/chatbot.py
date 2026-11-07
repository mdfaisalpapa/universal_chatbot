# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import re
import frappe
from frappe.model.document import Document
from frappe import _


class Chatbot(Document):
    def validate(self):
        self.validate_slug()
        if self.is_published and self.status != "Active":
            self.status = "Active"

    def validate_slug(self):
        if not re.match(r"^[a-z0-9_-]+$", self.bot_name):
            frappe.throw(
                _("Bot Name / Slug can only contain lowercase letters, numbers, hyphens, and underscores.")
            )
