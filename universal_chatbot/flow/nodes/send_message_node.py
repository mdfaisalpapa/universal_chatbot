"""Send Message node implementation."""

from universal_chatbot.flow.base import BaseFlowNode, NodeExecutionContext, NodeResult
from universal_chatbot.flow.evaluator import interpolate_template
from universal_chatbot.flow.registry import register_node


@register_node("Send Message")
class SendMessageNode(BaseFlowNode):
    """Emits an outgoing text/card message and continues flow."""

    def execute(self, context: NodeExecutionContext) -> NodeResult:
        template = self.config.get("text", "")
        rendered = interpolate_template(template, context.variables)
        msg_type = self.config.get("message_type", "text")

        payload = {"type": msg_type, "text": rendered}
        if "card" in self.config:
            payload["card"] = self.config["card"]

        return NodeResult.continue_flow(outgoing_messages=[payload])
