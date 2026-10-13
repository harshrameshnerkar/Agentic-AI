"""
Day 18 - Session 1: Standup & Replan
Sprint Replan Manager: Tracks re-estimation and deliberate scope cuts.
"""

import json
import os
from typing import Any, Dict


class SprintReplanManager:
    SPRINT_2_CAPACITY_HOURS = 16.0

    INITIAL_TASKS = [
        {"id": "TASK-2.1", "name": "REST Delivery Surface & Universal CLI", "category": "MUST_HAVE", "sp": 5, "hours": 4.0},
        {"id": "TASK-2.2", "name": "PII Redaction & Security Guardrails", "category": "MUST_HAVE", "sp": 3, "hours": 3.0},
        {"id": "TASK-2.3", "name": "HMAC-SHA256 Cryptographic HITL Gate", "category": "MUST_HAVE", "sp": 5, "hours": 4.0},
        {"id": "TASK-2.4", "name": "Bidirectional Slack/Teams Bot", "category": "MUST_HAVE", "sp": 5, "hours": 4.5},
        {"id": "TASK-2.5", "name": "Automated CI Regression Test Gate", "category": "MUST_HAVE", "sp": 3, "hours": 2.5},
        {"id": "TASK-2.6", "name": "Redis Cluster State Cache (30s TTL)", "category": "SHOULD_HAVE", "sp": 3, "hours": 2.5},
        {"id": "TASK-2.7", "name": "SHA-256 Merkle Audit Log Chain", "category": "SHOULD_HAVE", "sp": 2, "hours": 2.0},
        {"id": "TASK-2.8", "name": "Auto-Generated Markdown Postmortem", "category": "COULD_HAVE", "sp": 3, "hours": 2.5},
    ]

    SCOPE_CUTS = [
        {
            "task_id": "TASK-2.4",
            "task_name": "Bidirectional Slack/Teams Bot",
            "from_category": "MUST_HAVE",
            "to_category": "COULD_HAVE",
            "story_points": 5,
            "hours": 4.5,
            "reason": "Cutting scope to protect 16h capacity for cryptographic safety and regression testing.",
            "approver": "Dr. Elena Rostova (Mentor)",
        }
    ]

    def compute_replan_metrics(self) -> Dict[str, Any]:
        pre_must_hours = sum(t["hours"] for t in self.INITIAL_TASKS if t["category"] == "MUST_HAVE")
        pre_must_sp = sum(t["sp"] for t in self.INITIAL_TASKS if t["category"] == "MUST_HAVE")

        post_tasks = []
        for t in self.INITIAL_TASKS:
            copy = dict(t)
            for cut in self.SCOPE_CUTS:
                if t["id"] == cut["task_id"]:
                    copy["category"] = cut["to_category"]
                    copy["is_cut"] = True
            post_tasks.append(copy)

        post_must_hours = sum(t["hours"] for t in post_tasks if t["category"] == "MUST_HAVE")
        post_must_sp = sum(t["sp"] for t in post_tasks if t["category"] == "MUST_HAVE")
        post_should_hours = sum(t["hours"] for t in post_tasks if t["category"] == "SHOULD_HAVE")
        post_could_hours = sum(t["hours"] for t in post_tasks if t["category"] == "COULD_HAVE")

        return {
            "capacity_hours": self.SPRINT_2_CAPACITY_HOURS,
            "pre_replan": {
                "must_hours": pre_must_hours,
                "must_sp": pre_must_sp,
                "deficit_hours": max(0.0, pre_must_hours - self.SPRINT_2_CAPACITY_HOURS),
                "is_over_capacity": pre_must_hours > self.SPRINT_2_CAPACITY_HOURS,
            },
            "post_replan": {
                "must_hours": post_must_hours,
                "must_sp": post_must_sp,
                "should_hours": post_should_hours,
                "could_hours": post_could_hours,
                "buffer_hours": self.SPRINT_2_CAPACITY_HOURS - post_must_hours,
                "capacity_load_pct": round((post_must_hours / self.SPRINT_2_CAPACITY_HOURS) * 100, 1),
                "is_over_capacity": post_must_hours > self.SPRINT_2_CAPACITY_HOURS,
            },
            "hours_freed": pre_must_hours - post_must_hours,
            "scope_cuts": self.SCOPE_CUTS,
            "tasks": post_tasks,
        }


def run_and_save_replan(output_dir: str = None) -> Dict[str, Any]:
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(__file__))
    metrics = SprintReplanManager().compute_replan_metrics()
    with open(os.path.join(output_dir, "REPLAN_DATA.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    return metrics


if __name__ == "__main__":
    run_and_save_replan()
    print("Replan data saved to REPLAN_DATA.json")
