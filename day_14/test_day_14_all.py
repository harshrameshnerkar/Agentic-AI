"""
Day 14: Master End-to-End Verification Test Suite
=================================================
Automated verification suite validating all 4 sessions of Day 14:
  - Session 1: Prompt Versioning, CI Regression Gating, Shadow Mirroring, Canary Rollout
  - Session 2: 100-Case Stratified Dataset, Cohen's Kappa, Judge Drift, Online A/B Testing
  - Session 3: Run Tracing, Daily Time-Series Metrics, p95 Latency, Cost, Failure Categories, Alerting, Silent Decay
  - Session 4: Kill Switch Modes, Action Gates, Circuit Breakers, LKG Rollback, Defensive Parsing
"""

import os
import sys
import unittest

# Ensure workspace root and session directories are accessible
_workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _workspace_root not in sys.path:
    sys.path.insert(0, _workspace_root)

_day14_dir = os.path.dirname(os.path.abspath(__file__))
for s_dir in ["session_1", "session_2", "session_3", "session_4"]:
    p = os.path.join(_day14_dir, s_dir)
    if p not in sys.path:
        sys.path.insert(0, p)

# Session 1 Imports
from day_14.session_1.prompt_registry import PromptRegistry, BASELINE_PROMPT_V1, CANDIDATE_REGRESSED_PROMPT_V1_1
from day_14.session_1.golden_dataset import GOLDEN_EVAL_SUITE
from day_14.session_1.eval_harness import EvaluationHarness
from day_14.session_1.ci_gate import evaluate_ci_gate, CIGatePolicy
from day_14.session_1.canary_shadow import ShadowDeploymentRouter, CanaryDeploymentController

# Session 2 Imports
from day_14.session_2.stratified_dataset import StratifiedDatasetRegistry
from day_14.session_2.trace_miner import mine_100_stratified_cases
from day_14.session_2.eval_runner import StratifiedEvaluationRunner
from day_14.session_2.inter_rater_agreement import InterRaterAgreementEngine
from day_14.session_2.judge_calibration_drift import JudgeCalibrationDriftDetector
from day_14.session_2.ab_testing_framework import ABTestingEngine
from day_14.session_2.validate_eval_dataset import validate_dataset

# Session 3 Imports
from day_14.session_3.models import Trace, FailureCategory
from day_14.session_3.tracer import ProductionTracer
from day_14.session_3.metrics_aggregator import MetricsAggregator
from day_14.session_3.alerting_engine import AlertingEngine

# Session 4 Imports
from day_14.session_4.kill_switch_controller import (
    EmergencyKillSwitchController,
    KillSwitchLevel,
    CircuitBreakerState,
    PromptModelConfig,
)
from day_14.session_4.main import defensive_json_parser


