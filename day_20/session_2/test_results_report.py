"""Unit tests for Day 20 Session 2: Results & Limitations Report."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from report_generator import ResultsReportManager


class TestResultsReport(unittest.TestCase):
    """Test suite for Day 20 Results & Limitations validation."""

    def setUp(self):
        self.mgr = ResultsReportManager()

    def test_charter_metrics_loading(self):
        """Verify metrics JSON contains all required charter comparison fields."""
        metrics = self.mgr.load_metrics()
        self.assertIn("charter_comparison", metrics)
        self.assertIn("stratified_pass_rate", metrics)
        self.assertIn("honest_limitations", metrics)
        self.assertIn("scope_cut_summary", metrics)

    def test_sla_verification_all_pass(self):
        """Verify all SLA dimensions pass against Day 16 criteria."""
        res = self.mgr.verify_charter_slas()
        self.assertTrue(res.all_slas_met)
        self.assertTrue(res.pass_rate_ok)
        self.assertTrue(res.latency_ok)
        self.assertTrue(res.cost_ok)
        self.assertTrue(res.regressions_ok)
        self.assertEqual(res.total_golden_cases, 35)

    def test_stratified_pass_rate_100_percent(self):
        """Verify 100% pass rate across all 4 incident categories."""
        metrics = self.mgr.load_metrics()
        for cat in metrics.get("stratified_pass_rate", []):
            self.assertEqual(cat.get("pass_rate_pct"), 100.0)
            self.assertEqual(cat.get("passed_cases"), cat.get("total_cases"))

    def test_limitations_catalog(self):
        """Verify at least 4 honest operational limitations are cataloged."""
        metrics = self.mgr.load_metrics()
        limitations = metrics.get("honest_limitations", [])
        self.assertGreaterEqual(len(limitations), 4)

    def test_scope_cut_rationale(self):
        """Verify Slack bot scope cut is documented with engineering rationale."""
        metrics = self.mgr.load_metrics()
        sc = metrics.get("scope_cut_summary", {})
        self.assertEqual(sc.get("item"), "Slack Interactive Bot Integration")
        self.assertEqual(sc.get("revised_priority"), "COULD_HAVE")
        self.assertIn("contingency buffer", sc.get("rationale"))


if __name__ == "__main__":
    unittest.main()
