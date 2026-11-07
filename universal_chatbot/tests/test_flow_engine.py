"""Pure Python unit tests for the rule-based Flow Engine.

Verifies node execution, condition evaluation, template interpolation,
pausing for input, and resuming accurately on incoming messages.
Zero frappe dependencies.
"""

import unittest
from universal_chatbot.core.protocol import IncomingMessage
from universal_chatbot.flow.engine import FlowExecutor
from universal_chatbot.flow.evaluator import SafeConditionEvaluator, interpolate_template
from universal_chatbot.flow.schema import (
    ExecutionStatus,
    FlowDefinition,
    NodeDefinition,
    TransitionDefinition,
    VariableDefinition,
)


class TestSafeEvaluator(unittest.TestCase):
    def test_interpolate_template(self):
        vars_dict = {"name": "Alice", "order_id": "ORD-12345", "count": 3}
        text = "Hello {name}, your order #{{order_id}} has {count} items."
        res = interpolate_template(text, vars_dict)
        self.assertEqual(res, "Hello Alice, your order #ORD-12345 has 3 items.")

    def test_condition_evaluation_dict(self):
        vars_dict = {"dept": "support", "score": 85, "active": True}

        self.assertTrue(SafeConditionEvaluator.evaluate({"variable": "dept", "operator": "==", "value": "support"}, vars_dict))
        self.assertFalse(SafeConditionEvaluator.evaluate({"variable": "dept", "operator": "==", "value": "sales"}, vars_dict))
        self.assertTrue(SafeConditionEvaluator.evaluate({"variable": "score", "operator": ">=", "value": 80}, vars_dict))
        self.assertFalse(SafeConditionEvaluator.evaluate({"variable": "score", "operator": "<", "value": 50}, vars_dict))

        # Compound rules
        all_rule = {
            "all": [
                {"variable": "dept", "operator": "==", "value": "support"},
                {"variable": "score", "operator": ">=", "value": 50},
            ]
        }
        self.assertTrue(SafeConditionEvaluator.evaluate(all_rule, vars_dict))

    def test_condition_evaluation_expression_string(self):
        vars_dict = {"age": 25, "role": "admin"}
        self.assertTrue(SafeConditionEvaluator.evaluate("age > 18 and role == 'admin'", vars_dict))
        self.assertFalse(SafeConditionEvaluator.evaluate("age < 18 or role == 'guest'", vars_dict))
        self.assertTrue(SafeConditionEvaluator.evaluate("default", vars_dict))
        self.assertTrue(SafeConditionEvaluator.evaluate("", vars_dict))


