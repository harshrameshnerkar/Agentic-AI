"""
Day 17 - Session 2: Simplest Thing That Works
CLI Entrypoint for Baseline Evaluation, Scorecard Inspection, and Error Analysis.
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

from baseline_runner import run_and_save_baselines, BaselineEvaluator


def display_header():
    print("=" * 80)
    print("     DAY 17 - SESSION 2: SIMPLEST THING THAT WORKS (BASELINE EVALUATION)")
    print("=" * 80)
    print("  Curriculum Goal: Establish baseline before building an agent")
    print("  Comparison: Plain Prompt (Zero-Shot) vs. Single Retrieval Call (Vanilla RAG)")
    print("  Evaluation Dataset: 20 Golden Enterprise SRE Incidents")
    print("=" * 80)


def print_scorecard(scores: Dict[str, Any]):
    p = scores["plain_summary"]
    r = scores["rag_summary"]

    print("\n" + "=" * 80)
    print("                    EMPIRICAL BASELINE SCORECARD")
    print("=" * 80)
    print(f"{'EVALUATION METRIC':<36} | {'PLAIN PROMPT':<18} | {'SINGLE RETRIEVAL RAG':<20}")
    print("-" * 80)
    print(f"{'Overall Pass Rate':<36} | {p['overall_pass_rate_pct']:>16.1f}% | {r['overall_pass_rate_pct']:>18.1f}%")
    print(f"{'Static Runbook Pass Rate (6)':<36} | {p['static_runbook_pass_rate_pct']:>16.1f}% | {r['static_runbook_pass_rate_pct']:>18.1f}%")
    print(f"{'Dynamic Incident Pass Rate (14)':<36} | {p['ephemeral_cluster_pass_rate_pct']:>16.1f}% | {r['ephemeral_cluster_pass_rate_pct']:>18.1f}%")
    print(f"{'Key Indicator Recall':<36} | {p['avg_indicator_recall_pct']:>16.1f}% | {r['avg_indicator_recall_pct']:>18.1f}%")
    print(f"{'Generic Guess / Hallucination Rate':<36} | {p['generic_guess_rate_pct']:>16.1f}% | {r['generic_guess_rate_pct']:>18.1f}%")
    print(f"{'Mean Latency (ms)':<36} | {p['avg_latency_ms']:>16.1f}ms | {r['avg_latency_ms']:>18.1f}ms")
    print(f"{'Cost per Query ($)':<36} | ${p['avg_cost_usd']:>15.6f} | ${r['avg_cost_usd']:>17.6f}")
    print("=" * 80)
    print("\n[KEY TAKEAWAY]: Single Retrieval Call (Vanilla RAG) solves 100% of static runbook")
    print("queries, but scores 0.0% on dynamic cluster incidents because root causes exist")
    print("in live cluster telemetry, NOT static documentation.")
    print("--> THIS PROVES AN AGENTIC / TOOL-AUGMENTED CHAIN IS REQUIRED FOR SESSION 3.")
    print("=" * 80)


def inspect_incident(incident_id: str, current_dir: str):
    eval_file = os.path.join(current_dir, "eval_dataset.json")
    with open(eval_file, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    target_case = next((c for c in dataset if c["incident_id"].upper() == incident_id.upper()), None)
    if not target_case:
        print(f"[!] Incident '{incident_id}' not found in golden dataset.")
        return

    print("\n" + "=" * 80)
    print(f" INCIDENT INSPECTION: {target_case['incident_id']} ({target_case['service']})")
    print("=" * 80)
    print(f" Category    : {target_case['category']}")
    print(f" Alert Query : {target_case['query']}")
    print(f"\n Ground Truth Root Cause:")
    print(f"   {target_case['ground_truth_root_cause']}")
    print(f"\n Ground Truth Remediation:")
    print(f"   {target_case['ground_truth_action']}")
    print(f"\n Required Key Indicators:")
    print(f"   {', '.join(target_case['key_indicators'])}")

    if target_case.get("live_telemetry"):
        print(f"\n Live Telemetry (Ephemeral Cluster State):")
        print(json.dumps(target_case["live_telemetry"], indent=4))
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Day 17 Session 2: Baseline Evaluator")
    parser.add_argument("--eval", action="store_true", help="Re-run evaluation and update score files")
    parser.add_argument("--summary", action="store_true", help="Display the summary scorecard")
    parser.add_argument("--inspect", type=str, help="Inspect ground truth and telemetry for an incident ID (e.g. INC-101)")
    args = parser.parse_args()

    display_header()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    scores_file = os.path.join(current_dir, "BASELINE_SCORES.json")

    if args.inspect:
        inspect_incident(args.inspect, current_dir)
        return

    if args.eval or not os.path.exists(scores_file):
        print("\n[*] Running live evaluation across 20 golden cases...")
        scores = run_and_save_baselines(current_dir)
    else:
        with open(scores_file, "r", encoding="utf-8") as f:
            scores = json.load(f)

    print_scorecard(scores)


if __name__ == "__main__":
    main()
