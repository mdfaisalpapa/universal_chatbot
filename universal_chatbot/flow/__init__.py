"""Flow processing and rule-based execution engine package.

Strict Architectural Rule:
Do not import `frappe` here.
"""

from universal_chatbot.flow.base import BaseFlowNode, NodeExecutionContext, NodeResult
from universal_chatbot.flow.engine import FlowExecutionResult, FlowExecutor
from universal_chatbot.flow.evaluator import SafeConditionEvaluator, interpolate_template
from universal_chatbot.flow.registry import NodeRegistry, register_node
from universal_chatbot.flow.schema import (
    ExecutionStatus,
    FlowDefinition,
    FlowNodeType,
    NodeDefinition,
    TransitionDefinition,
    VariableDefinition,
)

__all__ = [
    "BaseFlowNode",
    "NodeExecutionContext",
    "NodeResult",
    "FlowExecutor",
    "FlowExecutionResult",
    "SafeConditionEvaluator",
    "interpolate_template",
    "NodeRegistry",
    "register_node",
    "FlowDefinition",
    "NodeDefinition",
    "TransitionDefinition",
    "VariableDefinition",
    "ExecutionStatus",
    "FlowNodeType",
]
