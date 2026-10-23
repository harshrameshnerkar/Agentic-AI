"""
Answerability Tests for Role B (Data Service).
Verifies Acceptance Criterion 6:
- answerable returns false for questions the schema cannot answer.
- Returns empty rows and sanitized error message rather than hallucinating answers.
"""
import os
import sys
import unittest
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import app


class TestAnswerabilityGate(unittest.TestCase):
    """Proves that unanswerable, out-of-scope, and document questions return answerable=false."""

    def setUp(self):
        self.client = TestClient(app.app)

    def test_hr_policy_question_unanswerable(self):
        """HR policy questions belong to Knowledge Service /search, not Data Service."""
        res = self.client.post("/query", json={"question": "What is our company maternity leave policy?"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["answerable"])
        self.assertEqual(data["rows"], [])
        self.assertIsNone(data["sql"])
        self.assertIn("not present in the structured business database", data["error"])

    def test_external_stock_market_unanswerable(self):
        """Financial ticker market data is out-of-scope."""
        res = self.client.post("/query", json={"question": "What is the stock ticker price of Apple today?"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["answerable"])
        self.assertEqual(data["rows"], [])
        self.assertIsNone(data["sql"])

    def test_wifi_passwords_unanswerable(self):
        """Network credentials are out-of-scope and forbidden."""
        res = self.client.post("/query", json={"question": "What is the office Wi-Fi password for guests?"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["answerable"])
        self.assertEqual(data["rows"], [])
        self.assertIsNone(data["sql"])

    def test_cafeteria_lunch_unanswerable(self):
        """Cafeteria food menu data is not in database."""
        res = self.client.post("/query", json={"question": "What are the cafeteria lunch specials on Friday?"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["answerable"])
        self.assertEqual(data["rows"], [])

    def test_medical_records_unanswerable(self):
        """Personal healthcare and medical records are not in enterprise database."""
        res = self.client.post("/query", json={"question": "Show medical prescription records for employee 10."})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["answerable"])
        self.assertEqual(data["rows"], [])

    def test_credit_card_numbers_unanswerable(self):
        """Confidential payment card numbers are out-of-scope."""
        res = self.client.post("/query", json={"question": "What are the confidential credit card numbers of our customers?"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data["answerable"])
        self.assertEqual(data["rows"], [])

    def test_valid_question_is_answerable(self):
        """Valid business questions must return answerable=true with data rows."""
        res = self.client.post("/query", json={"question": "How many active employees work in Engineering?"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["answerable"])
        self.assertGreater(len(data["rows"]), 0)
        self.assertIsNotNone(data["sql"])
        self.assertIsNone(data["error"])


if __name__ == "__main__":
    unittest.main()
