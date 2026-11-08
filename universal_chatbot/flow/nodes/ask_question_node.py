"""Ask Question node implementation."""

from universal_chatbot.flow.base import BaseFlowNode, NodeExecutionContext, NodeResult
from universal_chatbot.flow.evaluator import interpolate_template
from universal_chatbot.flow.registry import register_node


@register_node("Ask Question")
class AskQuestionNode(BaseFlowNode):
    """Asks the user a freeform question and pauses flow until reply."""

    def execute(self, context: NodeExecutionContext) -> NodeResult:
        question_text = (
            self.config.get("question")
            or self.config.get("prompt")
            or self.config.get("text")
            or self.config.get("message", "")
        )
        rendered = interpolate_template(question_text, context.variables)

        msg = {
            "type": "text",
            "text": rendered,
            "input_type": self.config.get("input_type", "text"),
        }
        return NodeResult.pause_flow(outgoing_messages=[msg])

    def resume(self, context: NodeExecutionContext) -> NodeResult:
        """When user replies, extract input and assign to variable."""
        save_var = self.config.get("save_to_variable") or self.config.get("variable_name")
        user_input = ""
        if context.incoming_message:
            msg_data = context.incoming_message.message or {}
            user_input = str(msg_data.get("text", "")).strip()

        updates = {}
        if save_var:
            updates[save_var] = user_input

        return NodeResult.continue_flow(variable_updates=updates)
