"""End-to-end integration flow test.

Tests a complete multi-step conversation flow where:
1. Bot asks user for an order ID (pauses).
2. User provides the ID on resume.
3. Flow calls an external integration action (mocked HTTP connector).
4. Flow unpacks the response, maps variables, and continues to completion.
Pure Python, zero Frappe imports.
"""

from unittest.mock import MagicMock, patch
import unittest
from universal_chatbot.connectors.rest.frappe_connector import FrappeRestConnector
from universal_chatbot.core.protocol import IncomingMessage
from universal_chatbot.flow.engine import FlowExecutor
from universal_chatbot.flow.schema import (
    ExecutionStatus,
    FlowDefinition,
    NodeDefinition,
    TransitionDefinition,
    VariableDefinition,
)


class TestEndToEndIntegrationFlow(unittest.TestCase):
    def setUp(self):
        self.executor = FlowExecutor()

    def build_order_lookup_flow(self, connector) -> FlowDefinition:
        nodes = {
            "node_start": NodeDefinition(
                node_id="node_start",
                node_type="Start",
                configuration={"message": "Welcome to the Order Tracking Assistant."},
            ),
            "node_ask_order": NodeDefinition(
                node_id="node_ask_order",
                node_type="Ask Question",
                configuration={
                    "question": "Please provide your order number:",
                    "save_to_variable": "input_order_id",
                },
            ),
            "node_call_action": NodeDefinition(
                node_id="node_call_action",
                node_type="Call Action",
                configuration={
                    "action_name": "get_doc",
                    "connector": connector,
                    "parameters": {"doctype": "Sales Order", "docname": "{input_order_id}"},
                    "input_schema": {"required": ["doctype", "docname"]},
                    "output_mapping": {
                        "order_status": "unpacked.status",
                        "customer_name": "unpacked.customer",
                        "total_amount": "unpacked.grand_total",
                    },
                },
            ),
            "node_confirmation": NodeDefinition(
                node_id="node_confirmation",
                node_type="Send Message",
                configuration={
                    "text": "Order #{input_order_id} for {customer_name} is currently '{order_status}' with total ${total_amount}."
                },
            ),
            "node_end": NodeDefinition(
                node_id="node_end",
                node_type="End",
                configuration={"message": "Have a wonderful day!"},
            ),
        }

        transitions = [
            TransitionDefinition(source_node="node_start", target_node="node_ask_order"),
            TransitionDefinition(source_node="node_ask_order", target_node="node_call_action"),
            TransitionDefinition(source_node="node_call_action", target_node="node_confirmation"),
            TransitionDefinition(source_node="node_confirmation", target_node="node_end"),
        ]

        variables = {
            "input_order_id": VariableDefinition(name="input_order_id", default_value=""),
            "order_status": VariableDefinition(name="order_status", default_value="Unknown"),
            "customer_name": VariableDefinition(name="customer_name", default_value=""),
            "total_amount": VariableDefinition(name="total_amount", default_value=0),
        }

        return FlowDefinition(
            flow_id="order_tracking_flow",
            name="Order Tracking Flow",
            nodes=nodes,
            transitions=transitions,
            variables=variables,
            start_node_id="node_start",
        )

    @patch("requests.request")
    def test_end_to_end_order_lookup_flow(self, mock_request):
        # 1. Setup mock remote ERPNext response
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": {
                "name": "SO-2026-9988",
                "customer": "Wayne Enterprises",
                "grand_total": 12500.00,
                "status": "In Transit",
            }
        }
        mock_resp.headers = {"Content-Type": "application/json"}
        mock_request.return_value = mock_resp

        # 2. Setup connector
        connector = FrappeRestConnector(
            config={"base_url": "https://erp.waynecorp.com"},
            credentials={"api_key": "bat_key", "api_secret": "bat_secret"},
        )

        flow = self.build_order_lookup_flow(connector)

        # 3. Initial execution: Start -> Ask Question (pause)
        step1 = self.executor.execute(
            flow=flow,
            conversation_id="conv_e2e_001",
            state={},
        )

        self.assertEqual(step1.status, ExecutionStatus.PAUSED)
        self.assertEqual(step1.current_node_id, "node_ask_order")
        self.assertEqual(len(step1.messages), 2)
        self.assertEqual(step1.messages[1]["text"], "Please provide your order number:")

        # 4. User provides order ID "SO-2026-9988"
        incoming = IncomingMessage.create(
            bot_id="bot_track",
            deployment_id="dep_track",
            channel="web",
            external_user_id="user_bruce",
            text="SO-2026-9988",
            conversation_id="conv_e2e_001",
        )

        # 5. Resume execution from saved paused state
        saved_state = {
            "current_node": step1.current_node_id,
            "variables": step1.variables,
            "context": step1.context,
        }

        step2 = self.executor.execute(
            flow=flow,
            conversation_id="conv_e2e_001",
            state=saved_state,
            incoming_message=incoming,
        )

        # 6. Verify connector call
        mock_request.assert_called_once()
        call_kwargs = mock_request.call_args[1]
        self.assertEqual(call_kwargs["url"], "https://erp.waynecorp.com/api/resource/Sales Order/SO-2026-9988")
        self.assertEqual(call_kwargs["headers"]["Authorization"], "token bat_key:bat_secret")

        # 7. Verify flow completed and variables correctly mapped
        self.assertEqual(step2.status, ExecutionStatus.COMPLETED)
        self.assertEqual(step2.variables["input_order_id"], "SO-2026-9988")
        self.assertEqual(step2.variables["customer_name"], "Wayne Enterprises")
        self.assertEqual(step2.variables["order_status"], "In Transit")
        self.assertEqual(step2.variables["total_amount"], 12500.00)

        # 8. Verify formatted output messages emitted by confirmation & end nodes
        msg_texts = [m["text"] for m in step2.messages]
        self.assertIn(
            "Order #SO-2026-9988 for Wayne Enterprises is currently 'In Transit' with total $12500.0.",
            msg_texts,
        )
        self.assertIn("Have a wonderful day!", msg_texts)


if __name__ == "__main__":
    unittest.main()
