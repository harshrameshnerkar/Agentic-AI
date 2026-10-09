"""
Day 16 - Session 4: Plan, Estimate & Eval Set First
Sprint Board Manager: Validates the 30-case pre-code evaluation dataset,
computes MoSCoW capacity metrics, and exports structured sprint telemetry.
"""

import os
import sys
import json
from typing import Dict, Any, List, Tuple

# Set UTF-8 encoding for Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


class EvalDatasetAuditor:
    """Audits and validates the 30-case pre-code evaluation set."""

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
            errors.append(f"Expected exactly 30 test cases, found {len(self.dataset)}.")

        for idx, item in enumerate(self.dataset, 1):
            for field in self.REQUIRED_FIELDS:
                if field not in item:
                    errors.append(f"Case #{idx} ({item.get('case_id', 'UNKNOWN')}): Missing required field '{field}'.")

            if item.get("category") not in self.VALID_CATEGORIES:
                errors.append(f"Case #{idx}: Invalid category '{item.get('category')}'.")

            if item.get("blast_radius_tier") not in self.VALID_TIERS:
                errors.append(f"Case #{idx}: Invalid blast radius tier '{item.get('blast_radius_tier')}'.")

            if item.get("expected_hitl_action") not in self.VALID_HITL_ACTIONS:
                errors.append(f"Case #{idx}: Invalid HITL action '{item.get('expected_hitl_action')}'.")

            if not isinstance(item.get("key_indicators"), list) or len(item.get("key_indicators", [])) == 0:
                errors.append(f"Case #{idx}: key_indicators must be a non-empty list.")

        is_valid = len(errors) == 0
        return is_valid, errors

    def get_summary_statistics(self) -> Dict[str, Any]:
        categories = {}
        tiers = {}
        hitl_actions = {}

        for item in self.dataset:
            cat = item["category"]
            categories[cat] = categories.get(cat, 0) + 1

            tier = item["blast_radius_tier"]
            tiers[tier] = tiers.get(tier, 0) + 1

            action = item["expected_hitl_action"]
            hitl_actions[action] = hitl_actions.get(action, 0) + 1

        return {
            "total_cases": len(self.dataset),
            "categories": categories,
            "blast_radius_tiers": tiers,
            "expected_hitl_actions": hitl_actions
        }


class SprintBoardManager:
    """Manages the MoSCoW sprint board, story point estimation, and capacity planning."""

    MOSCOW_TASKS = {
        "MUST_HAVE": [
            {"id": "MUST-01", "name": "30-Case Golden Evaluation Harness", "sp": 3, "hours": 2.5, "owner": "Harsh"},
            {"id": "MUST-02", "name": "De-Risk Riskiest Tool Integration", "sp": 5, "hours": 4.0, "owner": "Harsh"},
            {"id": "MUST-03", "name": "Non-Agent Baseline Scoring (Plain vs RAG)", "sp": 3, "hours": 3.0, "owner": "Harsh"},
            {"id": "MUST-04", "name": "Ephemeral Cluster Telemetry Diagnostic Tool", "sp": 5, "hours": 4.5, "owner": "Harsh"},
            {"id": "MUST-05", "name": "Cryptographic HMAC-SHA256 HITL Gateway", "sp": 5, "hours": 4.0, "owner": "Harsh"}
        ],
        "SHOULD_HAVE": [
            {"id": "SHOULD-01", "name": "Sub-5ms Intent Router", "sp": 3, "hours": 2.5, "owner": "Harsh"},
            {"id": "SHOULD-02", "name": "In-Process 50k-Line Log Compactor", "sp": 3, "hours": 2.5, "owner": "Harsh"},
            {"id": "SHOULD-03", "name": "Redis Cluster State In-Memory Cache (30s TTL)", "sp": 5, "hours": 4.0, "owner": "Harsh"},
            {"id": "SHOULD-04", "name": "Automated CI Regression Gate", "sp": 2, "hours": 2.0, "owner": "Harsh"}
        ],
        "COULD_HAVE": [
            {"id": "COULD-01", "name": "Slack / PagerDuty Interactive Webhook Bot", "sp": 5, "hours": 4.0, "owner": "Harsh"},
            {"id": "COULD-02", "name": "Automated Postmortem Markdown Generator", "sp": 3, "hours": 3.0, "owner": "Harsh"}
        ],
        "WONT_HAVE": [
            {"id": "WONT-01", "name": "Autonomous Production Database Migrations", "reason": "Violates Red Line #1"},
            {"id": "WONT-02", "name": "Fine-Tuning a Foundation LLM from Scratch", "reason": "Prohibitive compute cost ($>50k)"},
            {"id": "WONT-03", "name": "Multi-Cloud Autonomous Failover (AWS to GCP)", "reason": "Out of scope"}
        ]
    }

    CAPACITY_HOURS = 32.0  # 4 engineering days x 8 hours = 32 hours total

    def compute_sprint_metrics(self) -> Dict[str, Any]:
        must_sp = sum(t["sp"] for t in self.MOSCOW_TASKS["MUST_HAVE"])
        must_hours = sum(t["hours"] for t in self.MOSCOW_TASKS["MUST_HAVE"])

        should_sp = sum(t["sp"] for t in self.MOSCOW_TASKS["SHOULD_HAVE"])
        should_hours = sum(t["hours"] for t in self.MOSCOW_TASKS["SHOULD_HAVE"])

        could_sp = sum(t["sp"] for t in self.MOSCOW_TASKS["COULD_HAVE"])
        could_hours = sum(t["hours"] for t in self.MOSCOW_TASKS["COULD_HAVE"])

        committed_hours = must_hours + should_hours
        buffer_hours = max(0.0, self.CAPACITY_HOURS - committed_hours)
        load_pct = (committed_hours / self.CAPACITY_HOURS) * 100

        return {
            "capacity_hours": self.CAPACITY_HOURS,
            "must_have": {"sp": must_sp, "hours": must_hours, "task_count": len(self.MOSCOW_TASKS["MUST_HAVE"])},
            "should_have": {"sp": should_sp, "hours": should_hours, "task_count": len(self.MOSCOW_TASKS["SHOULD_HAVE"])},
            "could_have": {"sp": could_sp, "hours": could_hours, "task_count": len(self.MOSCOW_TASKS["COULD_HAVE"])},
            "wont_have_count": len(self.MOSCOW_TASKS["WONT_HAVE"]),
            "committed_hours": committed_hours,
            "buffer_hours": buffer_hours,
            "capacity_load_pct": round(load_pct, 1)
        }


