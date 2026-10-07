"""
Day 14 - Session 2: Evaluation at Scale Master CLI
===================================================
Provides comprehensive commands to demonstrate:
  1. 100-Case Stratified Dataset Mining & Export (--mine-dataset)
  2. Batch Evaluation across all 100 cases with per-stratum scorecards (--eval-100)
  3. Inter-Rater Agreement & Cohen's Kappa Analysis (--check-inter-rater)
  4. Judge Calibration Drift & Recalibration Engine (--audit-drift)
  5. Online Production A/B Testing & Hypothesis Testing (--simulate-ab-test)
"""

import os
import sys
import argparse
from typing import List, Dict, Any

try:
    from day_14.session_2.stratified_dataset import StratifiedDatasetRegistry, StratifiedTestCase
    from day_14.session_2.trace_miner import mine_100_stratified_cases
    from day_14.session_2.eval_runner import StratifiedEvaluationRunner
    from day_14.session_2.inter_rater_agreement import InterRaterAgreementEngine
    from day_14.session_2.judge_calibration_drift import JudgeCalibrationDriftDetector
    from day_14.session_2.ab_testing_framework import ABTestingEngine
except ImportError:
    from stratified_dataset import StratifiedDatasetRegistry, StratifiedTestCase
    from trace_miner import mine_100_stratified_cases
    from eval_runner import StratifiedEvaluationRunner
    from inter_rater_agreement import InterRaterAgreementEngine
    from judge_calibration_drift import JudgeCalibrationDriftDetector
    from ab_testing_framework import ABTestingEngine


def print_banner(title: str) -> None:
    print("\n" + "=" * 95)
    print(f" {title.center(93)} ")
    print("=" * 95)


def demo_mine_dataset() -> None:
    print_banner("1. TRACE MINER: 100 STRATIFIED GOLDEN CASES GENERATION")
    cases = mine_100_stratified_cases()
    breakdown = StratifiedDatasetRegistry.get_strata_breakdown(cases)

    export_path = os.path.join(os.path.dirname(__file__), "golden_dataset_100.json")
    StratifiedDatasetRegistry.export_json(cases, export_path)

    print(f"Total Cases Mined from Production Traces: {len(cases)}")
    print(f"Exported Benchmark Artifact             : {export_path}")
    print("-" * 95)
    print(f"| {'Stratum Query Type':<26} | {'Target Cases':<12} | {'Traffic Weight':<16} |")
    print("-" * 95)
    weights = {
        "INFRA_DIAGNOSTIC": "35%",
        "DESTRUCTIVE_REMEDIATION": "25%",
        "DATABASE_STORAGE": "20%",
        "NETWORK_INGRESS": "10%",
        "SECURITY_ADVERSARIAL": "10%",
    }
    for stratum, count in breakdown.items():
        print(f"| {stratum:<26} | {count:<12} | {weights.get(stratum, 'N/A'):<16} |")
    print("-" * 95)
    print("[PASS] Stratified dataset successfully mined and validated.")


def demo_eval_100(prompt_version: str = "v1.0.0") -> None:
    print_banner(f"2. BATCH EVALUATION OVER 100 CASES ({prompt_version})")
    runner = StratifiedEvaluationRunner()
    card = runner.run_stratified_eval(prompt_version=prompt_version)

    print(f"Overall Pass Rate    : {card.overall_pass_rate_pct:.1f}% ({card.passed_cases}/{card.total_cases})")
    print(f"Overall Safety Score : {card.overall_safety_score_pct:.1f}%")
    print(f"Mean Latency         : {card.mean_latency_ms:.1f}ms")
    print("-" * 95)
    print(f"| {'Stratum':<25} | {'Cases':<7} | {'Passed':<8} | {'Pass Rate':<11} | {'Safety Score':<14} |")
    print("-" * 95)
    for s_name, sc in card.strata_scorecards.items():
        print(
            f"| {s_name:<25} | {sc.total_cases:<7} | {sc.passed_cases:<8} | "
            f"{sc.pass_rate_pct:>5.1f}%     | {sc.safety_score_pct:>5.1f}%         |"
        )
    print("-" * 95)


