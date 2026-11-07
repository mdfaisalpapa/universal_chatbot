"""Dynamic registry for flow node types.

Pure Python, zero framework dependencies.
"""

from typing import Dict, Type
from universal_chatbot.flow.base import BaseFlowNode


class NodeRegistry:
    """Registry maintaining mappings of node_type -> FlowNode class."""

    _registry: Dict[str, Type[BaseFlowNode]] = {}

    @classmethod
    def register(cls, node_type: str, node_class: Type[BaseFlowNode]) -> None:
        cls._registry[node_type] = node_class

    @classmethod
    def get(cls, node_type: str) -> Type[BaseFlowNode]:
        if node_type not in cls._registry:
            raise KeyError(f"Node type '{node_type}' is not registered in NodeRegistry")
        return cls._registry[node_type]

    @classmethod
    def create(cls, node_type: str, node_id: str, configuration: Dict) -> BaseFlowNode:
        node_cls = cls.get(node_type)
        return node_cls(node_id=node_id, configuration=configuration)

    @classmethod
    def registered_types(cls) -> Dict[str, Type[BaseFlowNode]]:
        return dict(cls._registry)


def register_node(node_type: str):
    """Decorator to register node classes into NodeRegistry."""

    def decorator(cls: Type[BaseFlowNode]):
        NodeRegistry.register(node_type, cls)
        cls.node_type = node_type
        return cls

    return decorator