class TestDay14Session1RegressionAndCI(unittest.TestCase):
    """Session 1: Prompt Versioning, Evaluation Harness, CI Regression Blocking, Canary/Shadow."""

    def setUp(self):
        self.harness = EvaluationHarness()

    def test_prompt_versioning_registry(self):
        """Verify prompts are immutable, versioned, and include full provenance metadata."""
        v1 = PromptRegistry.get_prompt("v1.0.0")
        self.assertEqual(v1.version, "v1.0.0")
        self.assertEqual(v1.model_name, "claude-3-5-sonnet-20241022")
        self.assertEqual(v1.temperature, 0.0)
        self.assertTrue(len(v1.commit_sha) > 0)

        # Regressed candidate prompt
        v1_1 = PromptRegistry.get_prompt("v1.1.0-regressed")
        self.assertEqual(v1_1.version, "v1.1.0-regressed")

    def test_baseline_eval_passes_all_cases(self):
        """Verify baseline prompt achieves 100% pass rate and 100% safety compliance."""
        v1 = PromptRegistry.get_prompt("v1.0.0")
        summary, results = self.harness.run_eval(v1)
        self.assertEqual(summary.total_cases, len(GOLDEN_EVAL_SUITE))
        self.assertEqual(summary.pass_rate_pct, 100.0)
        self.assertEqual(summary.safety_compliance_pct, 100.0)
        self.assertEqual(summary.schema_validity_pct, 100.0)

    def test_ci_gate_blocks_regressed_prompt(self):
        """Verify CI Quality Gate blocks merge when candidate pass rate drops below baseline or safety gate fails."""
        base_prompt = PromptRegistry.get_prompt("v1.0.0")
        cand_prompt = PromptRegistry.get_prompt("v1.1.0-regressed")

        base_summary, _ = self.harness.run_eval(base_prompt)
        cand_summary, _ = self.harness.run_eval(cand_prompt)

        # Candidate has 0% pass rate because of schema drift and safety rule violation
        self.assertEqual(cand_summary.pass_rate_pct, 0.0)
        self.assertEqual(cand_summary.safety_compliance_pct, 0.0)

        passed, violations = evaluate_ci_gate(cand_summary, base_summary)
        self.assertFalse(passed, "CI Gate should fail on regressed candidate prompt")
        self.assertGreater(len(violations), 0)
        # Check specific violation triggers
        violation_text = " ".join(violations)
        self.assertIn("SAFETY_VIOLATION_BLOCK", violation_text)
        self.assertIn("PASS_RATE_FLOOR_BLOCK", violation_text)
        self.assertIn("REGRESSION_BLOCK", violation_text)

    def test_shadow_deployment_dark_traffic_mirroring(self):
        """Verify dark traffic mirroring detects behavioral drift without impacting users."""
        router = ShadowDeploymentRouter(baseline_version="v1.0.0", candidate_version="v1.1.0-regressed")
        for tc in GOLDEN_EVAL_SUITE[:8]:
            out = router.process_shadow_request(tc)
            self.assertIn("user_response", out)
            self.assertIn("shadow_record", out)
        
        summary = router.compute_shadow_drift_summary()
        self.assertEqual(summary["total_shadow_requests"], 8)
        self.assertFalse(summary["safe_for_canary"])

    def test_canary_deployment_automated_rollback(self):
        """Verify canary watchdog halts and rolls back traffic upon detecting safety violations."""
        controller = CanaryDeploymentController(
            baseline_version="v1.0.0",
            candidate_version="v1.1.0-regressed",
            max_error_threshold_pct=2.0,
        )
        stages = controller.simulate_rollout(GOLDEN_EVAL_SUITE[:10])
        # First stage should trigger rollback due to errors and safety violations
        self.assertTrue(len(stages) > 0)
        self.assertTrue(stages[0].rollback_triggered)
        self.assertEqual(stages[0].status, "ROLLED_BACK")


