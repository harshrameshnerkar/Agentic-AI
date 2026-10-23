"""
Unit Tests for Interface 2 Contract Compliance (UNIFIED-BUSINESS-ASSISTAN.md §4.5).
Verifies Acceptance Criteria 1 and 2:
- Mock endpoint published on Day 1 returning 2 hardcoded rows + fake SQL.
- Real /query endpoint matches contract exactly, allowing Role C to integrate with zero code drift.
"""
import os
import sys
import unittest
from fastapi.testclient import TestClient

# Ensure data_service root is on path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from contracts import QueryRequest, QueryResponse
import mock_query_service
import app


class TestInterfaceContract(unittest.TestCase):
    """Verifies schema parity between mock and production services."""

    def setUp(self):
        self.mock_client = TestClient(mock_query_service.app)
        self.real_client = TestClient(app.app)

    def test_mock_query_contract_shape(self):
        """Criterion 1: Mock endpoint returns 2 hardcoded rows + fake SQL in exact contracted shape."""
        response = self.mock_client.post("/query", json={"question": "Which five customers have the most invoices?"})
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Validate against Pydantic model
        validated = QueryResponse(**data)
        self.assertEqual(len(validated.rows), 2)
        self.assertTrue(validated.answerable)
        self.assertIsNotNone(validated.sql)
        self.assertIn("SELECT", validated.sql.upper())
        self.assertEqual(validated.columns, ["customer_name", "invoice_count"])
        self.assertIsNone(validated.error)

    def test_mock_query_triggers(self):
        """Verifies mock branch triggers for Role C integration testing."""
        # Unanswerable trigger
        res_unans = self.mock_client.post("/query", json={"question": "This question is unanswerable"})
        self.assertEqual(res_unans.status_code, 200)
        data_unans = res_unans.json()
        self.assertFalse(data_unans["answerable"])
        self.assertEqual(data_unans["rows"], [])

        # Error trigger
        res_err = self.mock_client.post("/query", json={"question": "Simulate error"})
        self.assertEqual(res_err.status_code, 503)

    def test_real_query_matches_contract_keys(self):
        """Criterion 2: Real /query returns identical keys as mock service with no consumer changes."""
        res_mock = self.mock_client.post("/query", json={"question": "How many customers do we have?"})
        res_real = self.real_client.post("/query", json={"question": "How many customers do we have?"})

        self.assertEqual(res_real.status_code, 200)
        mock_keys = set(res_mock.json().keys())
        real_keys = set(res_real.json().keys())

        # Exact key set match
        self.assertEqual(mock_keys, real_keys)
        self.assertIn("columns", real_keys)
        self.assertIn("rows", real_keys)
        self.assertIn("sql", real_keys)
        self.assertIn("answerable", real_keys)
        self.assertIn("error", real_keys)


if __name__ == "__main__":
    unittest.main()
