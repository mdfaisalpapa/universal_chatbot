"""Generic REST Connector.

Pure Python, decoupled from Frappe.
Handles standard GET/POST/PUT REST requests with JSON payloads and
Bearer / Basic / Custom header authentication.
"""

import base64
import json
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
import requests
from universal_chatbot.connectors.base import BaseConnector
from universal_chatbot.core.exceptions import ConnectorError


class GenericRestConnector(BaseConnector):
    """Generic REST API Connector."""

    connector_type = "generic_rest"

    def __init__(self, config: Dict[str, Any], credentials: Optional[Dict[str, Any]] = None):
        super().__init__(config, credentials)
        raw_base = (self.config.get("base_url") or "").rstrip("/")
        if raw_base:
            parsed = urlparse(raw_base)
            if (
                parsed.hostname in ("kvc3.local", "chatbot.local", "localhost", "127.0.0.1")
                and not parsed.port
            ):
                raw_base = f"{parsed.scheme or 'http'}://{parsed.hostname}:8000"
        self.base_url = raw_base
        self.timeout = int(self.config.get("timeout", 15))
        self.actions_registry: Dict[str, Dict[str, Any]] = {}

        # Pre-register any actions passed in config
        for act in self.config.get("actions", []):
            if isinstance(act, dict) and "name" in act:
                self.actions_registry[act["name"]] = act

    def _build_headers(self, custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        auth_type = (self.credentials.get("authentication_type") or "None").lower()
        if auth_type == "bearer":
            token = self.credentials.get("api_key") or self.credentials.get("token") or ""
            headers["Authorization"] = f"Bearer {token}"
        elif auth_type == "basic":
            user = self.credentials.get("api_key") or self.credentials.get("username") or ""
            pwd = self.credentials.get("api_secret") or self.credentials.get("password") or ""
            encoded = base64.b64encode(f"{user}:{pwd}".encode("utf-8")).decode("utf-8")
            headers["Authorization"] = f"Basic {encoded}"
        elif auth_type == "header":
            header_name = self.credentials.get("header_name", "X-API-KEY")
            header_val = self.credentials.get("api_key") or ""
            headers[header_name] = header_val

        if custom_headers:
            headers.update(custom_headers)

        return headers

    def register_action(self, action_name: str, action_def: Dict[str, Any]) -> None:
        self.actions_registry[action_name] = action_def

    def test_connection(self) -> Dict[str, Any]:
        """Verify connectivity to base_url."""
        if not self.base_url:
            raise ConnectorError("Base URL is required to test connection", connector_name=self.connector_type)

        test_path = self.config.get("ping_endpoint", "")
        test_url = f"{self.base_url}/{test_path.lstrip('/')}" if test_path else self.base_url
        headers = self._build_headers()

        try:
            resp = requests.get(test_url, headers=headers, timeout=self.timeout)
            is_ok = resp.status_code in (200, 201, 204, 301, 302, 401, 403)
            return {
                "success": is_ok,
                "status_code": resp.status_code,
                "message": f"Connection response HTTP {resp.status_code}",
            }
        except Exception as e:
            raise ConnectorError(f"Connection test failed: {str(e)}", connector_name=self.connector_type)

    def get_available_actions(self) -> List[Dict[str, Any]]:
        return list(self.actions_registry.values())

    def validate_parameters(self, action_name: str, parameters: Dict[str, Any]) -> bool:
        action_def = self.actions_registry.get(action_name)
        if not action_def:
            return True  # Allow dynamic actions

        input_schema = action_def.get("input_schema", {})
        if isinstance(input_schema, dict):
            required = input_schema.get("required", [])
            for req in required:
                if req not in parameters or parameters[req] is None or parameters[req] == "":
                    return False
        return True

    def execute(self, action_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        if not self.validate_parameters(action_name, parameters):
            raise ConnectorError(
                f"Validation failed for action '{action_name}'. Missing required parameters.",
                connector_name=self.connector_type,
            )

        action_def = self.actions_registry.get(action_name, {})
        method = action_def.get("method", "GET").upper()
        raw_endpoint = action_def.get("endpoint") or action_def.get("operation") or ""

        # Interpolate path parameters e.g. /resource/{doctype}/{docname}
        def _replace_path(match):
            key = match.group(1).strip()
            return str(parameters.get(key, ""))

        endpoint = re.sub(r"\{([a-zA-Z0-9_]+)\}", _replace_path, raw_endpoint)
        full_url = f"{self.base_url}/{endpoint.lstrip('/')}" if self.base_url else endpoint

        headers = self._build_headers(action_def.get("headers"))

        # Build payload / query parameters
        params_to_send = None
        data_to_send = None

        if method in ("GET", "DELETE"):
            params_to_send = {k: v for k, v in parameters.items() if f"{{{k}}}" not in raw_endpoint}
        else:
            data_to_send = {k: v for k, v in parameters.items() if f"{{{k}}}" not in raw_endpoint}

        try:
            resp = requests.request(
                method=method,
                url=full_url,
                headers=headers,
                params=params_to_send,
                json=data_to_send,
                timeout=self.timeout,
            )

            try:
                body = resp.json()
            except Exception:
                body = {"raw": resp.text}

            success = resp.status_code in (200, 201, 202, 204)
            if not success and action_def.get("raise_for_status", False):
                raise ConnectorError(
                    f"HTTP {resp.status_code}: {resp.text}",
                    connector_name=self.connector_type,
                    status_code=resp.status_code,
                )

            return {
                "success": success,
                "status_code": resp.status_code,
                "data": body,
                "headers": dict(resp.headers),
            }
        except Exception as e:
            if isinstance(e, ConnectorError):
                raise
            raise ConnectorError(
                f"Failed to execute '{action_name}': {str(e)}",
                connector_name=self.connector_type,
            )
