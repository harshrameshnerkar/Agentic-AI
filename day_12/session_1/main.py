"""
Day 12 - Session 1: When to Fine-Tune (Decision Memo & Economic Evaluation)
===========================================================================
Interactive CLI Workspace:
  1. Executive Decision Memo Summary (RFC-2026-042)
  2. 8-Dimension Architectural Assessment of OpsSentinel AI
  3. Total Cost of Ownership (TCO) & Breakeven Calculator
  4. Volume Scaling & Sensitivity Curves (10k to 5M queries)
  5. The "Exhaust Prompting First" Pedagogical Walkthrough
"""

import sys
import os
from cost_model import cost_model
from decision_framework import decision_framework


def print_banner(title: str):
    print("\n" + "=" * 95)
    print(f" {title.center(93)} ")
    print("=" * 95)


def show_memo_summary():
    print_banner("EXECUTIVE DECISION MEMO: RFC-2026-042")
    print("""
TARGET SYSTEM: OpsSentinel AI (Autonomous SRE & Incident Response Copilot)
DOCUMENT ID  : RFC-2026-042 | Lead AI Systems Architect
STATUS       : REJECTED FOR PHASE 1-2; APPROVED FOR IN-CONTEXT RAG + CONTEXT CACHING

THE VERDICT:
  DO NOT FINE-TUNE THE MODEL AT THIS STAGE.
  We strongly recommend exhausting In-Context RAG, Prompt Caching, and Guardrails.
  Fine-tuning introduces severe operational risks, unacceptable retraining latencies,
  an unjustified $14,500+ upfront engineering investment, and a $730+/month infrastructure
  maintenance burden, with ZERO measurable gain over our current 100% benchmark pass rate.

KEY METRIC COMPARISON (At 50,000 operations/month):
  - In-Context RAG (Current)    : $3.06 / month  | Upfront: $0      | Pass Rate: 100% (20/20)
  - Cloud Managed Fine-Tuning   : $20.40 / month | Upfront: $14,525 | High risk of hallucination
  - Dedicated Self-Hosted SLM   : $734.00 / month| Upfront: $14,525 | 240x more expensive than RAG

THE CORE AXIOM:
  "Fine-Tune for Behaviour & Format, RAG for Knowledge."
  SRE runbooks, active tickets, and telemetry databases change continuously.
  Knowledge baked into model weights at training time decays immediately,
  risking catastrophic hallucination during critical production outages.
""")


def run_assessment():
    print_banner("8-DIMENSION ARCHITECTURAL DECISION FRAMEWORK")
    res = decision_framework.evaluate_capstone()

    print(f"Target System   : {res.project_name}")
    print(f"Recommendation  : {res.overall_recommendation}")
    print(f"Confidence      : {res.recommendation_confidence}")
    print(f"Fit Scores      : In-Context RAG: {res.total_prompt_rag_score}%  |  Fine-Tuning: {res.total_fine_tune_score}%\n")

    print("-" * 95)
    print(f"| Dimension                    | Weight | RAG Fit | FT Fit | Operational Assessment Notes        |")
    print("-" * 95)
    for d in res.dimension_breakdown:
        print(f"| {d.name:<28} | {d.weight:>6.1f} | {d.prompt_rag_score:>5.1f}  | {d.fine_tune_score:>5.1f}  | {d.assessment_notes[:35]:<35} |")
    print("-" * 95)

    print("\n[EXECUTIVE JUSTIFICATION]:")
    print(f"  {res.executive_justification}\n")

    print("[CRITICAL RISK REGISTER IF FINE-TUNING WERE ADOPTED]:")
    for r in res.risk_register:
        print(f"  * {r}")

    print("\n[PHASE 3 EXIT CRITERIA / RE-EVALUATION GATES]:")
    for g in res.phase_gates:
        print(f"  * {g}")
    print("-" * 95)


def run_tco_calculator():
    print_banner("TOTAL COST OF OWNERSHIP (TCO) & FINANCIAL ANALYSIS")

    upfront = cost_model.upfront
    print("1. UPFRONT CAPITAL EXPENDITURE BREAKDOWN (ONE-TIME SETUP):")
    print(f"   - Dataset Curation (50 SRE hrs @ $125/hr)        : ${upfront.total_curation_cost:>9.2f}")
    print(f"   - Synthetic Data & LLM API Generation Costs      : ${upfront.synthetic_data_api_cost:>9.2f}")
    print(f"   - Expert QA Review & Human Labeling (20 hrs)     : ${upfront.total_qa_cost:>9.2f}")
    print(f"   - Training Compute (48 hrs on 8x A100 GPU node)  : ${upfront.total_compute_cost:>9.2f}")
    print(f"   - Evaluation Harness & Regression Suite Setup    : ${upfront.total_eval_harness_cost:>9.2f}")
    print(f"   - Tool Calling & Guardrail Integration Testing   : ${upfront.total_integration_cost:>9.2f}")
    print(f"   --------------------------------------------------------------")
    print(f"   TOTAL UPFRONT CAPITAL INVESTMENT                 : ${upfront.total_upfront_cost:>9.2f}")
    print(f"   (vs In-Context RAG Upfront Cost                  : $     0.00 - Already Built)\n")

    print("2. 12-MONTH TCO COMPARISON ACROSS VOLUME MILESTONES:")
    rows = cost_model.generate_tco_comparison()
    print("-" * 95)
    print(f"| Monthly Volume | RAG Monthly | Managed FT Mo | Self-Hosted Mo | RAG 12m TCO | Self-Hosted 12m TCO |")
    print("-" * 95)
    for r in rows:
        print(f"| {r['monthly_volume']:>14,d} | ${r['rag_monthly_cost']:>10.2f} | ${r['managed_ft_monthly_cost']:>12.2f} | ${r['self_hosted_monthly_cost']:>13.2f} | ${r['rag_12m_tco']:>10.2f} | ${r['self_hosted_12m_tco']:>18.2f} |")
    print("-" * 95)

    print("\n3. BREAKEVEN ANALYSIS:")
    be = cost_model.calculate_breakeven_volume()
    print(f"   - Unit RAG Cost per Query  : ${be['unit_rag_cost_per_query']:.6f} / query")
    print(f"   - Single GPU Monthly Cost  : ${cost_model.self_hosted_gpu_monthly:.2f} / month")
    print(f"   - Breakeven Query Volume   : {be['pure_monthly_opex_breakeven_volume']:,} queries / month")
    print(f"   - GPU Hardware Limit       : {be['single_gpu_capacity_limit']:,} queries / month max")
    print(f"\n   CONCLUSION: {be['conclusion']}")
    print("-" * 95)


