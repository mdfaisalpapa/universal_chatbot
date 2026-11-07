"""End node implementation."""

from universal_chatbot.flow.base import BaseFlowNode, NodeExecutionContext, NodeResult
from universal_chatbot.flow.evaluator import interpolate_template
from universal_chatbot.flow.registry import register_node


@register_node("End")
class EndNode(BaseFlowNode):
    """Terminates flow execution and marks conversation as completed."""

    def execute(self, context: NodeExecutionContext) -> NodeResult:
        closing_msg = self.config.get("message") or self.config.get("text")
        msgs = []
        if closing_msg:
            rendered = interpolate_template(closing_msg, context.variables)
            msgs.append({"type": "text", "text": rendered})

        return NodeResult.complete_flow(outgoing_messages=msgs)
