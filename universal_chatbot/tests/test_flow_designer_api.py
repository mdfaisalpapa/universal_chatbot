"""Unit tests for Visual Flow Designer API."""

import json
import unittest
import frappe
from universal_chatbot.api.v1.flow_designer import (
    load_visual_flow,
    publish_flow,
    save_visual_flow,
    validate_flow_structure,
)


class TestFlowDesignerAPI(unittest.TestCase):
    """Test suite for Visual Flow Designer backend APIs."""

    def setUp(self):
        frappe.set_user("Administrator")
        self.bot_name = f"designer_bot_{frappe.generate_hash(length=8).lower()}"
        self.bot = frappe.get_doc({
            "doctype": "Chatbot",
            "bot_name": self.bot_name,
            "title": "Designer Test Bot",
            "status": "Draft",
        }).insert(ignore_permissions=True)

        self.flow_name = f"designer_flow_{frappe.generate_hash(length=8).lower()}"
        self.flow = frappe.get_doc({
            "doctype": "Chatbot Flow",
            "flow_name": self.flow_name,
            "bot": self.bot.name,
            "status": "Draft",
        }).insert(ignore_permissions=True)

    def tearDown(self):
        frappe.db.rollback()

    def test_validate_flow_structure_success(self):
        """Valid flow graph should pass structural validation."""
        valid_graph = {
            "nodes": [
                {"node_id": "start_1", "node_type": "start", "configuration": {}},
                {"node_id": "msg_1", "node_type": "send_message", "configuration": {"message": "Hi"}},
                {"node_id": "end_1", "node_type": "end", "configuration": {}},
            ],
            "transitions": [
                {"source_node": "start_1", "target_node": "msg_1"},
                {"source_node": "msg_1", "target_node": "end_1"},
            ],
        }
        # Should not throw
        validate_flow_structure(valid_graph)

    def test_validate_flow_structure_no_start_node(self):
        """Graph without start node must fail validation."""
        invalid_graph = {
            "nodes": [
                {"node_id": "msg_1", "node_type": "send_message", "configuration": {}},
            ],
            "transitions": [],
        }
        with self.assertRaises(frappe.ValidationError):
            validate_flow_structure(invalid_graph)

    def test_validate_flow_structure_multiple_start_nodes(self):
        """Graph with multiple start nodes must fail validation."""
        invalid_graph = {
            "nodes": [
                {"node_id": "start_1", "node_type": "start", "configuration": {}},
                {"node_id": "start_2", "node_type": "start", "configuration": {}},
            ],
            "transitions": [],
        }
        with self.assertRaises(frappe.ValidationError):
            validate_flow_structure(invalid_graph)

    def test_validate_flow_structure_duplicate_node_ids(self):
        """Graph with duplicate node IDs must fail validation."""
        invalid_graph = {
            "nodes": [
                {"node_id": "start_1", "node_type": "start", "configuration": {}},
                {"node_id": "dup_1", "node_type": "send_message", "configuration": {}},
                {"node_id": "dup_1", "node_type": "end", "configuration": {}},
            ],
            "transitions": [],
        }
        with self.assertRaises(frappe.ValidationError):
            validate_flow_structure(invalid_graph)

    def test_validate_flow_structure_dangling_transition(self):
        """Transitions pointing to nonexistent nodes must fail validation."""
        invalid_graph = {
            "nodes": [
                {"node_id": "start_1", "node_type": "start", "configuration": {}},
            ],
            "transitions": [
                {"source_node": "start_1", "target_node": "nonexistent_node"},
            ],
        }
        with self.assertRaises(frappe.ValidationError):
            validate_flow_structure(invalid_graph)

    def test_save_and_load_visual_flow(self):
        """Saving and loading flow graph roundtrips all nodes, transitions, variables, and coords."""
        flow_payload = {
            "nodes": [
                {
                    "node_id": "start_node",
                    "node_type": "start",
                    "x": 120,
                    "y": 80,
                    "configuration": {"description": "Entry"},
                },
                {
                    "node_id": "ask_user",
                    "node_type": "ask_question",
                    "x": 120,
                    "y": 200,
                    "configuration": {
                        "prompt": "What is your order ID?",
                        "save_to_variable": "order_id",
                    },
                },
                {
                    "node_id": "goodbye",
                    "node_type": "end",
                    "x": 120,
                    "y": 350,
                    "configuration": {"message": "Goodbye!"},
                },
            ],
            "transitions": [
                {"source_node": "start_node", "target_node": "ask_user"},
                {"source_node": "ask_user", "target_node": "goodbye"},
            ],
            "variables": [
                {"variable_name": "order_id", "data_type": "String", "default_value": ""},
            ],
        }

        save_res = save_visual_flow(self.flow.name, flow_payload)
        self.assertEqual(save_res["status"], "success")
        self.assertEqual(save_res["nodes_count"], 3)
        self.assertEqual(save_res["transitions_count"], 2)
        self.assertEqual(save_res["variables_count"], 1)

        # Load back visual flow
        loaded = load_visual_flow(self.flow.name)
        self.assertEqual(loaded["flow_name"], self.flow.name)
        self.assertEqual(len(loaded["nodes"]), 3)
        self.assertEqual(len(loaded["transitions"]), 2)
        self.assertEqual(len(loaded["variables"]), 1)

        # Check coordinates and configuration preservation
        node_map = {n["node_id"]: n for n in loaded["nodes"]}
        self.assertIn("start_node", node_map)
        self.assertEqual(node_map["start_node"]["x"], 120)
        self.assertEqual(node_map["start_node"]["y"], 80)

        self.assertIn("ask_user", node_map)
        self.assertEqual(node_map["ask_user"]["configuration"]["save_to_variable"], "order_id")

        # Check transitions
        trans_pairs = [(t["source_node"], t["target_node"]) for t in loaded["transitions"]]
        self.assertIn(("start_node", "ask_user"), trans_pairs)
        self.assertIn(("ask_user", "goodbye"), trans_pairs)

    def test_publish_flow_creates_bot_version(self):
        """Publishing flow creates immutable Bot Version snapshot and marks chatbot active."""
        flow_payload = {
            "nodes": [
                {"node_id": "start_1", "node_type": "start", "x": 100, "y": 100, "configuration": {}},
                {"node_id": "end_1", "node_type": "end", "x": 100, "y": 250, "configuration": {}},
            ],
            "transitions": [
                {"source_node": "start_1", "target_node": "end_1"},
            ],
            "variables": [],
        }

        save_visual_flow(self.flow.name, flow_payload)
        pub_res = publish_flow(self.flow.name, changelog="Initial release")

        self.assertEqual(pub_res["status"], "success")
        self.assertEqual(pub_res["version_number"], "1.0.0")

        # Verify Bot Version doc was created
        version_doc = frappe.get_doc("Bot Version", pub_res["bot_version"])
        self.assertEqual(version_doc.chatbot, self.bot.name)
        self.assertEqual(version_doc.status, "Published")

        snapshot = json.loads(version_doc.flow_definition)
        self.assertEqual(len(snapshot["nodes"]), 2)

        # Verify Chatbot Flow status updated
        self.flow.reload()
        self.assertEqual(self.flow.status, "Published")
        self.assertEqual(self.flow.version, "1.0.0")

        # Verify Chatbot updated
        self.bot.reload()
        self.assertEqual(self.bot.active_version, version_doc.name)
        self.assertEqual(self.bot.status, "Active")
        self.assertEqual(self.bot.is_published, 1)
