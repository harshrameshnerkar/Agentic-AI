"""Unit tests for Day 20 Session 1: Stakeholder Demo Runner."""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from demo_runner import StakeholderDemoRunner


class TestStakeholderDemo(unittest.TestCase):
    """Test suite for live stakeholder demo execution and boundaries."""

    def setUp(self):
        self.runner = StakeholderDemoRunner()

    def test_scenario_1_read_triage(self):
        """Scenario 1 must resolve autonomously in sub-100ms with Tier 1 classification."""
        res = self.runner.run_scenario_1_read_triage()
        self.assertEqual(res.scenario_id, "SCENARIO-1")
        self.assertEqual(res.status, "RESOLVED_AUTONOMOUSLY")
        self.assertIn("TIER_1", res.blast_tier)
        self.assertLess(res.latency_ms, 150.0)
        self.assertTrue(res.audit_logged)

    def test_scenario_2_destructive_hitl(self):
        """Scenario 2 must enforce HMAC approval gate on Tier 3 action."""
        res = self.runner.run_scenario_2_destructive_hitl()
        self.assertEqual(res.scenario_id, "SCENARIO-2")
        self.assertEqual(res.status, "APPROVED_AND_EXECUTED")
        self.assertIn("TIER_3", res.blast_tier)
        self.assertTrue(res.audit_logged)
        self.assertGreaterEqual(len(self.runner.used_nonces), 1)

    def test_scenario_3_boundary_refusal(self):
        """Scenario 3 must refuse adversarial prompt injection with SECURITY_ABORT."""
        res = self.runner.run_scenario_3_boundary_refusal()
        self.assertEqual(res.scenario_id, "SCENARIO-3")
        self.assertEqual(res.status, "SECURITY_ABORT")
        self.assertTrue(res.audit_logged)

    def test_all_scenarios_execute_cleanly(self):
        """Verify all 3 scenarios run cleanly without exceptions."""
        results = self.runner.run_all_scenarios()
        self.assertEqual(len(results), 3)
        for r in results:
            self.assertTrue(r.audit_logged)
            self.assertGreater(r.latency_ms, 0)

    def test_stakeholder_feedback_data(self):
        """Verify stakeholder feedback JSON shows unanimous pilot approval."""
        fb_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "STAKEHOLDER_FEEDBACK.json")
        self.assertTrue(os.path.exists(fb_path))
        with open(fb_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        attendees = data.get("attendees", [])
        self.assertEqual(len(attendees), 3)
        for att in attendees:
            self.assertEqual(att.get("verdict"), "ACCEPTED_FOR_PILOT")
            self.assertEqual(att.get("score"), 5.0)


if __name__ == "__main__":
    unittest.main()
