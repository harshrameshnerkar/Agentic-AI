"""
Unit and Integration Tests for Day 16 Session 4: Plan, Estimate & Eval Set First.
Verifies exact 30-case evaluation set schema, MoSCoW capacity math, and sprint board artifacts.
"""

import os
import sys
import json
import unittest

# Ensure current session directory is on path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from sprint_board_manager import (
    EvalDatasetAuditor,
    SprintBoardManager,
    run_and_save_sprint_board
)


class TestPlanAndEval(unittest.TestCase):

    def setUp(self):
        self.dataset_path = os.path.join(CURRENT_DIR, "eval_dataset_30.json")
        self.md_path = os.path.join(CURRENT_DIR, "SPRINT_PLANNING_BOARD.md")

    def test_eval_dataset_exact_30_cases(self):
        """Verifies that the pre-code evaluation set contains exactly 30 test cases."""
        self.assertTrue(os.path.exists(self.dataset_path), "eval_dataset_30.json must exist")
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            cases = json.load(f)
        self.assertEqual(len(cases), 30, f"Expected exactly 30 cases, got {len(cases)}")

    def test_eval_dataset_category_distribution(self):
        """Verifies category distribution: 8 static, 16 ephemeral, 6 adversarial."""
        auditor = EvalDatasetAuditor(self.dataset_path)
        stats = auditor.get_summary_statistics()

        cats = stats["categories"]
        self.assertEqual(cats["static_runbook"], 8)
        self.assertEqual(cats["ephemeral_cluster"], 16)
        self.assertEqual(cats["adversarial_red_line"], 6)

    def test_schema_validity(self):
        """Audits every field across all 30 test cases for strict type and value validity."""
        auditor = EvalDatasetAuditor(self.dataset_path)
        is_valid, errors = auditor.validate_schema()
        self.assertTrue(is_valid, f"Schema validation errors found: {errors}")
        self.assertEqual(len(errors), 0)

    def test_moscow_sprint_metrics(self):
        """Verifies capacity math and MoSCoW task allocations."""
        mgr = SprintBoardManager()
        metrics = mgr.compute_sprint_metrics()

        self.assertEqual(metrics["capacity_hours"], 32.0)
        self.assertLessEqual(metrics["committed_hours"], metrics["capacity_hours"])
        self.assertEqual(metrics["must_have"]["task_count"], 5)
        self.assertEqual(metrics["should_have"]["task_count"], 4)
        self.assertEqual(metrics["could_have"]["task_count"], 2)
        self.assertEqual(metrics["wont_have_count"], 3)
        self.assertGreater(metrics["buffer_hours"], 0.0)

    def test_sprint_board_artifact_generation(self):
        """Verifies that run_and_save_sprint_board writes SPRINT_BOARD_DATA.json correctly."""
        data = run_and_save_sprint_board(CURRENT_DIR)
        out_file = os.path.join(CURRENT_DIR, "SPRINT_BOARD_DATA.json")
        self.assertTrue(os.path.exists(out_file))

        with open(out_file, "r", encoding="utf-8") as f:
            saved = json.load(f)

        self.assertEqual(saved["eval_dataset_statistics"]["total_cases"], 30)
        self.assertEqual(saved["sprint_planning_metrics"]["must_have"]["sp"], 21)


if __name__ == "__main__":
    unittest.main()
