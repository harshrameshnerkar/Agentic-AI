"""
Day 12 - Session 01: When to Fine-Tune (Decision Memo & Cost Model)
Demonstrates the 8-dimension architectural decision framework and
Total Cost of Ownership (TCO) calculator comparing In-Context RAG vs Fine-Tuning.
"""

from __future__ import annotations
from cost_model import cost_model
from decision_framework import decision_framework


def main():
    print("Day 12 Session 01: Fine-Tuning vs In-Context RAG Decision Framework\n")

    # 1. 8-Dimension Architectural Assessment
    res = decision_framework.evaluate_capstone()
    print(f"Target System:  {res.project_name}")
    print(f"Recommendation: {res.overall_recommendation}")
    print(f"Fit Scores:     In-Context RAG = {res.total_prompt_rag_score}% | Fine-Tuning = {res.total_fine_tune_score}%")

    # 2. Total Cost of Ownership (TCO) at 50,000 queries/month
    volume = 50_000
    tco = cost_model.calculate_tco(monthly_volume=volume)

    print(f"\nTCO Comparison at {volume:,} queries/month:")
    print(f"  • Current In-Context RAG:   ${tco.rag_monthly_cost_usd:.2f}/mo (Upfront: $0)")
    print(f"  • Cloud Managed Fine-Tune:  ${tco.cloud_ft_monthly_cost_usd:.2f}/mo (Upfront: ${tco.cloud_ft_upfront_usd:,.0f})")
    print(f"  • Self-Hosted Fine-Tune:    ${tco.self_hosted_monthly_cost_usd:.2f}/mo (Upfront: ${tco.self_hosted_upfront_usd:,.0f})")

    print("\nCore Conclusion: Fine-tune for static behavior/format; use RAG for dynamic facts & knowledge.")


if __name__ == "__main__":
    main()
