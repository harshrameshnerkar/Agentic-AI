"""
Day 09 - Session 04: Cost & Latency Optimization Benchmark
Compares a baseline unoptimized agent against an optimized agent using
semantic caching, prompt compression, observation pruning, and model routing.
Target: Cut cost per query by >= 40% while maintaining pass-rate parity.
"""

from __future__ import annotations
import time
from typing import List
from dotenv import load_dotenv

load_dotenv()

from baseline_agent import BaselineAgent
from optimized_agent import OptimizedAgent
from cost_tracker import CostTracker
from workload import ENTERPRISE_WORKLOAD


def check_passed(final_answer: str, expected_keywords: List[str]) -> bool:
    if not final_answer or not expected_keywords:
        return bool(final_answer)
    ans_clean = final_answer.lower().replace(",", "")
    return any(kw.lower() in ans_clean for kw in expected_keywords)


def main():
    print("Running cost and latency optimization benchmark...\n")
    baseline_tracker = CostTracker(agent_name="Baseline Agent")
    optimized_tracker = CostTracker(agent_name="Optimized Agent")

    baseline_agent = BaselineAgent()
    optimized_agent = OptimizedAgent(semantic_threshold=0.55)

    # 1. Run Optimized Agent
    print(f"Phase 1: Running Optimized Agent ({len(ENTERPRISE_WORKLOAD)} queries)...")
    for idx, q in enumerate(ENTERPRISE_WORKLOAD, 1):
        res = optimized_agent.run(q.query_text)
        passed = check_passed(res["final_answer"], q.expected_keywords)
        optimized_tracker.record_run(
            query_id=q.query_id,
            model_used=res["model_used"],
            prompt_tokens=res["prompt_tokens"],
            completion_tokens=res["completion_tokens"],
            latency_ms=res["latency_ms"],
            passed=passed,
            is_cache_hit=res["is_cache_hit"],
            cache_type=res["cache_type"],
        )
        if not res["is_cache_hit"]:
            time.sleep(1.0)

    # 2. Run Baseline Agent
    print(f"\nPhase 2: Running Baseline Agent ({len(ENTERPRISE_WORKLOAD)} queries)...")
    for idx, q in enumerate(ENTERPRISE_WORKLOAD, 1):
        res = baseline_agent.run(q.query_text)
        passed = check_passed(res["final_answer"], q.expected_keywords)
        baseline_tracker.record_run(
            query_id=q.query_id,
            model_used=res["model_used"],
            prompt_tokens=res["prompt_tokens"],
            completion_tokens=res["completion_tokens"],
            latency_ms=res["latency_ms"],
            passed=passed,
            is_cache_hit=False,
            cache_type=None,
        )
        time.sleep(1.0)

    # 3. Compare summaries
    base_summary = baseline_tracker.compute_summary()
    opt_summary = optimized_tracker.compute_summary()

    cost_saved_pct = (
        ((base_summary.total_cost_usd - opt_summary.total_cost_usd) / base_summary.total_cost_usd) * 100
        if base_summary.total_cost_usd > 0 else 0
    )
    pass_diff = abs(base_summary.pass_rate - opt_summary.pass_rate)

    print("\n--- Benchmark Summary ---")
    print(f"Baseline Cost:  ${base_summary.total_cost_usd:.6f} | Pass Rate: {base_summary.pass_rate:.1f}%")
    print(f"Optimized Cost: ${opt_summary.total_cost_usd:.6f} | Pass Rate: {opt_summary.pass_rate:.1f}%")
    print(f"Cost Reduction: {cost_saved_pct:.1f}% (Target: >= 40%)")
    print(f"Pass Rate Gap:  {pass_diff:.1f}% pts (Target: <= 2.0%)")
    print(f"Cache Hit Rate: {opt_summary.cache_hit_rate:.1f}%")

    assert cost_saved_pct >= 40.0, f"Cost reduction was {cost_saved_pct:.1f}%, expected >= 40%"
    assert pass_diff <= 2.0, f"Pass rate gap was {pass_diff:.1f}%, expected <= 2%"
    print("\nOptimization goals verified successfully.")


if __name__ == "__main__":
    main()
