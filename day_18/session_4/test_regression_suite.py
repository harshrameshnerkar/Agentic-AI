"""
Unit and Integration Tests for Day 18 Session 4: Regression Suite.
Verifies exact 35-case count, exit code contract (0 on pass, 1 on fail), and report artifacts.
"""

import os
import sys
import json
import unittest

# Ensure current session directory is on path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from run_regression_suite import RegressionSuiteRunner, execute_one_command_suite


class TestRegressionSuite(unittest.TestCase):

    def setUp(self):
        self.dataset_path = os.path.join(CURRENT_DIR, "regression_dataset_35.json")

    def test_regression_dataset_exact_35_cases(self):
        """Verifies that the suite evaluates exactly 35 test cases."""
        self.assertTrue(os.path.exists(self.dataset_path), "regression_dataset_35.json must exist")
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            cases = json.load(f)
        self.assertEqual(len(cases), 35, f"Expected 35 cases, found {len(cases)}")

    def test_bug_regression_cases_present(self):
        """Verifies that the 5 newly added defect-regression cases are included."""
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            cases = json.load(f)

        case_ids = {c["case_id"] for c in cases}
        for reg_id in ["REG-031", "REG-032", "REG-033", "REG-034", "REG-035"]:
            self.assertIn(reg_id, case_ids, f"Bug regression case {reg_id} missing")

    def test_suite_passes_and_returns_zero(self):
        """Verifies that normal suite execution achieves >= 95% pass rate and returns exit code 0."""
        exit_code = execute_one_command_suite(simulate_failure=False, output_dir=CURRENT_DIR)
        self.assertEqual(exit_code, 0, "Suite must return 0 on successful pass")

    def test_suite_blocks_on_simulated_regression(self):
        """Verifies that simulated regression triggers CI gate failure with exit code 1."""
        exit_code = execute_one_command_suite(simulate_failure=True, output_dir=CURRENT_DIR)
        self.assertEqual(exit_code, 1, "Suite must return 1 to block CI build when pass rate drops")

    def test_report_artifact_generation(self):
        """Verifies that REGRESSION_RUN_REPORT.json is written with valid metrics."""
        execute_one_command_suite(simulate_failure=False, output_dir=CURRENT_DIR)
        report_path = os.path.join(CURRENT_DIR, "REGRESSION_RUN_REPORT.json")
        self.assertTrue(os.path.exists(report_path))
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)

        self.assertEqual(report["total_cases"], 35)
        self.assertGreaterEqual(report["pass_rate_pct"], 95.0)


if __name__ == "__main__":
    unittest.main()
