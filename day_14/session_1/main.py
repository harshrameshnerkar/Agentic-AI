"""
Day 14 - Session 1: Master CLI & CI Simulation Runner
======================================================
Provides interactive commands to test:
  1. Baseline CI Evaluation (--run-baseline) -> PASSES with 100%
  2. Candidate PR CI Evaluation (--run-candidate) -> BLOCKS build on regression
  3. CI Quality Gate comparison (--ci-check)
  4. Dark Traffic Shadow Mirroring (--simulate-shadow)
  5. Progressive Canary Rollout with Automated Rollback (--simulate-canary)
"""

import sys
import os
import argparse
from typing import Dict, Any

try:
    from day_14.session_1.prompt_registry import PromptRegistry
    from day_14.session_1.golden_dataset import GOLDEN_EVAL_SUITE
    from day_14.session_1.eval_harness import EvaluationHarness
    from day_14.session_1.ci_gate import run_ci_gate_pipeline
    from day_14.session_1.canary_shadow import ShadowDeploymentRouter, CanaryDeploymentController
except ImportError:
    from prompt_registry import PromptRegistry
    from golden_dataset import GOLDEN_EVAL_SUITE
    from eval_harness import EvaluationHarness
    from ci_gate import run_ci_gate_pipeline
    from canary_shadow import ShadowDeploymentRouter, CanaryDeploymentController


def print_banner(title: str) -> None:
    print("\n" + "=" * 95)
    print(f" {title.center(93)} ")
    print("=" * 95)


def demo_shadow_mirroring() -> None:
    print_banner("SHADOW DEPLOYMENT: DARK TRAFFIC MIRRORING AUDIT")
    router = ShadowDeploymentRouter(baseline_version="v1.0.0", candidate_version="v1.1.0-regressed")

    print("Simulating 8 production user requests routed to Baseline with Candidate in Shadow Mode...")
    for tc in GOLDEN_EVAL_SUITE[:8]:
        out = router.process_shadow_request(tc)
        rec = out["shadow_record"]
        print(f"  [{rec.request_id}] Query: '{rec.incident_query[:45]}...'")
        print(f"    - Baseline Tool: {rec.baseline_tool:<18} | Candidate Tool: {rec.candidate_tool}")
        print(f"    - Base Approval: {str(rec.baseline_approval):<18} | Cand Approval : {str(rec.candidate_approval)}")
        print(f"    - Behavioral Drift Detected? {'YES [DRIFT]' if rec.shadow_drift_detected else 'NO [MATCH]'}")
        print("-" * 95)

    stats = router.compute_shadow_drift_summary()
    print("\nShadow Traffic Audit Summary:")
    print(f"  - Total Requests Mirrored : {stats['total_shadow_requests']}")
    print(f"  - Behavioral Drift Rate   : {stats['drift_percentage']}%")
    print(f"  - Tool Agreement Rate     : {stats['tool_agreement_pct']}%")
    print(f"  - Safety Agreement Rate   : {stats['safety_agreement_pct']}%")
    print(f"  - Safe to Promote Canary? : {'NO (HALT DEPLOYMENT)' if not stats['safe_for_canary'] else 'YES'}")


def demo_canary_rollout() -> None:
    print_banner("CANARY PROGRESSIVE ROLLOUT & AUTOMATED WATCHDOG")
    controller = CanaryDeploymentController(
        baseline_version="v1.0.0",
        candidate_version="v1.1.0-regressed",
        max_error_threshold_pct=2.0,
    )

    print("Initiating progressive canary rollout: 5% -> 25% -> 50% -> 100%...")
    stages = controller.simulate_rollout(GOLDEN_EVAL_SUITE[:10])

    for s in stages:
        print(f"\n[CANARY STAGE: {s.traffic_percentage}% TRAFFIC ALLOCATION]")
        print(f"  - Requests Processed  : {s.requests_processed}")
        print(f"  - Canary Errors       : {s.canary_errors}")
        print(f"  - Safety Violations   : {s.canary_safety_violations}")
        print(f"  - Status              : {s.status}")
        if s.rollback_triggered:
            print("  [WATCHDOG TRIGGERED] Critical error & safety threshold breached!")
            print("  [AUTOMATED ROLLBACK] Traffic reverted 100% to stable Baseline (v1.0.0).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 14 Session 1: LLMOps Regression Suites & CI")
    parser.add_argument("--run-baseline", action="store_true", help="Run CI eval on Baseline Prompt v1.0.0")
    parser.add_argument("--run-candidate", action="store_true", help="Run CI eval on Regressed Candidate Prompt v1.1.0")
    parser.add_argument("--ci-check", action="store_true", help="Run CI gate comparing Candidate against Baseline")
    parser.add_argument("--simulate-shadow", action="store_true", help="Simulate dark traffic shadow mirroring")
    parser.add_argument("--simulate-canary", action="store_true", help="Simulate progressive canary deployment")

    args = parser.parse_args()

    if args.run_baseline:
        code = run_ci_gate_pipeline(candidate_version="v1.0.0", baseline_version="v1.0.0")
        sys.exit(code)
    elif args.run_candidate or args.ci_check:
        code = run_ci_gate_pipeline(
            candidate_version="v1.1.0-regressed",
            baseline_version="v1.0.0",
            export_report_path="day_14/session_1/eval_report_candidate.md",
        )
        sys.exit(code)
    elif args.simulate_shadow:
        demo_shadow_mirroring()
    elif args.simulate_canary:
        demo_canary_rollout()
    else:
        # Default: demonstrate CI gate failure on regression
        print("Running default CI gate comparison (Candidate v1.1.0-regressed vs Baseline v1.0.0)...")
        code = run_ci_gate_pipeline(
            candidate_version="v1.1.0-regressed",
            baseline_version="v1.0.0",
            export_report_path="day_14/session_1/eval_report_candidate.md",
        )
        sys.exit(code)


if __name__ == "__main__":
    main()
