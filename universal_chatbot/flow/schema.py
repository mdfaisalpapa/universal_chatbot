"""Data structures and schemas for Flow definitions and execution.

Pure Python, zero framework dependencies.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class FlowNodeType(str, Enum):
    START = "Start"
    SEND_MESSAGE = "Send Message"
    ASK_QUESTION = "Ask Question"
    MULTIPLE_CHOICE = "Multiple Choice"
    CONDITION = "Condition"
    SET_VARIABLE = "Set Variable"
    CALL_ACTION = "Call Action"
    END = "End"


class ExecutionStatus(str, Enum):
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class VariableDefinition:
    name: str
    data_type: str = "String"
    default_value: Any = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "data_type": self.data_type,
            "default_value": self.default_value,
        }


@dataclass
class TransitionDefinition:
    source_node: str
    target_node: str
    condition: Optional[Any] = None  # Dict rule or condition string

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_node": self.source_node,
            "target_node": self.target_node,
            "condition": self.condition,
        }


@dataclass
class NodeDefinition:
    node_id: str
    node_type: str
    configuration: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "configuration": self.configuration,
        }


@dataclass
class FlowDefinition:
    flow_id: str
    name: str
    version: str = "1.0.0"
    nodes: Dict[str, NodeDefinition] = field(default_factory=dict)
    transitions: List[TransitionDefinition] = field(default_factory=list)
    variables: Dict[str, VariableDefinition] = field(default_factory=dict)
    start_node_id: Optional[str] = None

    def get_node(self, node_id: str) -> Optional[NodeDefinition]:
        return self.nodes.get(node_id)

    def get_outgoing_transitions(self, source_node_id: str) -> List[TransitionDefinition]:
        return [t for t in self.transitions if t.source_node == source_node_id]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "flow_id": self.flow_id,
            "name": self.name,
            "version": self.version,
            "start_node_id": self.start_node_id,
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "transitions": [t.to_dict() for t in self.transitions],
            "variables": {k: v.to_dict() for k, v in self.variables.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FlowDefinition":
        nodes = {}
        for nid, ndata in data.get("nodes", {}).items():
            if isinstance(ndata, dict):
                nodes[nid] = NodeDefinition(
                    node_id=ndata.get("node_id", nid),
                    node_type=ndata["node_type"],
                    configuration=ndata.get("configuration", {}),
                )
            else:
                nodes[nid] = ndata

        transitions = []
        for tdata in data.get("transitions", []):
            if isinstance(tdata, dict):
                transitions.append(
                    TransitionDefinition(
                        source_node=tdata["source_node"],
                        target_node=tdata["target_node"],
                        condition=tdata.get("condition"),
                    )
                )
            else:
                transitions.append(tdata)

        variables = {}
        for vname, vdata in data.get("variables", {}).items():
            if isinstance(vdata, dict):
                variables[vname] = VariableDefinition(
                    name=vdata.get("name", vname),
                    data_type=vdata.get("data_type", "String"),
                    default_value=vdata.get("default_value"),
                )
            else:
                variables[vname] = vdata

        return cls(
            flow_id=data.get("flow_id", "unnamed_flow"),
            name=data.get("name", "Unnamed Flow"),
            version=data.get("version", "1.0.0"),
            nodes=nodes,
            transitions=transitions,
            variables=variables,
            start_node_id=data.get("start_node_id"),
        )
