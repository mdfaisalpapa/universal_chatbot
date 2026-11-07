"""Multiple Choice node implementation."""

from typing import Any, Dict, List
from universal_chatbot.flow.base import BaseFlowNode, NodeExecutionContext, NodeResult
from universal_chatbot.flow.evaluator import interpolate_template
from universal_chatbot.flow.registry import register_node


@register_node("Multiple Choice")
class MultipleChoiceNode(BaseFlowNode):
    """Presents user with multiple options and pauses flow until selection."""

    def execute(self, context: NodeExecutionContext) -> NodeResult:
        prompt_text = self.config.get("prompt") or self.config.get("text", "Please select an option:")
        rendered = interpolate_template(prompt_text, context.variables)

        raw_options: List[Dict[str, Any]] = self.config.get("options", [])
        rendered_options = []
        for opt in raw_options:
            label = interpolate_template(opt.get("label", ""), context.variables)
            val = opt.get("value", label)
            rendered_options.append({"label": label, "value": val})

        msg = {
            "type": "options",
            "text": rendered,
            "options": rendered_options,
        }
        return NodeResult.pause_flow(outgoing_messages=[msg])

    def resume(self, context: NodeExecutionContext) -> NodeResult:
        save_var = self.config.get("save_to_variable") or self.config.get("variable_name", "user_choice")
        user_input = ""
        if context.incoming_message:
            msg_data = context.incoming_message.message or {}
            user_input = str(msg_data.get("text", "")).strip()

        # Match option
        raw_options = self.config.get("options", [])
        matched_value = user_input
        matched_target_node = None

        for opt in raw_options:
            val = str(opt.get("value", "")).strip()
            lbl = str(opt.get("label", "")).strip()
            if user_input.lower() in (val.lower(), lbl.lower()):
                matched_value = val
                matched_target_node = opt.get("target_node")
                break

        updates = {save_var: matched_value}
        return NodeResult.continue_flow(
            variable_updates=updates,
            next_node_override=matched_target_node,
        )
