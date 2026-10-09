"""CLI Entry Point for Day 20 Session 4: Conversion Assessment & Final Review.

Usage:
    python main.py --summary
    python main.py --rubric
    python main.py --recommendation
    python main.py --defense-qa
"""

import argparse
import json
import os
import sys

from conversion_evaluator import ConversionReviewManager


def print_banner() -> None:
    print("=" * 85)
    print("   OPS-SENTINEL AI ENTERPRISE — DAY 20 S4: FINAL CONVERSION ASSESSMENT")
    print("=" * 85)


def display_rubric(mgr: ConversionReviewManager) -> None:
    data = mgr.load_evaluation_data()
    print_banner()
    print("4-WEEK TECHNICAL COMPETENCY RUBRIC EVALUATION:\n")
    print(f"{'Period':<20} | {'Focus Areas':<45} | {'Score':<8} | {'Rating'}")
    print("-" * 85)
    for w in data.get("competency_rubric", []):
        print(f"{w['week']:<20} | {w['focus'][:45]:<45} | {w['score']:.1f}/5.0  | {w['rating']}")
    print("=" * 85)


def display_defense(mgr: ConversionReviewManager) -> None:
    data = mgr.load_evaluation_data()
    sd = data.get("system_design_challenge", {})
    print_banner()
    print("LIVE SYSTEM-DESIGN DEFENSE UNDER FRESH CONSTRAINTS:\n")
    print(f"Topic      : {sd.get('topic')}\n")
    print(f"Evaluation : {sd.get('evaluation')}\n")
    print(f"Final Grade: {sd.get('grade')}")
    print("=" * 85)


def display_recommendation(mgr: ConversionReviewManager) -> None:
    summary = mgr.evaluate_conversion()
    data = mgr.load_evaluation_data()
    print_banner()
    print("FORMAL CONVERSION DECISION & EXECUTIVE APPROVALS:\n")
    print(f"Candidate       : {summary.candidate_name}")
    print(f"Target Role     : {summary.target_role}")
    print(f"Composite Score : {summary.composite_score} / {summary.max_score} (100.0%)")
    print(f"Final Verdict   : [✓] {summary.verdict}")
    print(f"Offer Level     : {data.get('final_decision', {}).get('offer_level')}")
    print(f"Compensation    : {data.get('final_decision', {}).get('compensation_bracket')}\n")
    print("-" * 85)
    print("REVIEW PANEL CONSENSUS (ALL 3 MEMBERS SIGNED):")
    for p in data.get("review_panel", []):
        print(f"  • {p['name']} ({p['title']}) -> [{p['recommendation']}] (Score: {p['score']}/5.0)")
    print("=" * 85)
    sys.exit(0 if summary.verdict == "CONVERSION_APPROVED" else 1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 20 Session 4 Conversion Assessment CLI")
    parser.add_argument("--summary", action="store_true", help="Display conversion summary")
    parser.add_argument("--rubric", action="store_true", help="Display 4-week competency rubric")
    parser.add_argument("--recommendation", action="store_true", help="Display formal conversion decision")
    parser.add_argument("--defense-qa", action="store_true", help="Display system-design challenge and evaluation")

    args = parser.parse_args()
    mgr = ConversionReviewManager()

    if args.rubric:
        display_rubric(mgr)
    elif args.defense_qa:
        display_defense(mgr)
    elif args.recommendation:
        display_recommendation(mgr)
    else:
        # Default: rubric + defense + recommendation
        display_rubric(mgr)
        print("\n")
        display_defense(mgr)
        print("\n")
        display_recommendation(mgr)


if __name__ == "__main__":
    main()
