"""
Day 14 - Session 01: CI Quality Gates & Canary Deployments
Demonstrates:
1. CI regression quality gate evaluating candidate prompts against golden benchmarks.
2. Shadow mirroring (dark traffic testing) to detect behavioral drift without user impact.
3. Progressive canary rollout with automated rollback on error spikes.
"""

from __future__ import annotations
from prompt_registry import PromptRegistry
from golden_dataset import GOLDEN_EVAL_SUITE
from ci_gate import run_ci_gate_pipeline
from canary_shadow import ShadowDeploymentRouter, CanaryDeploymentController


def demo_ci_gate():
    print("\n--- 1. CI Quality Gate Pipeline ---")
    res_stable = run_ci_gate_pipeline("v1.0.0-stable")
    print(f"Stable Version Gate:   {'PASSED' if res_stable['passed'] else 'FAILED'} (Pass Rate: {res_stable['metrics']['pass_rate']}%)")

    res_regressed = run_ci_gate_pipeline("v1.1.0-regressed")
    print(f"Regressed PR Gate:     {'PASSED' if res_regressed['passed'] else 'BLOCKED'} (Blocked as expected: {res_regressed.get('block_reason', 'Regressed')})")
    assert res_regressed["passed"] is False, "CI gate failed to block regressed candidate!"


def demo_shadow_and_canary():
    print("\n--- 2. Shadow Traffic Mirroring & Canary Rollout ---")
    router = ShadowDeploymentRouter(baseline_version="v1.0.0", candidate_version="v1.1.0-regressed")

    for tc in GOLDEN_EVAL_SUITE[:5]:
        router.process_shadow_request(tc)

    stats = router.compute_shadow_drift_summary()
    print(f"Shadow Requests: {stats['total_shadow_requests']} | Drift: {stats['drift_percentage']}% | Safe: {stats['safe_for_canary']}")

    controller = CanaryDeploymentController()
    step_res = controller.step_canary(candidate_error_rate=0.08)
    print(f"Canary Traffic: {step_res['traffic_percentage']}% | Status: {step_res['status']}")


def main():
    print("Day 14 Session 01: CI Regression Harness & Safe Deployment\n")
    demo_ci_gate()
    demo_shadow_and_canary()
    print("\nCI gate and canary controls verified.")


if __name__ == "__main__":
    main()
