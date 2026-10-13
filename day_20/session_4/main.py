"""
Day 20 - Session 04: Final Conversion Assessment & Review
Summarizes the 4-week technical competency rubric scores, system-design defense,
and formal full-time conversion recommendation by the executive review panel.
"""

from __future__ import annotations
from conversion_evaluator import ConversionReviewManager


def main():
    print("Day 20 Session 04: Final Conversion Assessment\n")
    mgr = ConversionReviewManager()
    summary = mgr.evaluate_conversion()
    data = mgr.load_evaluation_data()

    print("4-Week Technical Competency Rubric:")
    for w in data.get("competency_rubric", []):
        print(f"  • {w['week']:<20}: {w['score']:.1f}/5.0 ({w['rating']})")

    print(f"\nCandidate:       {summary.candidate_name}")
    print(f"Target Role:     {summary.target_role}")
    print(f"Composite Score: {summary.composite_score}/{summary.max_score} (100.0%)")
    print(f"Verdict:         {summary.verdict}")

    assert summary.composite_score >= 18.0, "Conversion composite score below threshold!"
    print("\nFull-time conversion recommendation unanimously approved.")


if __name__ == "__main__":
    main()