class TestFlowExecutor(unittest.TestCase):
    def setUp(self):
        self.executor = FlowExecutor()

    def build_test_flow(self) -> FlowDefinition:
        """Constructs a test flow graph:

        Start -> Send Message (welcome) -> Ask Question (user_name) [PAUSES]
        -> Multiple Choice (inquiry_type) [PAUSES]
        -> Condition (branch to support vs sales)
           -> Support Branch: Set Variable (priority=high) -> Call Action (fetch_ticket) -> End
           -> Sales Branch: Set Variable (priority=standard) -> End
        """
        nodes = {
            "node_start": NodeDefinition(
                node_id="node_start",
                node_type="Start",
                configuration={"message": "Welcome to Universal Chatbot!"},
            ),
            "node_welcome": NodeDefinition(
                node_id="node_welcome",
                node_type="Send Message",
                configuration={"text": "I will assist you today."},
            ),
            "node_ask_name": NodeDefinition(
                node_id="node_ask_name",
                node_type="Ask Question",
                configuration={"question": "What is your name?", "save_to_variable": "user_name"},
            ),
            "node_choice": NodeDefinition(
                node_id="node_choice",
                node_type="Multiple Choice",
                configuration={
                    "prompt": "Hello {user_name}, what can we help you with?",
                    "save_to_variable": "inquiry_type",
                    "options": [
                        {"label": "Support", "value": "support"},
                        {"label": "Sales", "value": "sales"},
                    ],
                },
            ),
            "node_condition": NodeDefinition(
                node_id="node_condition",
                node_type="Condition",
                configuration={
                    "branches": [
                        {
                            "condition": {"variable": "inquiry_type", "operator": "==", "value": "support"},
                            "target_node": "node_support_action",
                        },
                        {
                            "condition": {"variable": "inquiry_type", "operator": "==", "value": "sales"},
                            "target_node": "node_sales_branch",
                        },
                    ],
                    "default_target_node": "node_end",
                },
            ),
            "node_support_action": NodeDefinition(
                node_id="node_support_action",
                node_type="Call Action",
                configuration={
                    "action_name": "lookup_customer_tier",
                    "parameters": {"user": "{user_name}"},
                    "save_result_to_variable": "tier_data",
                },
            ),
            "node_sales_branch": NodeDefinition(
                node_id="node_sales_branch",
                node_type="Set Variable",
                configuration={"variables": {"discount_rate": "15%"}},
            ),
            "node_end": NodeDefinition(
                node_id="node_end",
                node_type="End",
                configuration={"message": "Thank you {user_name}! Goodbye."},
            ),
        }

        transitions = [
            TransitionDefinition(source_node="node_start", target_node="node_welcome"),
            TransitionDefinition(source_node="node_welcome", target_node="node_ask_name"),
            TransitionDefinition(source_node="node_ask_name", target_node="node_choice"),
            TransitionDefinition(source_node="node_choice", target_node="node_condition"),
            TransitionDefinition(source_node="node_support_action", target_node="node_end"),
            TransitionDefinition(source_node="node_sales_branch", target_node="node_end"),
        ]

        variables = {
            "user_name": VariableDefinition(name="user_name", default_value="Guest"),
            "inquiry_type": VariableDefinition(name="inquiry_type", default_value="general"),
        }

        return FlowDefinition(
            flow_id="test_support_flow",
            name="Customer Support Flow",
            version="1.0.0",
            nodes=nodes,
            transitions=transitions,
            variables=variables,
            start_node_id="node_start",
        )

    def test_flow_traversal_and_pause_on_ask_question(self):
        flow = self.build_test_flow()

        # Step 1: Initial execution from Start
        res = self.executor.execute(
            flow=flow,
            conversation_id="conv_100",
            state={},
        )

        # Should traverse Start -> Send Message -> Ask Question and PAUSE
        self.assertEqual(res.status, ExecutionStatus.PAUSED)
        self.assertEqual(res.current_node_id, "node_ask_name")
        self.assertEqual(len(res.messages), 3)
        self.assertEqual(res.messages[0]["text"], "Welcome to Universal Chatbot!")
        self.assertEqual(res.messages[1]["text"], "I will assist you today.")
        self.assertEqual(res.messages[2]["text"], "What is your name?")

    def test_flow_resume_and_multiple_choice_pause(self):
        flow = self.build_test_flow()

        # Step 1: Paused at Ask Question
        state = {
            "current_node": "node_ask_name",
            "variables": {"user_name": "Guest"},
            "context": {},
        }

        incoming_reply = IncomingMessage.create(
            bot_id="bot1",
            deployment_id="dep1",
            channel="web",
            external_user_id="user1",
            text="Alice",
            conversation_id="conv_100",
        )

        # Step 2: Resume with user answer "Alice"
        res = self.executor.execute(
            flow=flow,
            conversation_id="conv_100",
            state=state,
            incoming_message=incoming_reply,
        )

        # Should save user_name="Alice", traverse to Multiple Choice and PAUSE
        self.assertEqual(res.status, ExecutionStatus.PAUSED)
        self.assertEqual(res.current_node_id, "node_choice")
        self.assertEqual(res.variables["user_name"], "Alice")
        self.assertEqual(len(res.messages), 1)
        self.assertEqual(res.messages[0]["type"], "options")
        self.assertEqual(res.messages[0]["text"], "Hello Alice, what can we help you with?")

    def test_flow_resume_multiple_choice_and_complete_via_condition(self):
        flow = self.build_test_flow()

        # Step 2: Paused at Multiple Choice with user_name="Alice"
        state = {
            "current_node": "node_choice",
            "variables": {"user_name": "Alice"},
            "context": {},
        }

        incoming_choice = IncomingMessage.create(
            bot_id="bot1",
            deployment_id="dep1",
            channel="web",
            external_user_id="user1",
            text="support",
            conversation_id="conv_100",
        )

        def mock_action_executor(action_name, params):
            self.assertEqual(action_name, "lookup_customer_tier")
            self.assertEqual(params["user"], "Alice")
            return {"tier": "Gold", "status": "active"}

        # Step 3: Resume with choice "support"
        res = self.executor.execute(
            flow=flow,
            conversation_id="conv_100",
            state=state,
            incoming_message=incoming_choice,
            action_executor=mock_action_executor,
        )

        # Should branch via Condition to Call Action -> End (COMPLETED)
        self.assertEqual(res.status, ExecutionStatus.COMPLETED)
        self.assertEqual(res.current_node_id, "node_end")
        self.assertEqual(res.variables["inquiry_type"], "support")
        self.assertEqual(res.variables["tier_data"]["tier"], "Gold")
        self.assertEqual(len(res.messages), 1)
        self.assertEqual(res.messages[0]["text"], "Thank you Alice! Goodbye.")

    def test_flow_resume_sales_branch(self):
        flow = self.build_test_flow()

        state = {
            "current_node": "node_choice",
            "variables": {"user_name": "Bob"},
            "context": {},
        }

        incoming_choice = IncomingMessage.create(
            bot_id="bot1",
            deployment_id="dep1",
            channel="web",
            external_user_id="user2",
            text="Sales",
            conversation_id="conv_101",
        )

        res = self.executor.execute(
            flow=flow,
            conversation_id="conv_101",
            state=state,
            incoming_message=incoming_choice,
        )

        # Should branch via Condition to Set Variable (discount_rate=15%) -> End
        self.assertEqual(res.status, ExecutionStatus.COMPLETED)
        self.assertEqual(res.variables["discount_rate"], "15%")
        self.assertEqual(res.messages[0]["text"], "Thank you Bob! Goodbye.")


if __name__ == "__main__":
    unittest.main()
