"""
Day 20 - Session 03: Engineering Sprint Retrospective
Reviews sprint estimation variance, analyzes the 3 technical mistakes,
and establishes actionable continuous improvement items for future sprints.
"""

from __future__ import annotations
from retro_analyzer import SprintRetrospectiveManager


def main():
    print("Day 20 Session 03: Engineering Sprint Retrospective\n")
    mgr = SprintRetrospectiveManager()
    data = mgr.load_retro_data()

    print("Sprint Variance Summary:")
    for t in data.get("sprint_variance", []):
        print(f"  • {t['task_id']} ({t['task_name']:<30}): Est={t['estimated_hours']}h, Act={t['actual_hours']}h ({t['variance_pct']:+.1f}%)")

    mistakes = mgr.get_mistakes()
    print(f"\nDocumented Technical Mistakes & Lessons ({len(mistakes)} items):")
    for m in mistakes:
        print(f"  • [{m['id']}] {m['title']}: {m['technical_lesson']}")

    actions = data.get("action_items_next_sprint", [])
    print(f"\nNext Sprint Action Items: {len(actions)} committed items.")


if __name__ == "__main__":
    main()
