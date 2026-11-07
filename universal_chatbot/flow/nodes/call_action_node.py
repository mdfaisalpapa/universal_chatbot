"""Call Action node implementation."""

from typing import Any, Dict
from universal_chatbot.flow.base import BaseFlowNode, NodeExecutionContext, NodeResult
from universal_chatbot.flow.evaluator import interpolate_template
from universal_chatbot.flow.registry import register_node


@register_node("Call Action")
class CallActionNode(BaseFlowNode):
    """Executes a connector action and stores the response in variables."""

    def execute(self, context: NodeExecutionContext) -> NodeResult:
        action_name = self.config.get("action_name", "")
        raw_params: Dict[str, Any] = self.config.get("parameters", {})
        save_to = self.config.get("save_result_to_variable") or self.config.get("result_variable", "action_result")

        # Resolve parameter templates
        resolved_params = {}
        for k, v in raw_params.items():
            if isinstance(v, str):
                resolved_params[k] = interpolate_template(v, context.variables)
            else:
                resolved_params[k] = v

        result_data: Dict[str, Any] = {}
        if context.action_executor:
            try:
                result_data = context.action_executor(action_name, resolved_params)
            except Exception as e:
                if self.config.get("fail_on_error", False):
                    return NodeResult.fail_flow(f"Action '{action_name}' execution failed: {str(e)}")
                result_data = {"error": str(e), "success": False}
        else:
            result_data = {"status": "mock_executed", "action": action_name, "parameters": resolved_params}

        return NodeResult.continue_flow(variable_updates={save_to: result_data})
