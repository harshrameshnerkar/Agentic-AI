"""
Day 18 - Session 1: Standup & Replan
Sprint Replan Manager: Manages honest re-estimation, tracks deliberate scope cuts (Must -> Could),
and audits team capacity allocation.
"""

import os
import sys
import json
from typing import Dict, Any, List

# Set UTF-8 encoding for Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


class SprintReplanManager:
    """Computes before-and-after capacity metrics following a deliberate scope cut."""

    SPRINT_2_CAPACITY_HOURS = 16.0

    INITIAL_TASKS = [
        {"id": "TASK-2.1", "name": "REST Delivery Surface & Universal CLI", "category": "MUST_HAVE", "sp": 5, "hours": 4.0},
        {"id": "TASK-2.2", "name": "PII Redaction & Security Guardrails", "category": "MUST_HAVE", "sp": 3, "hours": 3.0},
        {"id": "TASK-2.3", "name": "HMAC-SHA256 Cryptographic HITL Gate", "category": "MUST_HAVE", "sp": 5, "hours": 4.0},
        {"id": "TASK-2.4", "name": "Bidirectional Slack/Teams Bot", "category": "MUST_HAVE", "sp": 5, "hours": 4.5},
        {"id": "TASK-2.5", "name": "Automated CI Regression Test Gate", "category": "MUST_HAVE", "sp": 3, "hours": 2.5},
        {"id": "TASK-2.6", "name": "Redis Cluster State Cache (30s TTL)", "category": "SHOULD_HAVE", "sp": 3, "hours": 2.5},
        {"id": "TASK-2.7", "name": "SHA-256 Merkle Audit Log Chain", "category": "SHOULD_HAVE", "sp": 2, "hours": 2.0},
        {"id": "TASK-2.8", "name": "Auto-Generated Markdown Postmortem", "category": "COULD_HAVE", "sp": 3, "hours": 2.5}
    ]

    SCOPE_CUTS = [
        {
            "task_id": "TASK-2.4",
            "task_name": "Bidirectional Slack/Teams Bot",
            "from_category": "MUST_HAVE",
            "to_category": "COULD_HAVE",
            "story_points": 5,
            "hours": 4.5,
            "reason": "Cutting scope deliberately rather than silently missing it. Protects 16h capacity for HMAC cryptographic safety and automated regression testing.",
            "approver": "Dr. Elena Rostova (Mentor)"
        }
    ]

    def compute_replan_metrics(self) -> Dict[str, Any]:
        # Pre-replan Must-Have hours
        pre_must_hours = sum(t["hours"] for t in self.INITIAL_TASKS if t["category"] == "MUST_HAVE")
        pre_must_sp = sum(t["sp"] for t in self.INITIAL_TASKS if t["category"] == "MUST_HAVE")

        # Post-replan task map
        post_tasks = []
        for t in self.INITIAL_TASKS:
            task_copy = dict(t)
            for cut in self.SCOPE_CUTS:
                if t["id"] == cut["task_id"]:
                    task_copy["category"] = cut["to_category"]
                    task_copy["is_cut"] = True
            post_tasks.append(task_copy)

        post_must_hours = sum(t["hours"] for t in post_tasks if t["category"] == "MUST_HAVE")
        post_must_sp = sum(t["sp"] for t in post_tasks if t["category"] == "MUST_HAVE")
        post_should_hours = sum(t["hours"] for t in post_tasks if t["category"] == "SHOULD_HAVE")
        post_could_hours = sum(t["hours"] for t in post_tasks if t["category"] == "COULD_HAVE")

        hours_freed = pre_must_hours - post_must_hours
        buffer_hours = self.SPRINT_2_CAPACITY_HOURS - post_must_hours
        capacity_load_pct = (post_must_hours / self.SPRINT_2_CAPACITY_HOURS) * 100

        return {
            "capacity_hours": self.SPRINT_2_CAPACITY_HOURS,
            "pre_replan": {
                "must_hours": pre_must_hours,
                "must_sp": pre_must_sp,
                "deficit_hours": max(0.0, pre_must_hours - self.SPRINT_2_CAPACITY_HOURS),
                "is_over_capacity": pre_must_hours > self.SPRINT_2_CAPACITY_HOURS
            },
            "post_replan": {
                "must_hours": post_must_hours,
                "must_sp": post_must_sp,
                "should_hours": post_should_hours,
                "could_hours": post_could_hours,
                "buffer_hours": buffer_hours,
                "capacity_load_pct": round(capacity_load_pct, 1),
                "is_over_capacity": post_must_hours > self.SPRINT_2_CAPACITY_HOURS
            },
            "hours_freed": hours_freed,
            "scope_cuts": self.SCOPE_CUTS,
            "tasks": post_tasks
        }


def run_and_save_replan(output_dir: str = None) -> Dict[str, Any]:
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(__file__))

    mgr = SprintReplanManager()
    metrics = mgr.compute_replan_metrics()

    out_file = os.path.join(output_dir, "REPLAN_DATA.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    return metrics


if __name__ == "__main__":
    data = run_and_save_replan()
    print("=" * 80)
    print(" DAY 18 - SESSION 1: SPRINT 2 REPLAN & SCOPE DECISION AUDITOR")
    print("=" * 80)
    pre = data["pre_replan"]
    post = data["post_replan"]
    print(f"Total Available Capacity : {data['capacity_hours']} hrs")
    print(f"Pre-Replan Must-Have Load: {pre['must_hours']} hrs ({pre['must_sp']} SP) --> Deficit: +{pre['deficit_hours']} hrs (OVER CAPACITY)")
    print(f"Post-Replan Must-Have Load: {post['must_hours']} hrs ({post['must_sp']} SP) --> Buffer: {post['buffer_hours']} hrs ({post['capacity_load_pct']}% load)")
    print(f"Hours Freed via Scope Cut: {data['hours_freed']} hrs")
    print("-" * 80)
    print("DOCUMENTED SCOPE CUT:")
    for cut in data["scope_cuts"]:
        print(f"  • [{cut['task_id']}] {cut['task_name']} moved from {cut['from_category']} to {cut['to_category']}")
        print(f"    Reason: {cut['reason']}")
        print(f"    Sign-off: {cut['approver']}")
    print("=" * 80)
    print("[*] Replan audit saved to REPLAN_DATA.json")
