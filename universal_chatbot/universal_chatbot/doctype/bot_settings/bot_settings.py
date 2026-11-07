# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BotSettings(Document):
    pass


def get_bot_settings():
    """Helper function to load cached Bot Settings."""
    return frappe.get_cached_doc("Bot Settings")
