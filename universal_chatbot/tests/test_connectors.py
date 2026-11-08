"""Pure Python unit tests for Connector Framework.

Tests GenericRestConnector and FrappeRestConnector headers, parameter validation,
and response unpacking by mocking the requests library.
Zero Frappe imports.
"""

from unittest.mock import MagicMock, patch
import unittest
from universal_chatbot.connectors.rest.frappe_connector import FrappeRestConnector
from universal_chatbot.connectors.rest.generic import GenericRestConnector
from universal_chatbot.core.exceptions import ConnectorError


class TestConnectors(unittest.TestCase):
    @patch("requests.request")
    def test_generic_rest_bearer_auth_and_execution(self, mock_request):
        # Setup mock response
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "123", "status": "Shipped", "total": 99.50}
        mock_resp.headers = {"Content-Type": "application/json"}
        mock_request.return_value = mock_resp

        connector = GenericRestConnector(
            config={"base_url": "https://api.mycompany.com"},
            credentials={"authentication_type": "Bearer", "api_key": "secret_bearer_token"},
        )
        connector.register_action(
            "get_order",
            {
                "name": "get_order",
                "method": "GET",
                "endpoint": "/orders/{order_id}",
                "input_schema": {"required": ["order_id"]},
            },
        )

        result = connector.execute("get_order", {"order_id": "ORD-555"})

        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["status"], "Shipped")

        # Verify requests.request call
        mock_request.assert_called_once()
        call_kwargs = mock_request.call_args[1]
        self.assertEqual(call_kwargs["method"], "GET")
        self.assertEqual(call_kwargs["url"], "https://api.mycompany.com/orders/ORD-555")
        self.assertEqual(call_kwargs["headers"]["Authorization"], "Bearer secret_bearer_token")

    @patch("requests.request")
    def test_frappe_rest_token_auth_and_unpacking(self, mock_request):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": {
                "name": "SO-2026-0001",
                "customer": "Acme Corp",
                "grand_total": 4500.00,
                "status": "To Deliver and Bill",
            }
        }
        mock_resp.headers = {"Content-Type": "application/json"}
        mock_request.return_value = mock_resp

        frappe_conn = FrappeRestConnector(
            config={"base_url": "https://erp.site.local"},
            credentials={
                "authentication_type": "Token",
                "api_key": "frappe_key_xyz",
                "api_secret": "frappe_secret_abc",
            },
        )

        result = frappe_conn.execute("get_doc", {"doctype": "Sales Order", "docname": "SO-2026-0001"})

        self.assertTrue(result["success"])
        self.assertEqual(result["unpacked"]["customer"], "Acme Corp")
        self.assertEqual(result["unpacked"]["grand_total"], 4500.00)

        mock_request.assert_called_once()
        call_kwargs = mock_request.call_args[1]
        self.assertEqual(call_kwargs["headers"]["Authorization"], "token frappe_key_xyz:frappe_secret_abc")
        self.assertEqual(call_kwargs["url"], "https://erp.site.local/api/resource/Sales Order/SO-2026-0001")

    @patch("requests.get")
    def test_frappe_test_connection(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"message": "administrator@example.com"}
        mock_get.return_value = mock_resp

        frappe_conn = FrappeRestConnector(
            config={"base_url": "https://erp.site.local"},
            credentials={"api_key": "k", "api_secret": "s"},
        )

        test_res = frappe_conn.test_connection()
        self.assertTrue(test_res["success"])
        self.assertEqual(test_res["user"], "administrator@example.com")

    def test_parameter_validation_failure(self):
        connector = GenericRestConnector(config={"base_url": "https://api.test.com"})
        connector.register_action(
            "update_customer",
            {
                "endpoint": "/customers/{cust_id}",
                "input_schema": {"required": ["cust_id", "email"]},
            },
        )

        with self.assertRaises(ConnectorError):
            connector.execute("update_customer", {"cust_id": "CUST-1"})  # missing email


if __name__ == "__main__":
    unittest.main()
