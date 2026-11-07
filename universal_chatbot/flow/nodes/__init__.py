"""Flow nodes package.

Imports and registers all Phase 1 node types into NodeRegistry.
Strict Architectural Rule: Do not import frappe here.
"""

from universal_chatbot.flow.nodes.start_node import StartNode
from universal_chatbot.flow.nodes.send_message_node import SendMessageNode
from universal_chatbot.flow.nodes.ask_question_node import AskQuestionNode
from universal_chatbot.flow.nodes.multiple_choice_node import MultipleChoiceNode
from universal_chatbot.flow.nodes.condition_node import ConditionNode
from universal_chatbot.flow.nodes.set_variable_node import SetVariableNode
from universal_chatbot.flow.nodes.call_action_node import CallActionNode
from universal_chatbot.flow.nodes.end_node import EndNode

__all__ = [
    "StartNode",
    "SendMessageNode",
    "AskQuestionNode",
    "MultipleChoiceNode",
    "ConditionNode",
    "SetVariableNode",
    "CallActionNode",
    "EndNode",
]
