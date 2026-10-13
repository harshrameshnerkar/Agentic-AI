"""
Day 14 - Session 02: Evaluation at Scale & Judge Calibration
Demonstrates:
1. 100-case stratified dataset mining across incident domains.
2. Inter-rater agreement scoring (Cohen's kappa).
3. LLM-as-a-judge calibration drift auditing.
4. Online A/B testing hypothesis evaluation.
"""

from __future__ import annotations
from stratified_dataset import StratifiedDatasetRegistry
from trace_miner import mine_100_stratified_cases
from inter_rater_agreement import InterRaterAgreementEngine
from judge_calibration_drift import JudgeCalibrationDriftDetector
from ab_testing_framework import ABTestingEngine


def demo_dataset_and_kappa():
    print("\n--- 1. Stratified Dataset & Inter-Rater Agreement ---")
    cases = mine_100_stratified_cases()
    breakdown = StratifiedDatasetRegistry.get_strata_breakdown(cases)
    print(f"Total Mined Cases: {len(cases)} across {len(breakdown)} strata")

    kappa_engine = InterRaterAgreementEngine()
    kappa_res = kappa_engine.compute_cohens_kappa()
    print(f"Inter-Rater Cohen's Kappa: {kappa_res['kappa']:.3f} ({kappa_res['interpretation']})")
    assert kappa_res["kappa"] >= 0.70, "Judge agreement below minimum threshold!"


def demo_drift_and_ab_test():
    print("\n--- 2. Judge Calibration Drift & A/B Testing ---")
    detector = JudgeCalibrationDriftDetector()
    drift_res = detector.audit_drift()
    print(f"Judge Calibration Drift: {drift_res['drift_status']} (Mean Score Shift: {drift_res['score_delta']:+.3f})")

    ab_engine = ABTestingEngine()
    ab_res = ab_engine.simulate_experiment(sample_size=100)
    print(f"A/B Test Outcome: {ab_res['winner']} (p-value: {ab_res['p_value']:.4f}, Statistically Significant: {ab_res['is_significant']})")


def main():
    print("Day 14 Session 02: Large-Scale Evaluation & Judge Calibration\n")
    demo_dataset_and_kappa()
    demo_drift_and_ab_test()
    print("\nLarge-scale evaluation metrics verified.")


if __name__ == "__main__":
    main()
