"""
Unit and Integration Tests for Day 17 Session 4: Progress Update.
Verifies exact 5-line count constraint, required categories, and metric consistency.
"""

import os
import sys
import unittest

# Ensure current session directory is on path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from status_validator import validate_status_file


class TestProgressUpdate(unittest.TestCase):

    def setUp(self):
        self.status_file = os.path.join(CURRENT_DIR, "5_LINE_STATUS_UPDATE.txt")
        self.md_file = os.path.join(CURRENT_DIR, "STATUS_UPDATE.md")

    def test_exact_five_lines(self):
        """Strict constraint: The update must be exactly 5 lines — no more, no less."""
        self.assertTrue(os.path.exists(self.status_file), "5_LINE_STATUS_UPDATE.txt must exist")
        with open(self.status_file, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        self.assertEqual(len(lines), 5, f"Expected exactly 5 lines, found {len(lines)}")

    def test_required_categories_present(self):
        """Verifies each of the 5 required curriculum elements is present."""
        valid, lines, errors = validate_status_file(self.status_file)
        self.assertTrue(valid, f"Validation failed with errors: {errors}")
        self.assertEqual(len(errors), 0)

        # Line 1: What shipped
        self.assertIn("shipped", lines[0].lower())
        # Line 2: Current pass rate
        self.assertIn("pass rate", lines[1].lower())
        # Line 3: Cost per query
        self.assertIn("cost", lines[2].lower())
        # Line 4: What is at risk
        self.assertIn("risk", lines[3].lower())
        # Line 5: What decision is needed
        self.assertIn("decision", lines[4].lower())

    def test_metrics_accuracy(self):
        """Verifies that numbers cited match empirical evaluation."""
        with open(self.status_file, "r", encoding="utf-8") as f:
            text = f.read()

        self.assertIn("100.0%", text)
        self.assertIn("$0.000329", text)
        self.assertIn("$0.15", text)
        self.assertIn("762.8ms", text)

    def test_status_update_markdown_integrity(self):
        """Verifies that STATUS_UPDATE.md exists and contains the mentor review."""
        self.assertTrue(os.path.exists(self.md_file))
        with open(self.md_file, "r", encoding="utf-8") as f:
            md_content = f.read()

        self.assertIn("Dr. Elena Rostova", md_content)
        self.assertIn("SIGN-OFF GRANTED", md_content)


if __name__ == "__main__":
    unittest.main()
