# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _


class ChannelIdentity(Document):
    def validate(self):
        # Prevent silent merging or collision of channel identities across different contacts
        existing = frappe.db.get_value(
            "Channel Identity",
            {"channel": self.channel, "external_user_id": self.external_user_id},
            ["name", "contact"],
            as_dict=True,
        )
        if existing and existing.name != self.name and existing.contact != self.contact:
            frappe.throw(
                _("Channel Identity {0}:{1} is already explicitly mapped to contact {2}.").format(
                    self.channel, self.external_user_id, existing.contact
                )
            )
