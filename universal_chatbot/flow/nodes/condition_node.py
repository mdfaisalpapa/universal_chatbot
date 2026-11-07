"""Condition branching node implementation."""

from typing import Any, Dict, List
from universal_chatbot.flow.base import BaseFlowNode, NodeExecutionContext, NodeResult
from universal_chatbot.flow.evaluator import SafeConditionEvaluator
from universal_chatbot.flow.registry import register_node


@register_node("Condition")
class ConditionNode(BaseFlowNode):
    """Evaluates branching conditions to dynamically select the next node."""

    def execute(self, context: NodeExecutionContext) -> NodeResult:
        branches: List[Dict[str, Any]] = self.config.get("branches", [])
        matched_target = None

        for branch in branches:
            condition = branch.get("condition")
            if SafeConditionEvaluator.evaluate(condition, context.variables):
                matched_target = branch.get("target_node")
                break

        if not matched_target:
            matched_target = self.config.get("default_target_node") or self.config.get("else_target_node")

        return NodeResult.continue_flow(next_node_override=matched_target)
