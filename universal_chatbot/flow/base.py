"""Base classes and execution contexts for Flow Nodes.

Pure Python, zero framework dependencies.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from universal_chatbot.core.protocol import IncomingMessage
from universal_chatbot.flow.schema import ExecutionStatus


@dataclass
class NodeExecutionContext:
    """Carries conversation variables, context, and user input for node execution."""

    conversation_id: str
    variables: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    incoming_message: Optional[IncomingMessage] = None
    action_executor: Optional[Callable[[str, Dict[str, Any]], Dict[str, Any]]] = None

    def get_var(self, name: str, default: Any = None) -> Any:
        return self.variables.get(name, default)

    def set_var(self, name: str, value: Any) -> None:
        self.variables[name] = value


@dataclass
class NodeResult:
    """Outcome of executing or resuming a flow node."""

    status: ExecutionStatus = ExecutionStatus.RUNNING
    outgoing_messages: List[Dict[str, Any]] = field(default_factory=list)
    variable_updates: Dict[str, Any] = field(default_factory=dict)
    context_updates: Dict[str, Any] = field(default_factory=dict)
    next_node_override: Optional[str] = None
    error: Optional[str] = None

    @classmethod
    def continue_flow(
        cls,
        outgoing_messages: Optional[List[Dict[str, Any]]] = None,
        variable_updates: Optional[Dict[str, Any]] = None,
        next_node_override: Optional[str] = None,
    ) -> "NodeResult":
        return cls(
            status=ExecutionStatus.RUNNING,
            outgoing_messages=outgoing_messages or [],
            variable_updates=variable_updates or {},
            next_node_override=next_node_override,
        )

    @classmethod
    def pause_flow(
        cls,
        outgoing_messages: Optional[List[Dict[str, Any]]] = None,
        variable_updates: Optional[Dict[str, Any]] = None,
    ) -> "NodeResult":
        return cls(
            status=ExecutionStatus.PAUSED,
            outgoing_messages=outgoing_messages or [],
            variable_updates=variable_updates or {},
        )

    @classmethod
    def complete_flow(
        cls,
        outgoing_messages: Optional[List[Dict[str, Any]]] = None,
        variable_updates: Optional[Dict[str, Any]] = None,
    ) -> "NodeResult":
        return cls(
            status=ExecutionStatus.COMPLETED,
            outgoing_messages=outgoing_messages or [],
            variable_updates=variable_updates or {},
        )

    @classmethod
    def fail_flow(cls, error: str) -> "NodeResult":
        return cls(status=ExecutionStatus.FAILED, error=error)


class BaseFlowNode(ABC):
    """Abstract base class for all Flow node types."""

    node_type: str = "Base"

    def __init__(self, node_id: str, configuration: Optional[Dict[str, Any]] = None):
        self.node_id = node_id
        self.config = configuration or {}

    @abstractmethod
    def execute(self, context: NodeExecutionContext) -> NodeResult:
        """Execute node when entered."""
        pass

    def resume(self, context: NodeExecutionContext) -> NodeResult:
        """Handle incoming user reply when flow was paused on this node.

        Default implementation resumes by continuing to next node.
        """
        return NodeResult.continue_flow()
