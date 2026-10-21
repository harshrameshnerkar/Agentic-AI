"""Tests for FieldMatcher, FieldEvaluator, and Accuracy Reporting (Day 3 requirements)."""

from __future__ import annotations
import csv
import sys
import unittest
from pathlib import Path

# Ensure week5 directory is on path
WEEK5_DIR = Path(__file__).resolve().parent.parent
if str(WEEK5_DIR) not in sys.path:
    sys.path.insert(0, str(WEEK5_DIR))

from src.evaluator import FIELD_NAMES, FieldEvaluator, FieldMatcher

GT_CSV = WEEK5_DIR / "data" / "ground_truth" / "ground_truth.csv"
OUTPUT_CSV = WEEK5_DIR / "outputs" / "accuracy_report.csv"


class TestFieldEvaluator(unittest.TestCase):
    """Verifies matching rules, field-by-field accuracy, and report generation."""

    def setUp(self):
        self.matcher = FieldMatcher()
        self.evaluator = FieldEvaluator(
            ground_truth_path=GT_CSV,
            output_csv_path=OUTPUT_CSV,
        )

    def test_matching_rule_invoice_id(self):
        self.assertTrue(self.matcher.match_invoice_id("INV-101", "INV-101"))
        self.assertTrue(self.matcher.match_invoice_id("Invoice #: 101", "101"))
        self.assertTrue(self.matcher.match_invoice_id(None, None))  # True negative
        self.assertFalse(self.matcher.match_invoice_id("INV-101", "INV-102"))
        self.assertFalse(self.matcher.match_invoice_id(None, "INV-101"))

    def test_matching_rule_dates(self):
        self.assertTrue(self.matcher.match_date("2024-03-15", "2024-03-15"))
        self.assertTrue(self.matcher.match_date(None, None))
        self.assertFalse(self.matcher.match_date("2024-03-15", "2024-03-16"))

    def test_matching_rule_fuzzy_names(self):
        self.assertTrue(self.matcher.match_fuzzy_name(
            "Apex Cloud Systems Inc.",
            "Apex Cloud Systems, Inc"
        ))
        self.assertTrue(self.matcher.match_fuzzy_name(
            "SuperStore Commercial Supply",
            "SuperStore Commercial Supply"
        ))
        self.assertFalse(self.matcher.match_fuzzy_name(
            "Apple Inc.",
            "Microsoft Corp."
        ))

    def test_matching_rule_tax_id(self):
        self.assertTrue(self.matcher.match_tax_id("958-74-3511", "958743511"))
        self.assertTrue(self.matcher.match_tax_id("US-84-2910394", "US842910394"))
        self.assertTrue(self.matcher.match_tax_id(None, None))

    def test_matching_rule_amounts_epsilon(self):
        self.assertTrue(self.matcher.match_amount(100.00, 100.00))
        self.assertTrue(self.matcher.match_amount(100.01, 100.00, epsilon=0.02))
        self.assertFalse(self.matcher.match_amount(100.05, 100.00, epsilon=0.02))

    def test_matching_rule_enums(self):
        self.assertTrue(self.matcher.match_enum("USD", "USD"))
        self.assertTrue(self.matcher.match_enum("NET_30", "NET_30"))
        self.assertTrue(self.matcher.match_enum(None, None))

    def test_full_evaluation_against_ground_truth(self):
        if not GT_CSV.exists():
            self.skipTest(f"Ground truth file {GT_CSV} not found")

        results = self.evaluator.run_evaluation()

        self.assertEqual(results.total_documents, 40)
        self.assertEqual(len(results.field_metrics), 11)

        # High overall accuracy
        self.assertGreaterEqual(results.overall_field_accuracy, 90.0)

        # Weakest fields diagnosed
        weakest_names = [results.weakest_field_1.field_name, results.weakest_field_2.field_name]
        self.assertIn("due_date", weakest_names)
        self.assertIn("payment_terms", weakest_names)

        # Verify output CSV file generated
        self.assertTrue(OUTPUT_CSV.exists())
        with open(OUTPUT_CSV, "r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            self.assertEqual(len(reader), 11)
            field_names_in_csv = [row["field_name"] for row in reader]
            for f in FIELD_NAMES:
                self.assertIn(f, field_names_in_csv)


if __name__ == "__main__":
    unittest.main(verbosity=2)
