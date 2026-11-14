"""Call Action node implementation.

Invokes the Connector Framework to execute external system operations,
validates input schemas, and maps JSON response paths to flow variables.
Strict Architectural Rule: Pure Python, zero Frappe imports.
"""

from typing import Any, Dict, List, Optional
from universal_chatbot.connectors.base import BaseConnector
from universal_chatbot.flow.base import BaseFlowNode, NodeExecutionContext, NodeResult
from universal_chatbot.flow.evaluator import interpolate_template
from universal_chatbot.flow.registry import register_node


def extract_by_path(data: Any, path: str) -> Any:
    """Extract nested value from dictionary/list using dot notation (e.g. 'data.customer_name')."""
    if not path or path in (".", "$"):
        return data

    parts = path.split(".")
    curr = data
    for part in parts:
        if isinstance(curr, dict):
            curr = curr.get(part)
        elif isinstance(curr, (list, tuple)) and part.isdigit():
            idx = int(part)
            curr = curr[idx] if 0 <= idx < len(curr) else None
        else:
            return None
    return curr


@register_node("Call Action")
class CallActionNode(BaseFlowNode):
    """Executes a connector action and stores mapped response fields into variables."""

    def execute(self, context: NodeExecutionContext) -> NodeResult:
        action_name = self.config.get("action_name", "")
        raw_params: Dict[str, Any] = self.config.get("parameters", {})
        input_schema: Dict[str, Any] = self.config.get("input_schema", {})
        output_mapping: Dict[str, str] = self.config.get("output_mapping", {})
        save_all_var = self.config.get("save_result_to_variable") or self.config.get("result_variable")

        # 1. Resolve parameters from NodeExecutionContext variables overlaid with context
        combined_scope = dict(context.context or {})
        combined_scope.update(context.variables or {})
        # Also provide a nested 'context' key so {{context.channel}} or {{channel}} both work
        combined_scope["context"] = dict(context.context or {})

        resolved_params: Dict[str, Any] = {}
        for k, v in raw_params.items():
            if isinstance(v, str):
                resolved_params[k] = interpolate_template(v, combined_scope)
            else:
                resolved_params[k] = v

        # 2. Validate parameters against input_schema
        required_fields: List[str] = input_schema.get("required", []) if isinstance(input_schema, dict) else []
        for req in required_fields:
            val = resolved_params.get(req)
            if val is None or val == "":
                return NodeResult.fail_flow(
                    f"Action '{action_name}' missing required parameter '{req}'"
                )

        # 3. Execute via Connector or Context Action Executor
        result_data: Dict[str, Any] = {}
        connector: Optional[BaseConnector] = self.config.get("connector")

        try:
            if connector and isinstance(connector, BaseConnector):
                result_data = connector.execute(action_name, resolved_params)
            elif context.action_executor:
                try:
                    result_data = context.action_executor(
                        action_name, resolved_params, conversation_id=context.conversation_id
                    )
                except TypeError:
                    result_data = context.action_executor(action_name, resolved_params)
            else:
                result_data = {
                    "success": True,
                    "status_code": 200,
                    "data": {"status": "mock_executed", "action": action_name, "parameters": resolved_params},
                }
        except Exception as e:
            if self.config.get("fail_on_error", True):
                return NodeResult.fail_flow(f"Action '{action_name}' execution failed: {str(e)}")
            result_data = {"success": False, "error": str(e)}

        # 4. Map JSON response back into flow variables using output_mapping
        var_updates: Dict[str, Any] = {}

        if save_all_var:
            var_updates[save_all_var] = result_data

        effective_output_mapping = output_mapping or result_data.get("_action_output_mapping") or {}
        if isinstance(effective_output_mapping, dict) and effective_output_mapping:
            for target_var, response_path in effective_output_mapping.items():
                # Search unpacked.data first, then unpacked, then data, then root
                mapped_val = None
                if isinstance(result_data.get("unpacked"), dict):
                    mapped_val = extract_by_path(result_data.get("unpacked", {}).get("data"), response_path)
                    if mapped_val is None:
                        mapped_val = extract_by_path(result_data.get("unpacked"), response_path)
                if mapped_val is None and isinstance(result_data.get("data"), dict):
                    mapped_val = extract_by_path(result_data.get("data", {}).get("data"), response_path)
                    if mapped_val is None:
                        mapped_val = extract_by_path(result_data.get("data"), response_path)
                if mapped_val is None:
                    mapped_val = extract_by_path(result_data, response_path)

                var_updates[target_var] = mapped_val

        return NodeResult.continue_flow(variable_updates=var_updates)
