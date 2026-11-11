"""Unit tests for Flow Export & Import Utility."""

import json
import unittest
import frappe
from universal_chatbot.flow.export_import import export_flow_json, import_flow_json


class TestFlowExportImport(unittest.TestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        self.bot_slug = f"test_expimp_bot_{frappe.generate_hash(length=6).lower()}"
        self.bot = frappe.get_doc({
            "doctype": "Chatbot",
            "bot_name": self.bot_slug,
            "title": "Export Import Test Bot",
            "status": "Active",
        }).insert(ignore_permissions=True)

        self.flow_slug = "sample_test_flow"
        self.flow_docname = f"{self.bot_slug}-{self.flow_slug}"
        self.flow = frappe.get_doc({
            "doctype": "Chatbot Flow",
            "name": self.flow_docname,
            "flow_name": self.flow_slug,
            "bot": self.bot.name,
            "status": "Draft",
            "version": "1.0.0",
            "description": "Flow for testing export and import capabilities",
        }).insert(ignore_permissions=True)

        # Seed 3 nodes
        self.start_node = frappe.get_doc({
            "doctype": "Flow Node",
            "flow": self.flow.name,
            "node_id": "start_1",
            "node_type": "Start",
            "configuration": json.dumps({"message": "Hello tester!", "ui_x": 100, "ui_y": 100}),
        }).insert(ignore_permissions=True)

        self.ask_node = frappe.get_doc({
            "doctype": "Flow Node",
            "flow": self.flow.name,
            "node_id": "ask_1",
            "node_type": "Ask Question",
            "configuration": json.dumps({"prompt": "Enter value:", "save_to_variable": "test_var", "ui_x": 100, "ui_y": 250}),
        }).insert(ignore_permissions=True)

        self.end_node = frappe.get_doc({
            "doctype": "Flow Node",
            "flow": self.flow.name,
            "node_id": "end_1",
            "node_type": "End",
            "configuration": json.dumps({"message": "Goodbye!", "ui_x": 100, "ui_y": 400}),
        }).insert(ignore_permissions=True)

        # Seed transitions
        frappe.get_doc({
            "doctype": "Flow Transition",
            "source_node": self.start_node.name,
            "target_node": self.ask_node.name,
            "condition": "",
        }).insert(ignore_permissions=True)

        frappe.get_doc({
            "doctype": "Flow Transition",
            "source_node": self.ask_node.name,
            "target_node": self.end_node.name,
            "condition": "",
        }).insert(ignore_permissions=True)

        # Seed variable
        frappe.get_doc({
            "doctype": "Flow Variable",
            "flow": self.flow.name,
            "variable_name": "test_var",
            "data_type": "String",
            "default_value": "default_val",
        }).insert(ignore_permissions=True)

        frappe.db.commit()

    def tearDown(self):
        # Cleanup created records
        frappe.db.rollback()

    def test_export_flow_json(self):
        """Export flow serializes all nodes, transitions, variables, and metadata cleanly."""
        payload = export_flow_json(self.flow_docname)

        self.assertEqual(payload["schema_version"], "1.0")
        self.assertEqual(payload["metadata"]["flow_name"], self.flow_slug)
        self.assertEqual(payload["metadata"]["bot"], self.bot.name)

        # Nodes
        self.assertEqual(len(payload["nodes"]), 3)
        node_ids = {n["node_id"] for n in payload["nodes"]}
        self.assertEqual(node_ids, {"start_1", "ask_1", "end_1"})

        # Transitions
        self.assertEqual(len(payload["transitions"]), 2)
        trans_pairs = {(t["source_node"], t["target_node"]) for t in payload["transitions"]}
        self.assertIn(("start_1", "ask_1"), trans_pairs)
        self.assertIn(("ask_1", "end_1"), trans_pairs)

        # Variables
        self.assertEqual(len(payload["variables"]), 1)
        self.assertEqual(payload["variables"][0]["variable_name"], "test_var")

    def test_import_flow_json_new_flow(self):
        """Import flow provisions a brand new flow under a bot."""
        exported = export_flow_json(self.flow_docname)
        exported["metadata"]["flow_name"] = "cloned_flow"

        res = import_flow_json(exported, bot_slug=self.bot.name)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["nodes_count"], 3)
        self.assertEqual(res["transitions_count"], 2)
        self.assertEqual(res["variables_count"], 1)

        cloned_docname = f"{self.bot.name}-cloned_flow"
        self.assertTrue(frappe.db.exists("Chatbot Flow", cloned_docname))

        nodes = frappe.get_all("Flow Node", filters={"flow": cloned_docname})
        self.assertEqual(len(nodes), 3)

    def test_import_flow_json_duplicate_prevention(self):
        """Importing existing flow without overwrite=True throws DuplicateEntryError."""
        exported = export_flow_json(self.flow_docname)
        with self.assertRaises(frappe.DuplicateEntryError):
            import_flow_json(exported, bot_slug=self.bot.name, overwrite=False)

    def test_import_flow_json_overwrite(self):
        """Importing existing flow with overwrite=True successfully updates graph."""
        exported = export_flow_json(self.flow_docname)
        # Modify node message
        for n in exported["nodes"]:
            if n["node_id"] == "start_1":
                n["configuration"]["message"] = "Updated Welcome Message!"

        res = import_flow_json(exported, bot_slug=self.bot.name, overwrite=True)
        self.assertEqual(res["status"], "success")

        start_node_db = frappe.get_doc("Flow Node", f"{self.flow_docname}-start_1")
        cfg = json.loads(start_node_db.configuration)
        self.assertEqual(cfg["message"], "Updated Welcome Message!")
