"""Frappe REST Connector.

Pure Python, decoupled from Frappe.
Handles communication with an external Frappe/ERPNext installation using
token-based authentication (`token {api_key}:{api_secret}`).
"""

from typing import Any, Dict, List, Optional
from universal_chatbot.connectors.rest.generic import GenericRestConnector
from universal_chatbot.core.exceptions import ConnectorError


class FrappeRestConnector(GenericRestConnector):
    """Connector specifically configured for external Frappe / ERPNext REST APIs."""

    connector_type = "frappe_rest"

    def __init__(self, config: Dict[str, Any], credentials: Optional[Dict[str, Any]] = None):
        super().__init__(config, credentials)
        # Register standard Frappe actions out-of-the-box
        self._register_default_frappe_actions()

    def _build_headers(self, custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        api_key = self.credentials.get("api_key") or ""
        api_secret = self.credentials.get("api_secret") or ""

        if api_key and api_secret:
            headers["Authorization"] = f"token {api_key}:{api_secret}"
        elif api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        if custom_headers:
            headers.update(custom_headers)

        return headers

    def _register_default_frappe_actions(self) -> None:
        """Register common Frappe/ERPNext resource actions."""
        self.register_action(
            "get_doc",
            {
                "name": "get_doc",
                "method": "GET",
                "endpoint": "/api/resource/{doctype}/{docname}",
                "input_schema": {"required": ["doctype", "docname"]},
            },
        )
        self.register_action(
            "get_list",
            {
                "name": "get_list",
                "method": "GET",
                "endpoint": "/api/resource/{doctype}",
                "input_schema": {"required": ["doctype"]},
            },
        )
        self.register_action(
            "create_doc",
            {
                "name": "create_doc",
                "method": "POST",
                "endpoint": "/api/resource/{doctype}",
                "input_schema": {"required": ["doctype"]},
            },
        )
        self.register_action(
            "call_method",
            {
                "name": "call_method",
                "method": "POST",
                "endpoint": "/api/method/{method}",
                "input_schema": {"required": ["method"]},
            },
        )

    def test_connection(self) -> Dict[str, Any]:
        """Test Frappe API authentication via /api/method/frappe.auth.get_logged_user."""
        if not self.base_url:
            raise ConnectorError("Base URL is required to test Frappe connection", connector_name=self.connector_type)

        test_url = f"{self.base_url}/api/method/frappe.auth.get_logged_user"
        headers = self._build_headers()

        import requests

        try:
            resp = requests.get(test_url, headers=headers, timeout=self.timeout)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    user = data.get("message")
                    return {
                        "success": True,
                        "status_code": 200,
                        "user": user,
                        "message": f"Successfully authenticated as {user}",
                    }
                except Exception:
                    return {"success": True, "status_code": 200, "message": "Connection verified"}
            elif resp.status_code in (401, 403):
                return {
                    "success": False,
                    "status_code": resp.status_code,
                    "message": "Authentication failed: invalid api_key or api_secret token",
                }
            else:
                return {
                    "success": False,
                    "status_code": resp.status_code,
                    "message": f"Unexpected response HTTP {resp.status_code}",
                }
        except Exception as e:
            raise ConnectorError(f"Connection test failed: {str(e)}", connector_name=self.connector_type)

    def execute(self, action_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action and unpack Frappe 'data' or 'message' envelopes."""
        raw_result = super().execute(action_name, parameters)

        # Unpack Frappe standard envelope {"data": ...} or {"message": ...}
        body = raw_result.get("data", {})
        if isinstance(body, dict):
            if "data" in body:
                raw_result["unpacked"] = body["data"]
            elif "message" in body:
                raw_result["unpacked"] = body["message"]
            else:
                raw_result["unpacked"] = body
        else:
            raw_result["unpacked"] = body

        return raw_result
