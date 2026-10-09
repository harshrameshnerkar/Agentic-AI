"""
Day 18 - Session 4: Regression Suite
CLI Entrypoint for running the automated CI regression suite and inspecting test cases.
"""

import os
import sys
import json
import argparse

# Set UTF-8 encoding for Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from run_regression_suite import execute_one_command_suite


def display_header():
    print("=" * 82)
    print("        DAY 18 - SESSION 4: ONE-COMMAND AUTOMATED REGRESSION SUITE")
    print("=" * 82)
    print("  Curriculum Task: Automated suite with bug regressions, blocking on failure")
    print("  Evaluation Scale: 35 Golden Test Cases (Including 5 Bug Regression Cases)")
    print("  CI Contract: Exits 0 on Pass (>= 95% SLA) | Exits 1 on Regression (< 95%)")
    print("=" * 82)


def inspect_case(case_id: str, current_dir: str):
    dataset_path = os.path.join(current_dir, "regression_dataset_35.json")
    with open(dataset_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    target = next((c for c in cases if c["case_id"].upper() == case_id.upper()), None)
    if not target:
        print(f"[!] Case '{case_id}' not found in 35-case regression dataset.")
        return

    print("\n" + "=" * 82)
    print(f" REGRESSION CASE INSPECTION: {target['case_id']} ({target['service']})")
    print("=" * 82)
    print(f" Category         : {target['category']}")
    print(f" Blast Radius Tier: {target['blast_radius_tier']}")
    print(f" HITL Action Req. : {target['expected_hitl_action']}")
    print(f" Query            : {target['query']}")
    print(f" Root Cause       : {target['ground_truth_root_cause']}")
    print(f" Remediation      : {target['ground_truth_action']}")
    print(f" Key Indicators   : {', '.join(target['key_indicators'])}")
    print("=" * 82)


def main():
    parser = argparse.ArgumentParser(description="Day 18 Session 4: Regression Suite CLI")
    parser.add_argument("--simulate-fail", action="store_true", help="Demonstrate blocking CI build on regression")
    parser.add_argument("--inspect", type=str, help="Inspect a specific case (e.g. REG-031 or EVAL-001)")
    args = parser.parse_args()

    display_header()
    current_dir = os.path.dirname(os.path.abspath(__file__))

    if args.inspect:
        inspect_case(args.inspect, current_dir)
        return

    exit_code = execute_one_command_suite(simulate_failure=args.simulate_fail, output_dir=current_dir)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
