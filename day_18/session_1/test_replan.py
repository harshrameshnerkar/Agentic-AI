"""
Unit and Integration Tests for Day 18 Session 1: Standup & Replan.
Verifies honest re-estimation math, scope cut audit, and artifact generation.
"""

import os
import sys
import json
import unittest

# Ensure current session directory is on path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from replan_manager import SprintReplanManager, run_and_save_replan


class TestReplan(unittest.TestCase):

    def setUp(self):
        self.mgr = SprintReplanManager()

    def test_capacity_metrics_before_and_after(self):
        """Verifies that pre-replan was over capacity and post-replan has safe buffer."""
        metrics = self.mgr.compute_replan_metrics()

        pre = metrics["pre_replan"]
        post = metrics["post_replan"]

        self.assertTrue(pre["is_over_capacity"])
        self.assertEqual(pre["must_hours"], 18.0)
        self.assertEqual(pre["deficit_hours"], 2.0)

        self.assertFalse(post["is_over_capacity"])
        self.assertEqual(post["must_hours"], 13.5)
        self.assertEqual(post["buffer_hours"], 2.5)
        self.assertLessEqual(post["capacity_load_pct"], 85.0)

    def test_scope_cut_task_tracking(self):
        """Verifies TASK-2.4 was properly reclassified to COULD_HAVE."""
        metrics = self.mgr.compute_replan_metrics()
        cuts = metrics["scope_cuts"]

        self.assertEqual(len(cuts), 1)
        self.assertEqual(cuts[0]["task_id"], "TASK-2.4")
        self.assertEqual(cuts[0]["from_category"], "MUST_HAVE")
        self.assertEqual(cuts[0]["to_category"], "COULD_HAVE")
        self.assertEqual(cuts[0]["hours"], 4.5)
        self.assertIn("Dr. Elena Rostova", cuts[0]["approver"])

    def test_hours_freed_math(self):
        """Verifies that hours freed equals exactly the difference in must-have hours."""
        metrics = self.mgr.compute_replan_metrics()
        self.assertEqual(metrics["hours_freed"], 4.5)

    def test_replan_artifacts_generation(self):
        """Verifies run_and_save_replan produces valid JSON."""
        data = run_and_save_replan(CURRENT_DIR)
        out_file = os.path.join(CURRENT_DIR, "REPLAN_DATA.json")
        self.assertTrue(os.path.exists(out_file))

        with open(out_file, "r", encoding="utf-8") as f:
            saved = json.load(f)

        self.assertEqual(saved["post_replan"]["must_sp"], 16)
        self.assertEqual(saved["capacity_hours"], 16.0)


if __name__ == "__main__":
    unittest.main()
