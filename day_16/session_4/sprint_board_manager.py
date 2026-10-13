"""
Day 16 - Session 4: Plan, Estimate & Eval Set First
Sprint Board Manager: Validates the 30-case evaluation set and computes MoSCoW metrics.
"""

import json
import os
import sys
from typing import Any, Dict, List, Tuple


class EvalDatasetAuditor:
    """Audits the 30-case pre-code evaluation set."""

    REQUIRED_FIELDS = [
        "case_id", "query", "category", "service", "blast_radius_tier",
        "expected_hitl_action", "ground_truth_root_cause",
        "ground_truth_action", "key_indicators"
    ]
    VALID_CATEGORIES = ["static_runbook", "ephemeral_cluster", "adversarial_red_line"]
    VALID_TIERS = ["Tier 1 (Read-Only)", "Tier 2 (Scoped Safe)", "Tier 3 (Consequential)"]
    VALID_HITL_ACTIONS = ["NONE", "HUMAN_APPROVAL_REQUIRED", "BLOCKED_RED_LINE"]

    def __init__(self, dataset_path: str):
        self.dataset_path = dataset_path
        with open(dataset_path, "r", encoding="utf-8") as f:
            self.dataset = json.load(f)

    def validate_schema(self) -> Tuple[bool, List[str]]:
        errors = []
        if len(self.dataset) != 30:
            errors.append(f"Expected 30 cases, found {len(self.dataset)}.")

        for idx, item in enumerate(self.dataset, 1):
            for field in self.REQUIRED_FIELDS:
                if field not in item:
                    errors.append(f"Case #{idx}: Missing '{field}'.")
            if item.get("category") not in self.VALID_CATEGORIES:
                errors.append(f"Case #{idx}: Invalid category.")
            if item.get("blast_radius_tier") not in self.VALID_TIERS:
                errors.append(f"Case #{idx}: Invalid tier.")
            if item.get("expected_hitl_action") not in self.VALID_HITL_ACTIONS:
                errors.append(f"Case #{idx}: Invalid HITL action.")
            if not isinstance(item.get("key_indicators"), list) or not item.get("key_indicators"):
                errors.append(f"Case #{idx}: key_indicators must be non-empty list.")

        return len(errors) == 0, errors

    def get_summary_statistics(self) -> Dict[str, Any]:
        categories: Dict[str, int] = {}
        tiers: Dict[str, int] = {}
        actions: Dict[str, int] = {}

        for item in self.dataset:
            categories[item["category"]] = categories.get(item["category"], 0) + 1
            tiers[item["blast_radius_tier"]] = tiers.get(item["blast_radius_tier"], 0) + 1
            actions[item["expected_hitl_action"]] = actions.get(item["expected_hitl_action"], 0) + 1

        return {
            "total_cases": len(self.dataset),
            "categories": categories,
            "blast_radius_tiers": tiers,
            "expected_hitl_actions": actions,
        }


class SprintBoardManager:
    """Computes sprint capacity and MoSCoW allocations."""

    MOSCOW_TASKS = {
        "MUST_HAVE": [
            {"id": "MUST-01", "name": "30-Case Golden Harness", "sp": 3, "hours": 2.5, "owner": "Harsh"},
            {"id": "MUST-02", "name": "De-Risk Riskiest Tool", "sp": 5, "hours": 4.0, "owner": "Harsh"},
            {"id": "MUST-03", "name": "Non-Agent Baseline Scoring", "sp": 3, "hours": 3.0, "owner": "Harsh"},
            {"id": "MUST-04", "name": "Ephemeral Diagnostic Tool", "sp": 5, "hours": 4.5, "owner": "Harsh"},
            {"id": "MUST-05", "name": "HMAC-SHA256 HITL Gateway", "sp": 5, "hours": 4.0, "owner": "Harsh"},
        ],
        "SHOULD_HAVE": [
            {"id": "SHOULD-01", "name": "Intent Router", "sp": 3, "hours": 2.5, "owner": "Harsh"},
            {"id": "SHOULD-02", "name": "Log Compactor", "sp": 3, "hours": 2.5, "owner": "Harsh"},
            {"id": "SHOULD-03", "name": "Redis State Cache", "sp": 5, "hours": 4.0, "owner": "Harsh"},
            {"id": "SHOULD-04", "name": "CI Regression Gate", "sp": 2, "hours": 2.0, "owner": "Harsh"},
        ],
        "COULD_HAVE": [
            {"id": "COULD-01", "name": "Slack Webhook Bot", "sp": 5, "hours": 4.0, "owner": "Harsh"},
            {"id": "COULD-02", "name": "Postmortem Generator", "sp": 3, "hours": 3.0, "owner": "Harsh"},
        ],
        "WONT_HAVE": [
            {"id": "WONT-01", "name": "DB Migrations", "reason": "Red Line 1"},
            {"id": "WONT-02", "name": "Train LLM from scratch", "reason": "Prohibitive cost"},
            {"id": "WONT-03", "name": "Multi-Cloud failover", "reason": "Out of scope"},
        ],
    }
    CAPACITY_HOURS = 32.0

    def compute_sprint_metrics(self) -> Dict[str, Any]:
        must = self.MOSCOW_TASKS["MUST_HAVE"]
        should = self.MOSCOW_TASKS["SHOULD_HAVE"]
        could = self.MOSCOW_TASKS["COULD_HAVE"]

        must_h = sum(t["hours"] for t in must)
        should_h = sum(t["hours"] for t in should)
        committed = must_h + should_h

        return {
            "capacity_hours": self.CAPACITY_HOURS,
            "must_have": {"sp": sum(t["sp"] for t in must), "hours": must_h, "task_count": len(must)},
            "should_have": {"sp": sum(t["sp"] for t in should), "hours": should_h, "task_count": len(should)},
            "could_have": {"sp": sum(t["sp"] for t in could), "hours": sum(t["hours"] for t in could), "task_count": len(could)},
            "wont_have_count": len(self.MOSCOW_TASKS["WONT_HAVE"]),
            "committed_hours": committed,
            "buffer_hours": max(0.0, self.CAPACITY_HOURS - committed),
            "capacity_load_pct": round((committed / self.CAPACITY_HOURS) * 100, 1),
        }


def run_and_save_sprint_board(output_dir: str = None) -> Dict[str, Any]:
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(__file__))

    dataset_path = os.path.join(output_dir, "eval_dataset_30.json")
    auditor = EvalDatasetAuditor(dataset_path)
    is_valid, errors = auditor.validate_schema()
    if not is_valid:
        raise ValueError(f"Eval dataset validation failed: {errors}")

    board = SprintBoardManager()
    data = {
        "timestamp": "2026-10-08T18:00:00Z",
        "eval_dataset_statistics": auditor.get_summary_statistics(),
        "sprint_planning_metrics": board.compute_sprint_metrics(),
        "moscow_tasks": board.MOSCOW_TASKS,
    }

    out_file = os.path.join(output_dir, "SPRINT_BOARD_DATA.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


if __name__ == "__main__":
    d = run_and_save_sprint_board()
    print("Sprint board saved to SPRINT_BOARD_DATA.json")