def run_scaling_curves():
    print_banner("VOLUME SCALING & SENSITIVITY CURVES")
    print("Comparing monthly operational spend as volume scales from 10k to 5,000,000 operations:\n")

    test_vols = [10000, 25000, 50000, 100000, 250000, 500000, 1000000, 2500000, 5000000]
    print(f"| Monthly Operations | In-Context RAG + Cache | Cloud Managed FT | Dedicated Self-Hosted GPU | Advantage of RAG |")
    print("-" * 95)
    for v in test_vols:
        c_rag = cost_model.compute_rag_monthly_cost(v)
        c_mft = cost_model.compute_managed_ft_monthly_cost(v)
        c_gpu = cost_model.compute_self_hosted_monthly_cost(v)
        ratio = c_gpu / max(0.01, c_rag)
        print(f"| {v:>18,d} | ${c_rag:>21.2f} | ${c_mft:>15.2f} | ${c_gpu:>24.2f} | {ratio:>13.1f}x cheaper |")
    print("-" * 95)
    print("""
TAKEAWAYS:
1. Serverless In-Context RAG scales linearly and ultra-efficiently ($0.0612 per 1k operations).
2. Dedicated GPU hosting imposes a massive $734/mo step-function fixed cost that makes no sense
   at low-to-medium enterprise volumes.
3. Even at 1,000,000 queries/month, RAG costs only $61.18 vs $1,468 for GPU infrastructure!
""")


def run_exhaust_prompting_walkthrough():
    print_banner("WHY TEAMS MUST EXHAUST PROMPTING FIRST")
    print("""
THE 5-LEVEL IN-CONTEXT MATURITY LADDER:

[LEVEL 1] Zero-Shot System Instructions
  - Establish persona, guardrails, and role boundaries.
  - Takes 5 minutes to draft and test.

[LEVEL 2] Few-Shot In-Context Demonstrations
  - Supply 2-3 canonical input-output examples demonstrating edge-case reasoning.
  - Improves accuracy by 20-30% without changing model weights.

[LEVEL 3] Context Engineering & Schema Isolation (Proven Day 11 Session 4)
  - Dynamically prune unneeded tool schemas (857 tok -> 86-237 tok, 60-90% cut).
  - Compact multi-turn history into dense state tuples (600 tok -> 50 tok, 91% cut).
  - Distill raw log dumps to extract error signatures only.
  - Result: 62.4% context token cut with ZERO loss in accuracy.

[LEVEL 4] Prompt Caching & Cache-Aware Structuring
  - Place static system instructions and tools at the prompt head.
  - 85%+ cache hit rate delivers 75% cost discounts and 40% faster TTFT.

[LEVEL 5] Deterministic Guardrails & Blast-Radius Access Gates
  - Enforce role-based access control (RBAC) and SQL injection checks in code.
  - Guaranteed 100% deterministic safety at 0 token overhead.

WHY THIS MATTERS:
By exhausting Levels 1 through 5 on OpsSentinel AI, we achieved:
  - 100.0% Pass Rate across all 20 Capstone test cases.
  - $0.0612 cost per 1,000 queries.
  - 450 ms p95 response latency.

Fine-tuning cannot improve a 100% pass rate, but it DOES add $14,500+ in setup costs,
retraining latency, and model drift debt.
Exhaust prompting and RAG first; fine-tune only when mathematically justified!
""")


def interactive_menu():
    while True:
        print_banner("DAY 12 - SESSION 1: WHEN TO FINE-TUNE")
        print(" [1] View Executive Decision Memo Summary (RFC-2026-042)")
        print(" [2] Run 8-Dimension Decision Framework Assessment on Capstone")
        print(" [3] Run Total Cost of Ownership (TCO) & Breakeven Calculator")
        print(" [4] View Volume Sensitivity & Scaling Curves (10k to 5M queries)")
        print(" [5] Pedagogical Walkthrough: Why Teams Must Exhaust Prompting First")
        print(" [0] Exit")
        print("=" * 95)

        choice = input("Select an option (0-5): ").strip()
        if choice == "1":
            show_memo_summary()
        elif choice == "2":
            run_assessment()
        elif choice == "3":
            run_tco_calculator()
        elif choice == "4":
            run_scaling_curves()
        elif choice == "5":
            run_exhaust_prompting_walkthrough()
        elif choice == "0":
            print("\nExiting Day 12 Session 1 Decision Memo Workspace. Goodbye!\n")
            break
        else:
            print("[!] Invalid option. Please enter 0-5.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--memo":
        show_memo_summary()
    elif len(sys.argv) > 1 and sys.argv[1] == "--tco":
        run_tco_calculator()
    elif len(sys.argv) > 1 and sys.argv[1] == "--assess":
        run_assessment()
    else:
        interactive_menu()
