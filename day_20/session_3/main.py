"""CLI Entry Point for Day 20 Session 3: Engineering Sprint Retrospective.

Usage:
    python main.py --summary
    python main.py --variance
    python main.py --mistakes
    python main.py --action-items
"""

import argparse
import json
import os
import sys

from retro_analyzer import SprintRetrospectiveManager


def print_banner() -> None:
    print("=" * 85)
    print("    OPS-SENTINEL AI ENTERPRISE — DAY 20 S3: ENGINEERING RETROSPECTIVE")
    print("=" * 85)


def display_variance(mgr: SprintRetrospectiveManager) -> None:
    data = mgr.load_retro_data()
    print_banner()
    print("SPARK BOARD ESTIMATE VARIANCE ANALYSIS:\n")
    print(f"{'Task ID':<10} | {'Task Name':<32} | {'Est':<6} | {'Act':<6} | {'Var %':<8} | {'Root Cause'}")
    print("-" * 85)
    for t in data.get("sprint_variance", []):
        print(f"{t['task_id']:<10} | {t['task_name']:<32} | {t['estimated_hours']:<6.1f} | {t['actual_hours']:<6.1f} | {t['variance_pct']:<7.1f}% | {t['cause'][:20]}...")
    print("=" * 85)


def display_mistakes(mgr: SprintRetrospectiveManager) -> None:
    mistakes = mgr.get_mistakes()
    print_banner()
    print(f"3 SPECIFIC TECHNICAL MISTAKES & THEIR CONCRETE LESSONS ({len(mistakes)} Items):\n")
    for m in mistakes:
        print(f"  • [{m['id']}] {m['title']}")
        print(f"    Context : {m['context']}")
        print(f"    Mistake : {m['what_happened']}")
        print(f"    Lesson  : {m['technical_lesson']}\n")
    print("=" * 85)


def display_action_items(mgr: SprintRetrospectiveManager) -> None:
    data = mgr.load_retro_data()
    print_banner()
    print("CONTINUOUS IMPROVEMENT ACTION ITEMS FOR NEXT SPRINT:\n")
    for idx, act in enumerate(data.get("action_items_next_sprint", []), 1):
        print(f"  {idx}. [✓] {act}")
    print("=" * 85)


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 20 Session 3 Retrospective CLI")
    parser.add_argument("--summary", action="store_true", help="Display retrospective summary")
    parser.add_argument("--variance", action="store_true", help="Display sprint variance table")
    parser.add_argument("--mistakes", action="store_true", help="Display 3 technical mistakes & lessons")
    parser.add_argument("--action-items", action="store_true", help="Display action items for next sprint")

    args = parser.parse_args()
    mgr = SprintRetrospectiveManager()

    if args.variance:
        display_variance(mgr)
    elif args.mistakes:
        display_mistakes(mgr)
    elif args.action_items:
        display_action_items(mgr)
    else:
        # Default: show variance, mistakes, and action items
        display_variance(mgr)
        print("\n")
        display_mistakes(mgr)
        print("\n")
        display_action_items(mgr)


if __name__ == "__main__":
    main()
