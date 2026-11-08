# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.password import get_decrypted_password


class IntegrationCredential(Document):
    def get_decrypted_secret(self) -> str:
        """Safely decrypt and return api_secret strictly in backend memory."""
        if not self.name:
            return ""
        try:
            return get_decrypted_password("Integration Credential", self.name, "api_secret") or ""
        except Exception:
            return ""
