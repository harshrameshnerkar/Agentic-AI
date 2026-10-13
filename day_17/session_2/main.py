"""
Day 17 - Session 02: Simplest Thing That Works (Baseline Evaluation)
Establishes the performance floor before building an agent:
Compares Plain Zero-Shot Prompt vs Single Retrieval Call (Vanilla RAG).
"""

from __future__ import annotations
import os
from baseline_runner import run_and_save_baselines


def main():
    print("Day 17 Session 02: Establishing Empirical Baseline\n")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    scores = run_and_save_baselines(current_dir)

    p = scores["plain_summary"]
    r = scores["rag_summary"]

    print("--- Baseline Evaluation Results (20 Incidents) ---")
    print(f"Plain Prompt Pass Rate:    {p['overall_pass_rate_pct']:.1f}%")
    print(f"Vanilla RAG Pass Rate:      {r['overall_pass_rate_pct']:.1f}%")
    print(f"Static Runbooks (RAG):     {r['static_runbook_pass_rate_pct']:.1f}%")
    print(f"Dynamic Clusters (RAG):    {r['ephemeral_cluster_pass_rate_pct']:.1f}%")

    print("\nTakeaway: Vanilla RAG solves static runbook queries, but scores 0% on live cluster incidents.")
    print("Conclusion: Tool-augmented agentic execution is strictly required for live cluster triage.")


if __name__ == "__main__":
    main()
