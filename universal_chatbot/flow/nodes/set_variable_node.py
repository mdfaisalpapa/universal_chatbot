"""Set Variable node implementation."""

from typing import Any, Dict
from universal_chatbot.flow.base import BaseFlowNode, NodeExecutionContext, NodeResult
from universal_chatbot.flow.evaluator import interpolate_template
from universal_chatbot.flow.registry import register_node


@register_node("Set Variable")
class SetVariableNode(BaseFlowNode):
    """Sets or updates conversation variables."""

    def execute(self, context: NodeExecutionContext) -> NodeResult:
        updates: Dict[str, Any] = {}

        # Format 1: single variable & value
        var_name = self.config.get("variable_name")
        if var_name:
            val = self.config.get("value")
            if isinstance(val, str):
                val = interpolate_template(val, context.variables)
            updates[var_name] = val

        # Format 2: dictionary of variables
        vars_dict = self.config.get("variables", {})
        for k, v in vars_dict.items():
            if isinstance(v, str):
                v = interpolate_template(v, context.variables)
            updates[k] = v

        return NodeResult.continue_flow(variable_updates=updates)
