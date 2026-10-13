"""
Day 16 - Session 04: Sprint Planning & Pre-Code 30-Case Evaluation Set
Demonstrates MoSCoW sprint board planning, capacity budgeting,
and pre-code validation of the 30-case golden evaluation dataset.
"""

from __future__ import annotations
import os
import json
from sprint_board_manager import (
    EvalDatasetAuditor,
    SprintBoardManager,
    run_and_save_sprint_board,
)


def main():
    print("Day 16 Session 04: Sprint Planning & Pre-Code Eval Suite\n")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    board_file = os.path.join(current_dir, "SPRINT_BOARD_DATA.json")

    if not os.path.exists(board_file):
        data = run_and_save_sprint_board(current_dir)
    else:
        with open(board_file, "r", encoding="utf-8") as f:
            data = json.load(f)

    # 1. Sprint Capacity
    metrics = data["sprint_planning_metrics"]
    print(f"Sprint Capacity: {metrics['capacity_hours']} hrs | Committed: {metrics['committed_hours']} hrs ({metrics['capacity_load_pct']}% load)")

    # 2. MoSCoW Breakdown
    tasks = data["moscow_tasks"]
    print(f"Must-Have Tasks:   {len(tasks['MUST_HAVE'])} tasks")
    print(f"Should-Have Tasks: {len(tasks['SHOULD_HAVE'])} tasks")
    print(f"Could-Have Tasks:  {len(tasks['COULD_HAVE'])} tasks")

    # 3. Eval Dataset Validation
    stats = data["eval_dataset_statistics"]
    print(f"\nPre-Code Golden Eval Set: {stats['total_cases']} cases across {len(stats['categories'])} categories.")

    dataset_path = os.path.join(current_dir, "eval_dataset_30.json")
    auditor = EvalDatasetAuditor(dataset_path)
    valid, errors = auditor.validate_schema()
    assert valid is True, f"Eval dataset schema invalid: {errors}"
    print("Eval Dataset Schema: 100% Validated.")


if __name__ == "__main__":
    main()