def demo_inter_rater() -> None:
    print_banner("3. INTER-RATER AGREEMENT & COHEN'S KAPPA (HUMAN VS LLM JUDGE)")

    # Simulated ratings on 50 audit cases:
    # 44 agreements, 6 disagreements
    human_ratings = ["PASS"] * 35 + ["FAIL"] * 10 + ["PARTIAL"] * 5
    # LLM judge agrees on 43 out of 50
    llm_ratings = (
        ["PASS"] * 33 + ["PARTIAL"] * 2 +  # 2 minor disagreements on edge cases
        ["FAIL"] * 9 + ["PASS"] * 1 +     # 1 leniency disagreement
        ["PARTIAL"] * 4 + ["FAIL"] * 1    # 1 borderline case
    )

    result = InterRaterAgreementEngine.calculate_cohens_kappa(
        rater_1_ratings=human_ratings,
        rater_2_ratings=llm_ratings,
        rater_1_name="Human_Staff_SRE_Consensus",
        rater_2_name="LLM_Judge_Claude_3.5_Sonnet",
    )

    print(f"Rater 1 (Ground Truth)   : {result.rater_1_name}")
    print(f"Rater 2 (Evaluator)      : {result.rater_2_name}")
    print(f"Total Audit Cases Evaluated: {result.total_samples}")
    print(f"Observed Agreement (P_o) : {result.observed_agreement_pct:.1f}%")
    print(f"Chance Agreement (P_e)   : {result.expected_agreement_chance_pct:.1f}%")
    print(f"Cohen's Kappa (kappa)    : {result.cohens_kappa:.4f}")
    print(f"Agreement Strength       : {result.strength_interpretation}")
    print("-" * 95)
    print("Confusion Matrix:")
    print(f"{'':<12} | {'LLM PASS':<10} | {'LLM FAIL':<10} | {'LLM PARTIAL':<12} |")
    for row_label, cols in result.confusion_matrix.items():
        print(f"Human {row_label:<6} | {cols.get('PASS', 0):<10} | {cols.get('FAIL', 0):<10} | {cols.get('PARTIAL', 0):<12} |")
    print("-" * 95)


def demo_judge_drift() -> None:
    print_banner("4. JUDGE CALIBRATION DRIFT DETECTOR")

    # Baseline scores distribution (Mean ~ 0.85, Std ~ 0.08)
    baseline_scores = [0.85, 0.88, 0.90, 0.82, 0.79, 0.86, 0.87, 0.84, 0.89, 0.85] * 5

    # Simulated drifted run where LLM judge experienced leniency drift (Mean ~ 0.93)
    current_drifted_scores = [0.93, 0.95, 0.96, 0.91, 0.89, 0.94, 0.95, 0.92, 0.97, 0.93] * 5

    report = JudgeCalibrationDriftDetector.analyze_drift(
        baseline_scores=baseline_scores,
        current_scores=current_drifted_scores,
        judge_name="LLM_Judge_Claude_3.5_Sonnet",
        cycle_name="Sprint_42_Continuous_Eval",
    )

    print(f"Judge Evaluated        : {report.judge_name}")
    print(f"Evaluation Cycle       : {report.evaluation_cycle}")
    print(f"Baseline Mean Score    : {report.baseline_mean_score:.3f} (std: {report.baseline_std_dev:.3f})")
    print(f"Current Mean Score     : {report.current_mean_score:.3f} (std: {report.current_std_dev:.3f})")
    print(f"Score Shift (Delta)    : {report.score_delta:+.3f}")
    print(f"Drift Classification   : {report.drift_status}")
    print(f"Recalibration Needed?  : {'YES' if report.requires_recalibration else 'NO'}")
    print(f"Scaling Factor         : {report.recalibration_factor:.4f}")
    print(f"Diagnostic Report      : {report.diagnostic_details}")

    # Apply recalibration
    recalibrated = JudgeCalibrationDriftDetector.apply_recalibration(current_drifted_scores[:5], report.recalibration_factor)
    print(f"\nRecalibration Sample   : Uncalibrated: {current_drifted_scores[:5]}")
    print(f"                         Recalibrated : {recalibrated}")


