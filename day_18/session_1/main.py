"""
Day 18 - Session 1: Standup & Replan
CLI Entrypoint for Sprint 2 Standup, Re-estimation, and Scope Cut Review.
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

from replan_manager import run_and_save_replan


def display_header():
    print("=" * 82)
    print("           DAY 18 - SESSION 1: STANDUP & HONEST RE-ESTIMATION")
    print("=" * 82)
    print("  Curriculum Task: Updated Sprint Board with a documented scope decision")
    print("  Principle: Cutting scope deliberately rather than silently missing it")
    print("  Attendees: Harsh Ramesh Nerkar (Intern) + Dr. Elena Rostova (Mentor)")
    print("=" * 82)


def display_board(data: Dict[str, Any]):
    post = data["post_replan"]
    tasks = data["tasks"]

    print("\n" + "=" * 82)
    print("                    UPDATED SPRINT 2 BOARD (POST-REPLAN)")
    print("=" * 82)
    print(f"Capacity: {data['capacity_hours']} hrs | Committed: {post['must_hours']} hrs ({post['capacity_load_pct']}% load) | Buffer: {post['buffer_hours']} hrs\n")

    print("[1] MUST HAVE (P0 - Non-Negotiable Core Delivery):")
    for t in tasks:
        if t["category"] == "MUST_HAVE":
            print(f"  • [{t['id']}] {t['name']:<46} | {t['sp']} SP ({t['hours']}h)")

    print("\n[2] SHOULD HAVE (P1 - Performance Hardening):")
    for t in tasks:
        if t["category"] == "SHOULD_HAVE":
            print(f"  • [{t['id']}] {t['name']:<46} | {t['sp']} SP ({t['hours']}h)")

    print("\n[3] COULD HAVE (P2 - Demoted Scope / Contingent Stretch):")
    for t in tasks:
        if t["category"] == "COULD_HAVE":
            cut_flag = " [DEMOTED FROM MUST]" if t.get("is_cut") else ""
            print(f"  • [{t['id']}] {t['name']:<46} | {t['sp']} SP ({t['hours']}h){cut_flag}")
    print("=" * 82)


def display_scope_cut(data: Dict[str, Any]):
    print("\n" + "=" * 82)
    print("                   DOCUMENTED SCOPE CUT DECISION")
    print("=" * 82)
    for cut in data["scope_cuts"]:
        print(f"Task ID     : {cut['task_id']}")
        print(f"Task Name   : {cut['task_name']}")
        print(f"Migration   : {cut['from_category']}  -->  {cut['to_category']}")
        print(f"Hours Freed : {cut['hours']} hrs ({cut['story_points']} Story Points)")
        print(f"Rationale   : {cut['reason']}")
        print(f"Sign-Off By : {cut['approver']}")
    print("-" * 82)
    print(f"Capacity Impact: Pre-replan load was {data['pre_replan']['must_hours']}h (+{data['pre_replan']['deficit_hours']}h deficit).")
    print(f"Post-replan load is {data['post_replan']['must_hours']}h, creating a safe {data['post_replan']['buffer_hours']}h buffer.")
    print("=" * 82)


def main():
    parser = argparse.ArgumentParser(description="Day 18 Session 1: Sprint 2 Replan CLI")
    parser.add_argument("--board", action="store_true", help="Display updated Sprint 2 Board")
    parser.add_argument("--scope-cut", action="store_true", help="Display documented scope cut rationale")
    args = parser.parse_args()

    display_header()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    replan_file = os.path.join(current_dir, "REPLAN_DATA.json")

    if not os.path.exists(replan_file):
        data = run_and_save_replan(current_dir)
    else:
        with open(replan_file, "r", encoding="utf-8") as f:
            data = json.load(f)

    if args.scope_cut:
        display_scope_cut(data)
    else:
        display_board(data)
        display_scope_cut(data)


if __name__ == "__main__":
    main()
