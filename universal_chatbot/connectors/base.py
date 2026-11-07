"""Base connector contract for external system integrations.

Pure Python, decoupled from Frappe.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseConnector(ABC):
    """Abstract connector for interacting with external APIs (e.g. ERPNext, REST)."""

    connector_type: str = "base"

    def __init__(self, config: Dict[str, Any], credentials: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.credentials = credentials or {}

    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """Test authentication and connectivity to the remote target."""
        pass

    @abstractmethod
    def get_available_actions(self) -> List[Dict[str, Any]]:
        """Return metadata describing available actions and required parameters."""
        pass

    @abstractmethod
    def validate_parameters(self, action_name: str, parameters: Dict[str, Any]) -> bool:
        """Validate parameters against action definitions."""
        pass

    @abstractmethod
    def execute(self, action_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the remote action and return standardized output payload."""
        pass
