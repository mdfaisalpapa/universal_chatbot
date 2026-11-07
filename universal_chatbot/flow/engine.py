"""Flow execution engine.

Orchestrates node traversal, condition evaluation, state persistence,
pausing on interactive nodes, and accurate resumption.
Pure Python, zero framework dependencies.
"""

from typing import Any, Callable, Dict, List, Optional
from universal_chatbot.core.exceptions import FlowExecutionError
from universal_chatbot.core.protocol import IncomingMessage
from universal_chatbot.flow.base import NodeExecutionContext, NodeResult
from universal_chatbot.flow.evaluator import SafeConditionEvaluator
from universal_chatbot.flow.registry import NodeRegistry
from universal_chatbot.flow.schema import ExecutionStatus, FlowDefinition, NodeDefinition

# Ensure all standard nodes are registered
import universal_chatbot.flow.nodes  # noqa: F401


class FlowExecutionResult:
    """Standard execution result returned by FlowExecutor."""

    def __init__(
        self,
        conversation_id: str,
        status: ExecutionStatus,
        messages: List[Dict[str, Any]],
        variables: Dict[str, Any],
        context: Dict[str, Any],
        current_node_id: Optional[str] = None,
        error: Optional[str] = None,
    ):
        self.conversation_id = conversation_id
        self.status = status
        self.messages = messages
        self.variables = variables
        self.context = context
        self.current_node_id = current_node_id
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "status": self.status.value,
            "current_node_id": self.current_node_id,
            "messages": self.messages,
            "variables": self.variables,
            "context": self.context,
            "error": self.error,
        }


class FlowExecutor:
    """Core rule-based flow executor."""

    def __init__(self, max_steps: int = 100):
        self.max_steps = max_steps

    def execute(
        self,
        flow: FlowDefinition,
        conversation_id: str,
        state: Optional[Dict[str, Any]] = None,
        incoming_message: Optional[IncomingMessage] = None,
        action_executor: Optional[Callable[[str, Dict[str, Any]], Dict[str, Any]]] = None,
    ) -> FlowExecutionResult:
        """Execute or resume a conversation flow graph."""
        state = state or {}

        # 1. Initialize variables from default flow variables overlaid with state variables
        variables: Dict[str, Any] = {}
        for var_name, var_def in flow.variables.items():
            variables[var_name] = var_def.default_value
        variables.update(state.get("variables", {}))

        context_data = dict(state.get("context", {}))

        exec_context = NodeExecutionContext(
            conversation_id=conversation_id,
            variables=variables,
            context=context_data,
            incoming_message=incoming_message,
            action_executor=action_executor,
        )

        aggregated_messages: List[Dict[str, Any]] = []
        current_node_id = state.get("current_node")

        # 2. If resuming from a paused state
        next_node_id: Optional[str] = None
        if current_node_id and current_node_id in flow.nodes:
            paused_node_def = flow.nodes[current_node_id]
            node_instance = NodeRegistry.create(
                paused_node_def.node_type, paused_node_def.node_id, paused_node_def.configuration
            )

            resume_result = node_instance.resume(exec_context)
            exec_context.variables.update(resume_result.variable_updates)
            exec_context.context.update(resume_result.context_updates)
            if resume_result.outgoing_messages:
                aggregated_messages.extend(resume_result.outgoing_messages)

            if resume_result.status == ExecutionStatus.PAUSED:
                return FlowExecutionResult(
                    conversation_id=conversation_id,
                    status=ExecutionStatus.PAUSED,
                    messages=aggregated_messages,
                    variables=exec_context.variables,
                    context=exec_context.context,
                    current_node_id=current_node_id,
                )
            elif resume_result.status == ExecutionStatus.COMPLETED:
                return FlowExecutionResult(
                    conversation_id=conversation_id,
                    status=ExecutionStatus.COMPLETED,
                    messages=aggregated_messages,
                    variables=exec_context.variables,
                    context=exec_context.context,
                    current_node_id=current_node_id,
                )
            elif resume_result.status == ExecutionStatus.FAILED:
                return FlowExecutionResult(
                    conversation_id=conversation_id,
                    status=ExecutionStatus.FAILED,
                    messages=aggregated_messages,
                    variables=exec_context.variables,
                    context=exec_context.context,
                    current_node_id=current_node_id,
                    error=resume_result.error,
                )

            # Determine next node from resumed node
            next_node_id = resume_result.next_node_override or self._find_next_node(
                flow, current_node_id, exec_context.variables
            )
        else:
            # Fresh start: locate Start node
            start_node = self._find_start_node(flow)
            if not start_node:
                raise FlowExecutionError(f"Flow '{flow.flow_id}' has no valid Start node")
            next_node_id = start_node.node_id

        # 3. Main Traversal Loop
        steps = 0
        while next_node_id and steps < self.max_steps:
            steps += 1
            if next_node_id not in flow.nodes:
                raise FlowExecutionError(f"Target node '{next_node_id}' not found in flow definition")

            node_def = flow.nodes[next_node_id]
            node_instance = NodeRegistry.create(
                node_def.node_type, node_def.node_id, node_def.configuration
            )

            result = node_instance.execute(exec_context)
            exec_context.variables.update(result.variable_updates)
            exec_context.context.update(result.context_updates)
            if result.outgoing_messages:
                aggregated_messages.extend(result.outgoing_messages)

            if result.status == ExecutionStatus.PAUSED:
                # Pause execution and save current node
                return FlowExecutionResult(
                    conversation_id=conversation_id,
                    status=ExecutionStatus.PAUSED,
                    messages=aggregated_messages,
                    variables=exec_context.variables,
                    context=exec_context.context,
                    current_node_id=node_def.node_id,
                )

            if result.status == ExecutionStatus.COMPLETED:
                return FlowExecutionResult(
                    conversation_id=conversation_id,
                    status=ExecutionStatus.COMPLETED,
                    messages=aggregated_messages,
                    variables=exec_context.variables,
                    context=exec_context.context,
                    current_node_id=node_def.node_id,
                )

            if result.status == ExecutionStatus.FAILED:
                return FlowExecutionResult(
                    conversation_id=conversation_id,
                    status=ExecutionStatus.FAILED,
                    messages=aggregated_messages,
                    variables=exec_context.variables,
                    context=exec_context.context,
                    current_node_id=node_def.node_id,
                    error=result.error,
                )

            # Determine next node
            next_node_id = result.next_node_override or self._find_next_node(
                flow, node_def.node_id, exec_context.variables
            )

        if steps >= self.max_steps:
            raise FlowExecutionError(f"Flow exceeded maximum allowed steps ({self.max_steps}). Possible loop.")

        # Reached end of unlinked path
        return FlowExecutionResult(
            conversation_id=conversation_id,
            status=ExecutionStatus.COMPLETED,
            messages=aggregated_messages,
            variables=exec_context.variables,
            context=exec_context.context,
            current_node_id=current_node_id,
        )

    def _find_start_node(self, flow: FlowDefinition) -> Optional[NodeDefinition]:
        if flow.start_node_id and flow.start_node_id in flow.nodes:
            return flow.nodes[flow.start_node_id]
        for node in flow.nodes.values():
            if node.node_type == "Start":
                return node
        return None

    def _find_next_node(
        self, flow: FlowDefinition, current_node_id: str, variables: Dict[str, Any]
    ) -> Optional[str]:
        transitions = flow.get_outgoing_transitions(current_node_id)
        for t in transitions:
            if SafeConditionEvaluator.evaluate(t.condition, variables):
                return t.target_node
        return None
