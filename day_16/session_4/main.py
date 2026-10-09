"""
Day 16 - Session 4: Plan, Estimate & Eval Set First
CLI Entrypoint for Sprint Planning, MoSCoW Prioritisation, and Eval Set Inspection.
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

from sprint_board_manager import (
    EvalDatasetAuditor,
    SprintBoardManager,
    run_and_save_sprint_board
)


def display_header():
    print("=" * 82)
    print("        DAY 16 - SESSION 4: PLAN, ESTIMATE & EVAL SET FIRST")
    print("=" * 82)
    print("  Curriculum Task: Filled Sprint Board with estimates + 30-case eval set")
    print("  Principle: MoSCoW prioritisation; define the eval set BEFORE any code")
    print("  Attendees: Harsh Ramesh Nerkar (Intern) + Dr. Elena Rostova (Mentor)")
    print("=" * 82)


def display_sprint_board(data: Dict[str, Any]):
    tasks = data["moscow_tasks"]
    metrics = data["sprint_planning_metrics"]

    print("\n" + "=" * 82)
    print("                    FILLED SPRINT PLANNING BOARD (MoSCoW)")
    print("=" * 82)
    print(f"Capacity: {metrics['capacity_hours']} hrs | Committed: {metrics['committed_hours']} hrs ({metrics['capacity_load_pct']}% load) | Buffer: {metrics['buffer_hours']} hrs\n")

    print("[1] MUST HAVE (P0 - Non-Negotiable Core):")
    for t in tasks["MUST_HAVE"]:
        print(f"  • [{t['id']}] {t['name']:<46} | {t['sp']} SP ({t['hours']}h) | Owner: {t['owner']}")

    print("\n[2] SHOULD HAVE (P1 - High-Value Hardening):")
    for t in tasks["SHOULD_HAVE"]:
        print(f"  • [{t['id']}] {t['name']:<46} | {t['sp']} SP ({t['hours']}h) | Owner: {t['owner']}")

    print("\n[3] COULD HAVE (P2 - Stretch Enhancements):")
    for t in tasks["COULD_HAVE"]:
        print(f"  • [{t['id']}] {t['name']:<46} | {t['sp']} SP ({t['hours']}h) | Owner: {t['owner']}")

    print("\n[4] WON'T HAVE (P3 - Explicitly Excluded Scope):")
    for t in tasks["WONT_HAVE"]:
        print(f"  • [{t['id']}] {t['name']:<46} | Reason: {t['reason']}")
    print("=" * 82)


def display_eval_set(data: Dict[str, Any]):
    stats = data["eval_dataset_statistics"]
    print("\n" + "=" * 82)
    print("              30-CASE PRE-CODE EVALUATION SET BREAKDOWN")
    print("=" * 82)
    print(f"Total Cases: {stats['total_cases']}")
    print("\nCategories:")
    for cat, count in stats["categories"].items():
        pct = (count / stats["total_cases"]) * 100
        print(f"  • {cat:<24}: {count:>2} cases ({pct:>4.1f}%)")

    print("\nBlast Radius Tiers:")
    for tier, count in stats["blast_radius_tiers"].items():
        print(f"  • {tier:<26}: {count:>2} cases")

    print("\nExpected Human-in-the-Loop Actions:")
    for action, count in stats["expected_hitl_actions"].items():
        print(f"  • {action:<26}: {count:>2} cases")
    print("=" * 82)


def inspect_case(case_id: str, current_dir: str):
    dataset_path = os.path.join(current_dir, "eval_dataset_30.json")
    with open(dataset_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    target = next((c for c in cases if c["case_id"].upper() == case_id.upper()), None)
    if not target:
        print(f"[!] Case '{case_id}' not found.")
        return

    print("\n" + "=" * 82)
    print(f" TEST CASE INSPECTION: {target['case_id']} ({target['service']})")
    print("=" * 82)
    print(f" Category         : {target['category']}")
    print(f" Blast Radius Tier: {target['blast_radius_tier']}")
    print(f" HITL Action Req. : {target['expected_hitl_action']}")
    print(f" Query            : {target['query']}")
    print(f" Root Cause       : {target['ground_truth_root_cause']}")
    print(f" Remediation      : {target['ground_truth_action']}")
    print(f" Key Indicators   : {', '.join(target['key_indicators'])}")
    if target.get("live_telemetry"):
        print(f" Live Telemetry   : {json.dumps(target['live_telemetry'], indent=2)}")
    print("=" * 82)


def main():
    parser = argparse.ArgumentParser(description="Day 16 Session 4: Sprint Planning & Eval Set CLI")
    parser.add_argument("--board", action="store_true", help="Display the MoSCoW Sprint Board")
    parser.add_argument("--eval-set", action="store_true", help="Display 30-case evaluation set summary")
    parser.add_argument("--inspect", type=str, help="Inspect a specific test case (e.g. EVAL-001 or EVAL-025)")
    parser.add_argument("--validate", action="store_true", help="Audit evaluation dataset schema")
    args = parser.parse_args()

    display_header()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    board_file = os.path.join(current_dir, "SPRINT_BOARD_DATA.json")

    if args.validate:
        dataset_path = os.path.join(current_dir, "eval_dataset_30.json")
        auditor = EvalDatasetAuditor(dataset_path)
        valid, errors = auditor.validate_schema()
        if valid:
            print("\n[✓] Evaluation dataset validation SUCCESS. Exactly 30 cases satisfy schema.")
        else:
            print("\n[✗] Validation failed:")
            for e in errors:
                print(f"  - {e}")
        return

    if args.inspect:
        inspect_case(args.inspect, current_dir)
        return

    if not os.path.exists(board_file):
        data = run_and_save_sprint_board(current_dir)
    else:
        with open(board_file, "r", encoding="utf-8") as f:
            data = json.load(f)

    if args.eval_set:
        display_eval_set(data)
    else:
        display_sprint_board(data)
        display_eval_set(data)
        print("\nRun with '--inspect <case_id>' or '--validate' to audit specific test cases.")


if __name__ == "__main__":
    main()
