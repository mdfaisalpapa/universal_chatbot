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

    def on_trash(self):
        """
        Handle deletion policy:
        - In Production (developer_mode == 0): Disallow hard delete of active/existing bots.
          Enforce Approach 3: Soft-Delete (Archive).
        - In Development (developer_mode == 1): Allow clean cascading deletion (Approach 1 & 2).
        """
        is_dev_mode = bool(frappe.conf.get("developer_mode"))

        if not is_dev_mode:
            frappe.throw(
                _(
                    "Permanent deletion of Chatbot '{0}' is disabled in Production to preserve audit trails "
                    "and conversation history. Please set its status to 'Archived' instead."
                ).format(self.name),
                title=_("Hard Delete Prohibited in Production"),
            )

        # In Development: Clean cascading deletion of all dependent records
        self.clean_cascade_delete()

    def clean_cascade_delete(self):
        """Cleanly remove dependent records before Chatbot is deleted."""
        bot_identifier = self.name

        # 1. Delete associated deployments
        for dep in frappe.get_all("Bot Deployment", filters={"chatbot": bot_identifier}, pluck="name"):
            frappe.delete_doc("Bot Deployment", dep, force=1, ignore_permissions=True)

        # 2. Delete associated bot channels (cleans up secrets in __Auth too)
        for ch in frappe.get_all("Bot Channel", filters={"chatbot": bot_identifier}, pluck="name"):
            frappe.delete_doc("Bot Channel", ch, force=1, ignore_permissions=True)

        # 3. Delete flows
        for flow in frappe.get_all("Chatbot Flow", filters={"bot": bot_identifier}, pluck="name"):
            frappe.delete_doc("Chatbot Flow", flow, force=1, ignore_permissions=True)

        # 4. Delete versions
        for ver in frappe.get_all("Bot Version", filters={"chatbot": bot_identifier}, pluck="name"):
            frappe.delete_doc("Bot Version", ver, force=1, ignore_permissions=True)

        # 5. Delete integrations
        for integ in frappe.get_all("Chatbot Integration", filters={"chatbot": bot_identifier}, pluck="name"):
            frappe.delete_doc("Chatbot Integration", integ, force=1, ignore_permissions=True)

        # 6. Delete conversations sessions
        for conv in frappe.get_all("Chat Conversation", filters={"bot": bot_identifier}, pluck="name"):
            frappe.delete_doc("Chat Conversation", conv, force=1, ignore_permissions=True)