def demo_ab_test() -> None:
    print_banner("5. ONLINE PRODUCTION A/B EXPERIMENT (1,000 SESSIONS)")
    decision = ABTestingEngine.simulate_production_experiment(
        experiment_name="Prompt_SRE_v1_Baseline_vs_Candidate",
        sample_size=500,
    )

    va = decision.variant_a_metrics
    vb = decision.variant_b_metrics

    print(f"Experiment Name        : {decision.experiment_name}")
    print(f"Sample Size Per Variant: {decision.sample_size_per_variant} sessions (Total: 1,000)")
    print("-" * 95)
    print(f"| Metric                      | Variant A (Baseline) | Variant B (Candidate) | Difference |")
    print("-" * 95)
    print(f"| Incident Resolution Rate    | {va.success_rate_pct:>6.1f}%              | {vb.success_rate_pct:>6.1f}%               | {vb.success_rate_pct - va.success_rate_pct:>+6.1f}%     |")
    print(f"| Human Escalation Rate       | {va.escalation_rate_pct:>6.1f}%              | {vb.escalation_rate_pct:>6.1f}%               | {vb.escalation_rate_pct - va.escalation_rate_pct:>+6.1f}%     |")
    print(f"| Mean Resolution Time (MTTR) | {va.mean_resolution_time_sec:>6.1f}s             | {vb.mean_resolution_time_sec:>6.1f}s              | {vb.mean_resolution_time_sec - va.mean_resolution_time_sec:>+6.1f}s     |")
    print(f"| Undo / Compensation Rate    | {va.undo_rate_pct:>6.1f}%              | {vb.undo_rate_pct:>6.1f}%               | {vb.undo_rate_pct - va.undo_rate_pct:>+6.1f}%     |")
    print("-" * 95)
    print(f"Two-Proportion Z-Score : z = {decision.z_score:.3f}")
    print(f"Calculated p-value     : p = {decision.p_value:.5f} (alpha = 0.05)")
    print(f"Statistically Significant? {'YES (p < 0.05)' if decision.is_statistically_significant else 'NO'}")
    print(f"Final Recommendation   : {decision.recommendation}")
    print(f"Executive Rationale    : {decision.rationale}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 14 Session 2: Evaluation at Scale")
    parser.add_argument("--mine-dataset", action="store_true", help="Mine and export 100 stratified cases")
    parser.add_argument("--eval-100", action="store_true", help="Run evaluation across 100 cases")
    parser.add_argument("--candidate", action="store_true", help="Run 100-case eval on candidate prompt")
    parser.add_argument("--check-inter-rater", action="store_true", help="Compute Cohen's Kappa agreement")
    parser.add_argument("--audit-drift", action="store_true", help="Check judge calibration drift")
    parser.add_argument("--simulate-ab-test", action="store_true", help="Run production A/B experiment")

    args = parser.parse_args()

    if args.mine_dataset:
        demo_mine_dataset()
    elif args.eval_100:
        version = "v1.1.0-regressed" if args.candidate else "v1.0.0"
        demo_eval_100(prompt_version=version)
    elif args.check_inter_rater:
        demo_inter_rater()
    elif args.audit_drift:
        demo_judge_drift()
    elif args.simulate_ab_test:
        demo_ab_test()
    else:
        # Run full master demo
        demo_mine_dataset()
        demo_eval_100("v1.0.0")
        demo_inter_rater()
        demo_judge_drift()
        demo_ab_test()


if __name__ == "__main__":
    main()
