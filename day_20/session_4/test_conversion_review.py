"""Unit tests for Day 20 Session 4: Conversion Assessment & Final Review."""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conversion_evaluator import ConversionReviewManager


class TestConversionReview(unittest.TestCase):
    """Test suite for Day 20 internship conversion review and rubric."""

    def setUp(self):
        self.mgr = ConversionReviewManager()

    def test_load_evaluation_metadata(self):
        """Verify candidate details and target conversion role."""
        data = self.mgr.load_evaluation_data()
        cand = data.get("candidate", {})
        self.assertEqual(cand.get("name"), "Harsh Ramesh Nerkar")
        self.assertIn("AI Systems Engineer", cand.get("target_conversion_role", ""))

    def test_composite_score_perfect_rating(self):
        """Verify candidate scored 5.0 / 5.0 across all 4 weeks."""
        summary = self.mgr.evaluate_conversion()
        self.assertEqual(summary.composite_score, 5.0)
        self.assertEqual(summary.weeks_evaluated, 4)

    def test_unanimous_strong_hire_recommendation(self):
        """Verify unanimous STRONG_HIRE from all 3 review panel members."""
        summary = self.mgr.evaluate_conversion()
        self.assertTrue(summary.unanimous_strong_hire)
        self.assertEqual(summary.panel_count, 3)

    def test_system_design_defense_excellence(self):
        """Verify system design challenge grade and topic."""
        data = self.mgr.load_evaluation_data()
        sd = data.get("system_design_challenge", {})
        self.assertIn("EXCEPTIONAL", sd.get("grade", ""))
        self.assertIn("Multi-Region", sd.get("topic", ""))

    def test_final_conversion_verdict_approved(self):
        """Verify final conversion decision is APPROVED."""
        summary = self.mgr.evaluate_conversion()
        self.assertEqual(summary.verdict, "CONVERSION_APPROVED")


if __name__ == "__main__":
    unittest.main()