class TestDay14Session2EvaluationAtScale(unittest.TestCase):
    """Session 2: 100-Case Dataset, Stratification, Inter-Rater Agreement, Judge Drift, A/B Testing."""

    def test_100_case_dataset_provenance_and_stratification(self):
        """Verify dataset contains exactly 100 cases, stratified into 5 distinct operational strata."""
        dataset_path = os.path.join(_day14_dir, "session_2", "golden_dataset_100.json")
        is_valid = validate_dataset(dataset_path)
        self.assertTrue(is_valid)

    def test_batch_eval_across_all_100_cases(self):
        """Verify batch evaluation executes across all 100 cases with per-stratum scoring."""
        runner = StratifiedEvaluationRunner()
        card = runner.run_stratified_eval(prompt_version="v1.0.0")
        self.assertEqual(card.total_cases, 100)
        self.assertEqual(card.passed_cases, 100)
        self.assertEqual(card.overall_pass_rate_pct, 100.0)
        self.assertEqual(card.overall_safety_score_pct, 100.0)
        self.assertEqual(len(card.strata_scorecards), 5)

    def test_inter_rater_cohens_kappa(self):
        """Verify statistical Cohen's Kappa inter-rater agreement calculation."""
        r1 = ["PASS"] * 35 + ["FAIL"] * 10 + ["PARTIAL"] * 5
        r2 = ["PASS"] * 33 + ["PARTIAL"] * 2 + ["FAIL"] * 9 + ["PASS"] * 1 + ["PARTIAL"] * 4 + ["FAIL"] * 1

        result = InterRaterAgreementEngine.calculate_cohens_kappa(r1, r2)
        self.assertEqual(result.total_samples, 50)
        self.assertGreater(result.observed_agreement_pct, 90.0)
        self.assertGreater(result.cohens_kappa, 0.80)
        self.assertIn("Near-Perfect", result.strength_interpretation)

    def test_judge_calibration_drift_and_recalibration(self):
        """Verify detection of leniency/harshness drift and mathematical recalibration."""
        base_scores = [0.85, 0.88, 0.90, 0.82, 0.79] * 10
        drifted_scores = [0.93, 0.95, 0.96, 0.91, 0.89] * 10

        report = JudgeCalibrationDriftDetector.analyze_drift(base_scores, drifted_scores)
        self.assertEqual(report.drift_status, "LENIENCY_DRIFT")
        self.assertTrue(report.requires_recalibration)
        self.assertLess(report.recalibration_factor, 1.0)

        # Apply recalibration
        recalibrated = JudgeCalibrationDriftDetector.apply_recalibration(drifted_scores, report.recalibration_factor)
        new_mean = sum(recalibrated) / len(recalibrated)
        self.assertAlmostEqual(new_mean, report.baseline_mean_score, delta=0.01)

    def test_online_ab_testing_hypothesis(self):
        """Verify two-sample z-test hypothesis testing for A/B rollout decisions."""
        decision = ABTestingEngine.simulate_production_experiment(sample_size=500)
        self.assertEqual(decision.sample_size_per_variant, 500)
        self.assertTrue(decision.is_statistically_significant)
        self.assertLess(decision.p_value, 0.05)
        self.assertEqual(decision.recommendation, "PROMOTE_VARIANT_B")


class TestDay14Session3ProductionMonitoring(unittest.TestCase):
    """Session 3: Tracing, Daily Time-Series, p95 Latency, Cost, Failure Categories, Alerting, Silent Decay."""

    def setUp(self):
        self.data_path = os.path.join(_day14_dir, "session_3", "production_traces.json")
        self.tracer = ProductionTracer()
        self.traces = self.tracer.load_traces_json(self.data_path)

    def test_traces_loaded_and_structured(self):
        """Verify real production traces are structured with latency, cost, and ground truth."""
        self.assertGreater(len(self.traces), 1000)
        sample = self.traces[0]
        self.assertTrue(sample.trace_id.startswith("TRC-"))
        self.assertGreater(sample.latency_ms, 0.0)
        self.assertGreater(sample.cost_usd, 0.0)
        self.assertIsNotNone(sample.groundedness)

    def test_time_series_daily_percentiles_and_costs(self):
        """Verify daily aggregation computes exact percentiles (p50, p90, p95, p99) and cost breakdowns."""
        time_series = MetricsAggregator.aggregate_by_day(self.traces)
        self.assertEqual(len(time_series), 14)  # 14 days of data

        for bucket in time_series:
            self.assertEqual(bucket.total_traces, 80)
            self.assertGreater(bucket.p95_latency_ms, 0.0)
            self.assertGreaterEqual(bucket.p95_latency_ms, bucket.p50_latency_ms)
            self.assertGreater(bucket.total_cost_usd, 0.0)
            self.assertIn("TIMEOUT", bucket.failure_category_counts)
            self.assertIn("TOOL_FAILURE", bucket.failure_category_counts)

    def test_alerting_engine_evaluates_thresholds(self):
        """Verify alerting engine fires on SLA breaches, p95 violations, and groundedness drops."""
        engine = AlertingEngine(failure_rate_threshold_pct=5.0, p95_latency_threshold_ms=1500.0)
        time_series = MetricsAggregator.aggregate_by_day(self.traces)

        all_alerts = []
        for bucket in time_series:
            alerts = engine.evaluate_bucket(bucket)
            all_alerts.extend(alerts)

        self.assertGreater(len(all_alerts), 0)
        rule_names = {a.rule_name for a in all_alerts}
        self.assertIn("HIGH_FAILURE_RATE_SLA_BREACH", rule_names)
        self.assertIn("P95_LATENCY_SLA_VIOLATION", rule_names)

    def test_silent_quality_decay_statistical_detector(self):
        """Verify detection of silent quality decay using sliding-window statistical drift."""
        decay = MetricsAggregator.detect_silent_quality_decay(self.traces)
        self.assertTrue(decay.is_decaying)
        self.assertGreaterEqual(decay.decay_score, 0.50)
        self.assertLess(decay.groundedness_drift_pct, -5.0)
        self.assertGreater(decay.cost_inflation_pct, 20.0)


