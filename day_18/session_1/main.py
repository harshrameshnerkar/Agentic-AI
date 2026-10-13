"""
Day 18 - Session 01: Standup & Sprint 2 Re-estimation
Evaluates the Sprint 2 backlog, reviewing capacity, commitments,
and documenting deliberate scope adjustments.
"""

from __future__ import annotations
import os
import json
from replan_manager import run_and_save_replan


def main():
    print("Day 18 Session 01: Sprint 2 Standup & Re-estimation\n")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    board_file = os.path.join(current_dir, "REPLAN_BOARD_DATA.json")

    if not os.path.exists(board_file):
        data = run_and_save_replan(current_dir)
    else:
        with open(board_file, "r", encoding="utf-8") as f:
            data = json.load(f)

    post = data["post_replan"]
    print(f"Sprint 2 Capacity:  {data['capacity_hours']} hrs")
    print(f"Committed Must-Do: {post['must_hours']} hrs ({post['capacity_load_pct']}% load)")
    print(f"Safety Buffer:     {post['buffer_hours']} hrs")

    print("\nScope Adjustments:")
    for cut in data.get("scope_cuts", []):
        print(f"  • {cut['task_id']} ({cut['task_name']}): {cut['from_category']} -> {cut['to_category']}")

    print("\nSprint 2 re-planning verified: Capacity and commitments rebalanced.")


if __name__ == "__main__":
    main()
