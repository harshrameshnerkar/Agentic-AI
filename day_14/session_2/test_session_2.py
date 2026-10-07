"""
Day 14 - Session 2: Unit & Integration Test Suite
==================================================
Verifies:
  1. Exact 100-case dataset creation and strata distributions
  2. JSON export and round-trip schema deserialization
  3. Cohen's Kappa inter-rater agreement computation
  4. Judge calibration drift detection (leniency & harshness)
  5. Online A/B hypothesis test (two-proportion z-test)
  6. Stratified evaluation runner scorecards
"""

import os
import unittest
from typing import List, Dict, Any

try:
    from day_14.session_2.stratified_dataset import StratifiedTestCase, StratifiedDatasetRegistry
    from day_14.session_2.trace_miner import mine_100_stratified_cases
    from day_14.session_2.inter_rater_agreement import InterRaterAgreementEngine
    from day_14.session_2.judge_calibration_drift import JudgeCalibrationDriftDetector
    from day_14.session_2.ab_testing_framework import ABTestingEngine
    from day_14.session_2.eval_runner import StratifiedEvaluationRunner
except ImportError:
    from stratified_dataset import StratifiedTestCase, StratifiedDatasetRegistry
    from trace_miner import mine_100_stratified_cases
    from inter_rater_agreement import InterRaterAgreementEngine
    from judge_calibration_drift import JudgeCalibrationDriftDetector
    from ab_testing_framework import ABTestingEngine
    from eval_runner import StratifiedEvaluationRunner


class EvaluationAtScaleTestSuite(unittest.TestCase):

    def setUp(self) -> None:
        self.cases = mine_100_stratified_cases()

    def test_01_strata_distribution(self) -> None:
        """Verifies exactly 100 cases are created with proper stratification quotas."""
        self.assertEqual(len(self.cases), 100)
        breakdown = StratifiedDatasetRegistry.get_strata_breakdown(self.cases)

        self.assertEqual(breakdown["INFRA_DIAGNOSTIC"], 25)
        self.assertEqual(breakdown["DESTRUCTIVE_REMEDIATION"], 25)
        self.assertEqual(breakdown["DATABASE_STORAGE"], 20)
        self.assertEqual(breakdown["NETWORK_INGRESS"], 15)
        self.assertEqual(breakdown["SECURITY_ADVERSARIAL"], 15)

    def test_02_json_export_and_roundtrip(self) -> None:
        """Verifies that the dataset exports to valid JSON and loads identically."""
        temp_path = os.path.join(os.path.dirname(__file__), "test_golden_100.json")
        try:
            StratifiedDatasetRegistry.export_json(self.cases, temp_path)
            self.assertTrue(os.path.exists(temp_path))

            loaded = StratifiedDatasetRegistry.load_json(temp_path)
            self.assertEqual(len(loaded), 100)
            self.assertEqual(loaded[0].case_id, self.cases[0].case_id)
            self.assertEqual(loaded[-1].case_id, self.cases[-1].case_id)
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except PermissionError:
                    pass

    def test_03_cohens_kappa_calculation(self) -> None:
        """Verifies Cohen's Kappa calculation on perfect and realistic agreement."""
        # 1. Perfect agreement
        ratings_a = ["PASS", "FAIL", "PARTIAL", "PASS"] * 10
        perfect_res = InterRaterAgreementEngine.calculate_cohens_kappa(ratings_a, ratings_a)
        self.assertEqual(perfect_res.cohens_kappa, 1.0)
        self.assertEqual(perfect_res.observed_agreement_pct, 100.0)

        # 2. Substantial agreement (85% observed)
        ratings_b = ["PASS"] * 35 + ["FAIL"] * 10 + ["PARTIAL"] * 5
        ratings_c = ["PASS"] * 33 + ["PARTIAL"] * 2 + ["FAIL"] * 9 + ["PASS"] * 1 + ["PARTIAL"] * 5
        res = InterRaterAgreementEngine.calculate_cohens_kappa(ratings_b, ratings_c)
        self.assertGreater(res.cohens_kappa, 0.70)
        self.assertIn("Agreement", res.strength_interpretation)

    def test_04_judge_calibration_drift(self) -> None:
        """Verifies detection of leniency drift and computation of recalibration scaling."""
        baseline = [0.80] * 30
        drifted = [0.92] * 30  # +0.12 shift
        report = JudgeCalibrationDriftDetector.analyze_drift(baseline, drifted)

        self.assertEqual(report.drift_status, "LENIENCY_DRIFT")
        self.assertTrue(report.requires_recalibration)
        self.assertLess(report.recalibration_factor, 1.0)

        # Apply recalibration
        recal = JudgeCalibrationDriftDetector.apply_recalibration([0.92], report.recalibration_factor)
        self.assertAlmostEqual(recal[0], 0.80, places=2)

    def test_05_ab_testing_hypothesis_test(self) -> None:
        """Verifies two-proportion z-test and decision logic."""
        decision = ABTestingEngine.simulate_production_experiment(sample_size=500)

        self.assertTrue(decision.is_statistically_significant)
        self.assertLess(decision.p_value, 0.05)
        self.assertGreater(decision.z_score, 0.0)
        self.assertEqual(decision.recommendation, "PROMOTE_VARIANT_B")

    def test_06_eval_runner_100_cases(self) -> None:
        """Verifies stratified evaluation runner over all 100 cases."""
        runner = StratifiedEvaluationRunner(self.cases)
        card_v1 = runner.run_stratified_eval("v1.0.0")
        self.assertEqual(card_v1.total_cases, 100)
        self.assertEqual(card_v1.passed_cases, 100)
        self.assertEqual(card_v1.overall_pass_rate_pct, 100.0)
        self.assertEqual(len(card_v1.strata_scorecards), 5)

        card_cand = runner.run_stratified_eval("v1.1.0-regressed")
        self.assertLess(card_cand.overall_pass_rate_pct, 100.0)
        self.assertEqual(card_cand.strata_scorecards["DESTRUCTIVE_REMEDIATION"].pass_rate_pct, 0.0)


if __name__ == "__main__":
    unittest.main()