class TestDay14Session4IncidentResponse(unittest.TestCase):
    """Session 4: Kill Switches, Circuit Breakers, Rollbacks, Defensive Parsers, Runbook & Postmortem."""

    def setUp(self):
        baseline = PromptModelConfig(
            version="v1.0.0-stable",
            model_id="claude-3-5-sonnet-20241022",
            prompt_template="Produce raw JSON tool calls only.",
            max_tokens=2048,
        )
        self.controller = EmergencyKillSwitchController(
            initial_config=baseline,
            error_threshold=3,
            recovery_time_seconds=10.0,
        )

    def test_kill_switch_action_blocking(self):
        """Verify kill switch restricts destructive actions in READ_ONLY and EMERGENCY_SHUTDOWN modes."""
        self.controller.set_kill_switch(KillSwitchLevel.READ_ONLY, reason="Test drill")
        
        # Read-only tool should be allowed
        allowed, msg = self.controller.validate_action_execution("query_telemetry", is_destructive=False)
        self.assertTrue(allowed)

        # Destructive tool MUST be blocked
        allowed_dest, msg_dest = self.controller.validate_action_execution("drain_node", is_destructive=True)
        self.assertFalse(allowed_dest)
        self.assertIn("READ_ONLY", msg_dest)

        # Emergency shutdown blocks everything
        self.controller.set_kill_switch(KillSwitchLevel.EMERGENCY_SHUTDOWN, reason="Hard shutdown")
        allowed_any, _ = self.controller.validate_action_execution("query_telemetry", is_destructive=False)
        self.assertFalse(allowed_any)

    def test_circuit_breaker_trips_on_consecutive_errors(self):
        """Verify circuit breaker trips to OPEN upon consecutive provider errors."""
        self.assertEqual(self.controller.circuit_state, CircuitBreakerState.CLOSED)
        self.controller.record_provider_result(is_success=False)
        self.controller.record_provider_result(is_success=False)
        self.controller.record_provider_result(is_success=False)

        self.assertEqual(self.controller.circuit_state, CircuitBreakerState.OPEN)
        self.assertEqual(self.controller.current_level, KillSwitchLevel.READ_ONLY)

    def test_prompt_model_config_rollback_to_lkg(self):
        """Verify automated rollback reverts to Last Known Good (LKG) configuration."""
        candidate = PromptModelConfig(
            version="v2.0.0-candidate",
            model_id="claude-3-5-sonnet-latest",
            prompt_template="Experimental candidate prompt.",
            max_tokens=1024,
        )
        self.controller.deploy_config(candidate)
        self.assertEqual(self.controller.active_config.version, "v2.0.0-candidate")

        # Execute rollback
        restored = self.controller.rollback_to_last_known_good(reason="Regression in v2.0.0")
        self.assertEqual(restored.version, "v1.0.0-stable")
        self.assertEqual(self.controller.active_config.version, "v1.0.0-stable")

    def test_defensive_json_parser_mitigates_markdown_drift(self):
        """Verify defensive parser strips markdown code fences (ACT-01 mitigation from postmortem)."""
        drifted_payload = "```json\n{\"action\": \"query_telemetry\", \"target\": \"payment-core\"}\n```"
        parsed = defensive_json_parser(drifted_payload)
        self.assertEqual(parsed["action"], "query_telemetry")
        self.assertEqual(parsed["target"], "payment-core")


if __name__ == "__main__":
    unittest.main(verbosity=2)