def run_and_save_sprint_board(output_dir: str = None) -> Dict[str, Any]:
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(__file__))

    dataset_path = os.path.join(output_dir, "eval_dataset_30.json")
    auditor = EvalDatasetAuditor(dataset_path)
    is_valid, errors = auditor.validate_schema()
    if not is_valid:
        raise ValueError(f"Eval dataset validation failed: {errors}")

    eval_stats = auditor.get_summary_statistics()
    board_mgr = SprintBoardManager()
    sprint_metrics = board_mgr.compute_sprint_metrics()

    combined_telemetry = {
        "timestamp": "2026-10-08T18:00:00Z",
        "eval_dataset_statistics": eval_stats,
        "sprint_planning_metrics": sprint_metrics,
        "moscow_tasks": board_mgr.MOSCOW_TASKS
    }

    out_file = os.path.join(output_dir, "SPRINT_BOARD_DATA.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(combined_telemetry, f, indent=2)

    return combined_telemetry


if __name__ == "__main__":
    data = run_and_save_sprint_board()
    print("=" * 80)
    print(" DAY 16 - SESSION 4: SPRINT PLANNING & EVAL SET VALIDATOR")
    print("=" * 80)
    stats = data["eval_dataset_statistics"]
    print(f"Total Pre-Code Eval Cases: {stats['total_cases']}")
    for cat, count in stats["categories"].items():
        print(f"  • {cat:<24}: {count:>2} cases ({count/stats['total_cases']*100:>4.1f}%)")

    metrics = data["sprint_planning_metrics"]
    print("-" * 80)
    print(f"Sprint Capacity: {metrics['capacity_hours']} hrs | Committed: {metrics['committed_hours']} hrs ({metrics['capacity_load_pct']}%)")
    print(f"  • Must Have  : {metrics['must_have']['task_count']} tasks ({metrics['must_have']['sp']} SP, {metrics['must_have']['hours']} hrs)")
    print(f"  • Should Have: {metrics['should_have']['task_count']} tasks ({metrics['should_have']['sp']} SP, {metrics['should_have']['hours']} hrs)")
    print(f"  • Could Have : {metrics['could_have']['task_count']} tasks ({metrics['could_have']['sp']} SP, {metrics['could_have']['hours']} hrs)")
    print(f"  • Won't Have : {metrics['wont_have_count']} explicit cuts")
    print("=" * 80)
    print("[*] Sprint planning data saved to SPRINT_BOARD_DATA.json")
