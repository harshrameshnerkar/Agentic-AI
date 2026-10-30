"""
Self-Correction Loop Tests for Role B (Data Service) on Real Northwind Database.
Verifies Acceptance Criterion 4:
- The service self-corrects a failed query using the database error.
- At least 3 deliberately broken queries self-correct live, visible in logs.
"""
import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from correction.self_correction import correction_engine


class TestSelfCorrectionLoop(unittest.TestCase):
    """Proves automated self-repair using database error messages on real Northwind data."""

    def test_broken_query_1_customer_name_typo(self):
        """Case 1: 'Name' column typo on Customers self-corrects using error feedback."""
        broken_sql = "SELECT CustomerID, Name FROM Customers LIMIT 5;"
        question = "Show 5 customer names and IDs."

        columns, rows, final_sql, success, err, logs = (
            correction_engine.execute_with_self_correction(
                question=question,
                initial_sql=broken_sql,
                request_id="CORR-CASE-1",
            )
        )

        print(f"\n[Case 1 Logs]: {logs}")
        self.assertTrue(success, f"Failed to self-correct: {err}")
        self.assertGreaterEqual(len(logs), 2, "Must record at least 2 attempts (initial failure + correction).")
        self.assertEqual(logs[0]["status"], "db_error")
        self.assertIn("no such column: name", logs[0]["error"].lower())
        self.assertEqual(logs[1]["status"], "success")
        self.assertGreater(len(rows), 0)

    def test_broken_query_2_revenue_column_typo(self):
        """Case 2: 'TotalRevenue' typo on Orders self-corrects to 'Freight' using error feedback."""
        broken_sql = "SELECT OrderID, TotalRevenue FROM Orders LIMIT 5;"
        question = "Show 5 order IDs and freight totals."

        columns, rows, final_sql, success, err, logs = (
            correction_engine.execute_with_self_correction(
                question=question,
                initial_sql=broken_sql,
                request_id="CORR-CASE-2",
            )
        )

        print(f"\n[Case 2 Logs]: {logs}")
        self.assertTrue(success, f"Failed to self-correct: {err}")
        self.assertGreaterEqual(len(logs), 2)
        self.assertEqual(logs[0]["status"], "db_error")
        self.assertEqual(logs[1]["status"], "success")
        self.assertGreater(len(rows), 0)

    def test_broken_query_3_price_column_typo(self):
        """Case 3: 'Cost' typo on Products self-corrects to 'UnitPrice' using error feedback."""
        broken_sql = "SELECT ProductID, ProductName, Cost FROM Products LIMIT 5;"
        question = "Show 5 product names and their unit prices."

        columns, rows, final_sql, success, err, logs = (
            correction_engine.execute_with_self_correction(
                question=question,
                initial_sql=broken_sql,
                request_id="CORR-CASE-3",
            )
        )

        print(f"\n[Case 3 Logs]: {logs}")
        self.assertTrue(success, f"Failed to self-correct: {err}")
        self.assertGreaterEqual(len(logs), 2)
        self.assertEqual(logs[0]["status"], "db_error")
        self.assertEqual(logs[1]["status"], "success")
        self.assertGreater(len(rows), 0)


if __name__ == "__main__":
    unittest.main()
