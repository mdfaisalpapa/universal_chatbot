# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestChatContact(FrappeTestCase):
    def tearDown(self):
        frappe.db.rollback()

    def test_create_contact(self):
        contact = frappe.get_doc({
            "doctype": "Chat Contact",
            "display_name": "Alice Smith",
            "contact_status": "Active",
            "email": "alice@example.com",
            "phone": "+1234567890",
        }).insert(ignore_permissions=True)

        self.assertTrue(contact.name.startswith("CONT-"))
        self.assertEqual(contact.display_name, "Alice Smith")
        self.assertEqual(contact.contact_status, "Active")

    def test_no_implicit_merge_on_duplicate_name(self):
        # Explicit identity linking principle: same display_name creates distinct contacts
        c1 = frappe.get_doc({
            "doctype": "Chat Contact",
            "display_name": "John Doe",
        }).insert(ignore_permissions=True)

        c2 = frappe.get_doc({
            "doctype": "Chat Contact",
            "display_name": "John Doe",
        }).insert(ignore_permissions=True)

        self.assertNotEqual(c1.name, c2.name)
