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

        # Test deleting the End node and creating a looping flow
        looping_payload = {
            "flow_name": self.flow.name,
            "nodes": [
                {
                    "node_id": "start_node",
                    "node_type": "start",
                    "x": 120,
                    "y": 80,
                    "configuration": {"message": "Welcome!"},
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
            ],
            "transitions": [
                {"source_node": "start_node", "target_node": "ask_user"},
                {"source_node": "ask_user", "target_node": "start_node"},  # Looping transition
            ],
            "variables": [
                {"variable_name": "order_id", "data_type": "String", "default_value": ""},
            ],
        }

        # Saving should cleanly delete goodbye node without LinkExistsError
        update_res = save_visual_flow(self.flow.name, looping_payload)
        self.assertEqual(update_res["status"], "success")
        self.assertEqual(update_res["nodes_count"], 2)
        self.assertEqual(update_res["transitions_count"], 2)

        # Verify goodbye node is gone
        loaded_loop = load_visual_flow(self.flow.name)
        node_ids = [n["node_id"] for n in loaded_loop["nodes"]]
        self.assertNotIn("goodbye", node_ids)
        self.assertIn("start_node", node_ids)
        self.assertIn("ask_user", node_ids)

        loop_pairs = [(t["source_node"], t["target_node"]) for t in loaded_loop["transitions"]]
        self.assertIn(("ask_user", "start_node"), loop_pairs)

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

    def test_call_action_node_configuration_structure_and_execution(self):
        """Verify that Call Action node JSON structure generated by the Quick Form integrates with CallActionNode."""
        from universal_chatbot.flow.base import NodeExecutionContext
        from universal_chatbot.flow.nodes.call_action_node import CallActionNode

        call_action_config = {
            "action_name": "get_maintenance_dues",
            "parameters": {
                "flat_number": "{{user_flat}}"
            },
            "output_mapping": {
                "outstanding_dues": "data.message.outstanding_amount",
                "owner_name": "data.message.owner_name"
            }
        }

        flow_payload = {
            "nodes": [
                {"node_id": "start", "node_type": "start", "configuration": {}},
                {"node_id": "ask_flat", "node_type": "ask_question", "configuration": {"prompt": "Flat number?", "save_to_variable": "user_flat"}},
                {"node_id": "call_api", "node_type": "call_action", "configuration": call_action_config},
                {"node_id": "send_msg", "node_type": "send_message", "configuration": {"message": "Dues: {{outstanding_dues}}"}},
                {"node_id": "end", "node_type": "end", "configuration": {}},
            ],
            "transitions": [
                {"source_node": "start", "target_node": "ask_flat"},
                {"source_node": "ask_flat", "target_node": "call_api"},
                {"source_node": "call_api", "target_node": "send_msg"},
                {"source_node": "send_msg", "target_node": "end"},
            ],
            "variables": [],
        }

        # Save and verify
        save_res = save_visual_flow(self.flow.name, flow_payload)
        self.assertEqual(save_res["status"], "success")

        loaded = load_visual_flow(self.flow.name)
        call_node_loaded = next(n for n in loaded["nodes"] if n["node_id"] == "call_api")
        self.assertEqual(call_node_loaded["configuration"]["action_name"], "get_maintenance_dues")
        self.assertEqual(call_node_loaded["configuration"]["parameters"]["flat_number"], "{{user_flat}}")
        self.assertEqual(call_node_loaded["configuration"]["output_mapping"]["outstanding_dues"], "data.message.outstanding_amount")

        # Test execution engine with CallActionNode
        mock_executor = lambda action, params, **kwargs: {
            "success": True,
            "data": {
                "message": {
                    "outstanding_amount": "₹ 2,940.00",
                    "owner_name": "PRAVEEN KUMAR"
                }
            }
        }
        ctx = NodeExecutionContext(
            conversation_id="test_conv",
            variables={"user_flat": "TB2-203"},
            action_executor=mock_executor
        )
        node_instance = CallActionNode(node_id="call_api", configuration=call_action_config)
        result = node_instance.execute(ctx)

        self.assertIsNone(result.error)
        self.assertEqual(result.variable_updates.get("outstanding_dues"), "₹ 2,940.00")
        self.assertEqual(result.variable_updates.get("owner_name"), "PRAVEEN KUMAR")

    def test_test_integration_action_endpoint(self):
        """Verify the test_integration_action dry-run endpoint returns schema results."""
        from universal_chatbot.api.v1.flow_designer import test_integration_action

        # Nonexistent action should return error status gracefully
        res_err = test_integration_action("nonexistent_action_xyz", {"foo": "bar"})
        self.assertEqual(res_err["status"], "error")
        self.assertIn("not configured", res_err["message"])

        # If get_maintenance_dues action exists on chatbot.local, test it with mocked response or live call
        if frappe.db.exists("Integration Action", {"action_name": "get_maintenance_dues"}):
            from unittest.mock import patch
            mock_resp = {
                "success": True,
                "status_code": 200,
                "data": {"message": {"flat_number": "TB2-203", "outstanding_amount": "₹ 2,940.00"}},
            }
            with patch(
                "universal_chatbot.adapters.frappe_repository.FrappeConversationRepository.execute_action",
                return_value=mock_resp,
            ):
                res = test_integration_action("get_maintenance_dues", {"flat_number": "TB2-203"})
                self.assertEqual(res["status"], "success")
                self.assertIn("data", res["result"])
