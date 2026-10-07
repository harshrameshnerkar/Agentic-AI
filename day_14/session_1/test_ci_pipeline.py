"""
Day 14 - Session 1: End-to-End CI Pipeline & Regression Test Suite
===================================================================
Automated verification proving:
  1. Baseline Prompt (v1.0.0) passes all golden evaluation tests with 100% score (Exit Code 0).
  2. Candidate Regressed Prompt (v1.1.0) fails quality & safety gates (Exit Code 1).
  3. PR Merge is blocked when pass rate drops or destructive actions lack human approval.
  4. Dark traffic shadow mirroring flags behavioral drift without impacting users.
  5. Progressive canary deployment triggers automated watchdog rollback.
"""

import os
import sys
import unittest

try:
    from day_14.session_1.prompt_registry import PromptRegistry, BASELINE_PROMPT_V1, CANDIDATE_REGRESSED_PROMPT_V1_1
    from day_14.session_1.golden_dataset import GOLDEN_EVAL_SUITE
    from day_14.session_1.eval_harness import EvaluationHarness
    from day_14.session_1.ci_gate import evaluate_ci_gate, run_ci_gate_pipeline
    from day_14.session_1.canary_shadow import ShadowDeploymentRouter, CanaryDeploymentController
except ImportError:
    from prompt_registry import PromptRegistry, BASELINE_PROMPT_V1, CANDIDATE_REGRESSED_PROMPT_V1_1
    from golden_dataset import GOLDEN_EVAL_SUITE
    from eval_harness import EvaluationHarness
    from ci_gate import evaluate_ci_gate, run_ci_gate_pipeline
    from canary_shadow import ShadowDeploymentRouter, CanaryDeploymentController


class CIPipelineRegressionTest(unittest.TestCase):

    def setUp(self) -> None:
        self.harness = EvaluationHarness(test_suite=GOLDEN_EVAL_SUITE)

    def test_01_baseline_passes_all_gates(self) -> None:
        """Proves that production stable v1.0.0 prompt satisfies all CI quality criteria."""
        summary, results = self.harness.run_eval(BASELINE_PROMPT_V1)

        self.assertEqual(summary.total_cases, 20)
        self.assertEqual(summary.passed_cases, 20)
        self.assertEqual(summary.failed_cases, 0)
        self.assertEqual(summary.pass_rate_pct, 100.0)
        self.assertEqual(summary.safety_compliance_pct, 100.0)
        self.assertEqual(summary.schema_validity_pct, 100.0)

        # Evaluate CI gate decision
        is_passed, violations = evaluate_ci_gate(summary, baseline_summary=summary)
        self.assertTrue(is_passed)
        self.assertEqual(len(violations), 0)

    def test_02_regressed_candidate_fails_ci_and_blocks_build(self) -> None:
        """Proves that a prompt change that drops pass rate or violates safety FAILS the build."""
        base_summary, _ = self.harness.run_eval(BASELINE_PROMPT_V1)
        cand_summary, cand_results = self.harness.run_eval(CANDIDATE_REGRESSED_PROMPT_V1_1)

        # Verify candidate failed multiple gates
        self.assertLess(cand_summary.pass_rate_pct, base_summary.pass_rate_pct)
        self.assertLess(cand_summary.safety_compliance_pct, 100.0)

        # Gatekeeper evaluation must reject the build
        is_passed, violations = evaluate_ci_gate(cand_summary, baseline_summary=base_summary)
        self.assertFalse(is_passed)
        self.assertGreater(len(violations), 0)

        # Confirm specific blocking reasons exist
        safety_blocks = [v for v in violations if "SAFETY_VIOLATION_BLOCK" in v]
        regression_blocks = [v for v in violations if "REGRESSION_BLOCK" in v]
        self.assertTrue(len(safety_blocks) > 0, "Safety violation block must be triggered!")
        self.assertTrue(len(regression_blocks) > 0, "Pass rate regression block must be triggered!")

    def test_03_shadow_deployment_auditing(self) -> None:
        """Proves dark traffic mirroring accurately detects drift before public deployment."""
        router = ShadowDeploymentRouter(baseline_version="v1.0.0", candidate_version="v1.1.0-regressed")

        for tc in GOLDEN_EVAL_SUITE[:10]:
            out = router.process_shadow_request(tc)
            self.assertIn("user_response", out)
            self.assertIn("shadow_record", out)

        stats = router.compute_shadow_drift_summary()
        self.assertEqual(stats["total_shadow_requests"], 10)
        self.assertFalse(stats["safe_for_canary"])
        self.assertGreater(stats["drift_percentage"], 0.0)

    def test_04_canary_automated_watchdog_rollback(self) -> None:
        """Proves progressive rollout triggers immediate rollback when safety is breached."""
        controller = CanaryDeploymentController(
            baseline_version="v1.0.0",
            candidate_version="v1.1.0-regressed",
            max_error_threshold_pct=2.0,
        )

        stages = controller.simulate_rollout(GOLDEN_EVAL_SUITE[:10])
        first_stage = stages[0]
        self.assertEqual(first_stage.traffic_percentage, 5)
        self.assertTrue(first_stage.rollback_triggered)
        self.assertEqual(first_stage.status, "ROLLED_BACK")


if __name__ == "__main__":
    unittest.main()
