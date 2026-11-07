# Copyright (c) 2026, Universal Chatbot and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.exceptions import ValidationError


class TestChannelIdentity(FrappeTestCase):
    def setUp(self):
        self.contact1 = frappe.get_doc({
            "doctype": "Chat Contact",
            "display_name": "Contact One",
        }).insert(ignore_permissions=True)

        self.contact2 = frappe.get_doc({
            "doctype": "Chat Contact",
            "display_name": "Contact Two",
        }).insert(ignore_permissions=True)

    def tearDown(self):
        frappe.db.rollback()

    def test_create_channel_identity(self):
        ident = frappe.get_doc({
            "doctype": "Channel Identity",
            "contact": self.contact1.name,
            "channel": "web",
            "external_user_id": "usr_web_001",
            "verification_status": "Anonymous",
        }).insert(ignore_permissions=True)

        self.assertEqual(ident.name, "web:usr_web_001")
        self.assertEqual(ident.contact, self.contact1.name)

    def test_prevent_remapping_identity_to_different_contact(self):
        frappe.get_doc({
            "doctype": "Channel Identity",
            "contact": self.contact1.name,
            "channel": "web",
            "external_user_id": "usr_unique_002",
        }).insert(ignore_permissions=True)

        # Attempt to map same external_user_id to another contact must fail
        with self.assertRaises(Exception):
            frappe.get_doc({
                "doctype": "Channel Identity",
                "contact": self.contact2.name,
                "channel": "web",
                "external_user_id": "usr_unique_002",
            }).insert(ignore_permissions=True)
