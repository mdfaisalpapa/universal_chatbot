"""Start node implementation."""

from universal_chatbot.flow.base import BaseFlowNode, NodeExecutionContext, NodeResult
from universal_chatbot.flow.evaluator import interpolate_template
from universal_chatbot.flow.registry import register_node


@register_node("Start")
class StartNode(BaseFlowNode):
    """Entry point node for the flow execution."""

    def execute(self, context: NodeExecutionContext) -> NodeResult:
        message = self.config.get("message")
        msgs = []
        if message:
            rendered = interpolate_template(message, context.variables)
            msgs.append({"type": "text", "text": rendered})
        return NodeResult.continue_flow(outgoing_messages=msgs)
