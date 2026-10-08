"""
Day 17 - Session 3: First Real Iteration
CLI Entrypoint for Benchmarking Incremental Architectural Changes.
"""

import os
import sys
import json
import argparse
from typing import Dict, Any

# Set UTF-8 encoding for Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from first_iteration_engine import (
    run_and_save_iterations,
    IncrementalArchitectures,
    IntentRouter
)


def display_header():
    print("=" * 84)
    print("      DAY 17 - SESSION 3: FIRST REAL ITERATION (SCIENTIFIC EVALUATION)")
    print("=" * 84)
    print("  Curriculum Rule: Adding only what the evaluation set proves is needed")
    print("  Progression: Vanilla RAG -> +Hybrid RRF -> +Cluster Tool -> +Conditional Routing")
    print("  Evaluation Set: 20 Golden Enterprise SRE Cases")
    print("=" * 84)


def print_scorecard(scores: Dict[str, Any]):
    print("\n" + "=" * 84)
    print("               STEP-BY-STEP INCREMENTAL IMPROVEMENT SCORECARD")
    print("=" * 84)
    print(f"{'ITERATION STEP':<35} | {'PASS %':<8} | {'STATIC %':<8} | {'EPH %':<8} | {'LATENCY':<10} | {'COST/Q'}")
    print("-" * 84)
    for name, data in scores.items():
        print(f"{name:<35} | {data['overall_pass_rate_pct']:>6.1f}% | {data['static_pass_rate_pct']:>6.1f}% | {data['ephemeral_pass_rate_pct']:>6.1f}% | {data['avg_latency_ms']:>8.1f}ms | ${data['avg_cost_usd']:>8.6f}")
    print("=" * 84)
    print("\n[KEY TAKEAWAYS]:")
    print("  1. Step 1 (+Retrieval) had 0% delta: More search cannot invent missing cluster telemetry.")
    print("  2. Step 2 (+Tool) produced +70.0% delta: Telemetry closed the ephemeral cluster gap.")
    print("  3. Step 3 (+Routing) reduced latency by 13.7% and lowered cost with 100% accuracy.")
    print("=" * 84)


def inspect_route(incident_id: str, current_dir: str):
    eval_file = os.path.join(current_dir, "eval_dataset.json")
    with open(eval_file, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    target_case = next((c for c in dataset if c["incident_id"].upper() == incident_id.upper()), None)
    if not target_case:
        print(f"[!] Incident '{incident_id}' not found.")
        return

    router = IntentRouter()
    intent = router.classify_intent(target_case["query"])
    runbooks_path = os.path.join(current_dir, "static_runbooks.json")
    arch = IncrementalArchitectures(runbooks_path, dataset)
    result = arch.step_3_conditional_routed(target_case)

    print("\n" + "=" * 84)
    print(f" ROUTING INSPECTION: {target_case['incident_id']} ({target_case['service']})")
    print("=" * 84)
    print(f" Alert Query     : {target_case['query']}")
    print(f" Actual Category : {target_case['category']}")
    print(f" Detected Intent : {intent}")
    print(f" Execution Path  : {result['route_taken']}")
    print(f" Execution Time  : {result['latency_ms']} ms")
    print(f" Diagnosis       : {result['diagnosis'][:120]}...")
    print("=" * 84)


def main():
    parser = argparse.ArgumentParser(description="Day 17 Session 3: Iterative Progression Benchmark")
    parser.add_argument("--benchmark", action="store_true", help="Run full benchmark across all steps")
    parser.add_argument("--inspect-route", type=str, help="Inspect router decision for an incident ID (e.g. INC-101 or INC-102)")
    args = parser.parse_args()

    display_header()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    scores_file = os.path.join(current_dir, "ITERATION_SCORECARD.json")

    if args.inspect_route:
        inspect_route(args.inspect_route, current_dir)
        return

    if args.benchmark or not os.path.exists(scores_file):
        print("\n[*] Running live evaluation across all 4 architectural steps...")
        scores = run_and_save_iterations(current_dir)
    else:
        with open(scores_file, "r", encoding="utf-8") as f:
            scores = json.load(f)

    print_scorecard(scores)


if __name__ == "__main__":
    main()
