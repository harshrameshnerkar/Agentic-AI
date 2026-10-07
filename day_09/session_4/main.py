"""
Cost & Latency Optimization Benchmark Runner.
Executes head-to-head comparison between:
1. Baseline Agent (Unoptimized: bloated prompt, no caching, raw JSON observations).
2. Cost & Latency Optimized Agent (exact + semantic cache, prompt compression, observation compaction, tiered routing).

Evaluates:
- Cost per query reduction (Target: >= 40% reduction).
- Pass rate parity (Target: within 2 percentage points).
- Latency percentiles: p50 (median) and p95 (tail latency).
"""

import sys
import time
from typing import List, Dict, Any

# Ensure UTF-8 output on Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from baseline_agent import BaselineAgent
from optimized_agent import OptimizedAgent
from cost_tracker import CostTracker, AggregatePerformanceSummary
from workload import ENTERPRISE_WORKLOAD, WorkloadQuery


def check_passed(final_answer: str, expected_keywords: List[str]) -> bool:
    """Verifies that the generated answer contains expected factual keywords."""
    if not final_answer or not expected_keywords:
        return bool(final_answer)
    clean_ans = final_answer.lower().replace(",", "")
    return any(
        kw.lower() in final_answer.lower() or kw.lower().replace(",", "") in clean_ans
        for kw in expected_keywords
    )


def format_table_row(cols: List[str], widths: List[int]) -> str:
    """Formats columns into an ASCII table row."""
    cells = [c[: widths[i]].ljust(widths[i]) for i, c in enumerate(cols)]
    return "| " + " | ".join(cells) + " |"


def main():
    print("=" * 88)
    print(" DAY 9 - SESSION 4: COST & LATENCY OPTIMIZATION BENCHMARK")
    print(" Targets: Cut Cost/Query >= 40% | Keep Pass Rate within 2 percentage points")
    print("=" * 88)

    baseline_tracker = CostTracker(agent_name="Baseline Agent")
    optimized_tracker = CostTracker(agent_name="Optimized Agent")

    baseline_agent = BaselineAgent()
    optimized_agent = OptimizedAgent(semantic_threshold=0.55)

    total_queries = len(ENTERPRISE_WORKLOAD)

    # =======================================================================
    # PART 1: RUNNING OPTIMIZED AGENT (CACHING + COMPRESSION + ROUTING)
    # =======================================================================
    print(f"\n[PHASE 1] Executing Optimized Agent across {total_queries} Enterprise Queries...")
    print("         (Exact Cache + Semantic Cache + Prompt Compression + Tiered Routing)")
    print("-" * 88)

    for idx, q in enumerate(ENTERPRISE_WORKLOAD, 1):
        t0 = time.time()
        res = optimized_agent.run(q.query_text)
        latency_ms = res["latency_ms"]

        is_passed = check_passed(res["final_answer"], q.expected_keywords)
        optimized_tracker.record_run(
            query_id=q.query_id,
            model_used=res["model_used"],
            prompt_tokens=res["prompt_tokens"],
            completion_tokens=res["completion_tokens"],
            latency_ms=latency_ms,
            passed=is_passed,
            is_cache_hit=res["is_cache_hit"],
            cache_type=res["cache_type"],
        )

        status_badge = "[✓ PASS]" if is_passed else "[✗ FAIL]"
        cache_badge = f"[{res['cache_type'].upper()} HIT]" if res["is_cache_hit"] else "[LLM CALL]"
        print(
            f"[{idx:02d}/{total_queries}] {q.query_id} ({q.query_type:<15}): {status_badge} {cache_badge:<14} "
            f"Tokens: {res['total_tokens']:<4} | Latency: {latency_ms:>7.1f}ms | Cost: ${optimized_tracker.metrics[-1].cost_usd:.6f}"
        )

        # Only sleep if an actual LLM call was made (pacing API quotas)
        if not res["is_cache_hit"]:
            time.sleep(2.5)

    # =======================================================================
    # PART 2: RUNNING BASELINE AGENT (UNOPTIMIZED BENCHMARK)
    # =======================================================================
    print("\n" + "=" * 88)
    print(f"[PHASE 2] Executing Baseline Agent across {total_queries} Enterprise Queries...")
    print("         (Bloated Monolithic Prompt + Zero Caching + Uncompressed JSON Obs)")
    print("-" * 88)

    for idx, q in enumerate(ENTERPRISE_WORKLOAD, 1):
        t0 = time.time()
        res = baseline_agent.run(q.query_text)
        latency_ms = res["latency_ms"]

        is_passed = check_passed(res["final_answer"], q.expected_keywords)
        baseline_tracker.record_run(
            query_id=q.query_id,
            model_used=res["model_used"],
            prompt_tokens=res["prompt_tokens"],
            completion_tokens=res["completion_tokens"],
            latency_ms=latency_ms,
            passed=is_passed,
            is_cache_hit=False,
            cache_type=None,
        )

        status_badge = "[✓ PASS]" if is_passed else "[✗ FAIL]"
        print(
            f"[{idx:02d}/{total_queries}] {q.query_id} ({q.query_type:<15}): {status_badge} [NO CACHE]     "
            f"Tokens: {res['total_tokens']:<4} | Latency: {latency_ms:>7.1f}ms | Cost: ${baseline_tracker.metrics[-1].cost_usd:.6f}"
        )
        time.sleep(2.5)

    # =======================================================================
    # PART 3: AGGREGATE STATISTICAL AUDIT & PERCENTILE ANALYSIS
    # =======================================================================
    base_summary = baseline_tracker.compute_summary()
    opt_summary = optimized_tracker.compute_summary()

    cost_reduction_pct = (
        ((base_summary.total_cost_usd - opt_summary.total_cost_usd) / base_summary.total_cost_usd) * 100.0
        if base_summary.total_cost_usd > 0
        else 0.0
    )
    token_reduction_pct = (
        ((base_summary.total_tokens - opt_summary.total_tokens) / base_summary.total_tokens) * 100.0
        if base_summary.total_tokens > 0
        else 0.0
    )
    pass_rate_diff = abs(base_summary.pass_rate - opt_summary.pass_rate)

    print("\n" + "=" * 88)
    print("                 COST & LATENCY PERFORMANCE COMPARISON SCORECARD")
    print("=" * 88)

    headers = ["Performance Metric", "Baseline (Unoptimized)", "Optimized Agent", "Optimization Delta"]
    widths = [26, 22, 20, 22]
    sep = "+-" + "-+-".join(["-" * w for w in widths]) + "-+"

    print(sep)
    print(format_table_row(headers, widths))
    print(sep)

    rows = [
        ["Total Tokens Consumed", f"{base_summary.total_tokens:,}", f"{opt_summary.total_tokens:,}", f"-{token_reduction_pct:.1f}% Tokens"],
        ["Total Dollar Cost (USD)", f"${base_summary.total_cost_usd:.6f}", f"${opt_summary.total_cost_usd:.6f}", f"-{cost_reduction_pct:.1f}% Cost"],
        ["Cost per Query (USD)", f"${base_summary.cost_per_query_usd:.6f}", f"${opt_summary.cost_per_query_usd:.6f}", f"-{cost_reduction_pct:.1f}% Cheaper"],
        ["Task Pass Rate (%)", f"{base_summary.pass_rate:.1f}%", f"{opt_summary.pass_rate:.1f}%", f"Δ {pass_rate_diff:.1f}% pts (Parity)"],
        ["Cache Hit Rate (%)", "0.0% (No Caching)", f"{opt_summary.cache_hit_rate:.1f}% ({opt_summary.cache_hits}/{opt_summary.total_queries})", f"+{opt_summary.cache_hit_rate:.1f}% Cached"],
        ["Median Latency (p50)", f"{base_summary.latency_p50_ms:.1f} ms", f"{opt_summary.latency_p50_ms:.1f} ms", f"{base_summary.latency_p50_ms - opt_summary.latency_p50_ms:+.1f} ms"],
        ["90th Percentile (p90)", f"{base_summary.latency_p90_ms:.1f} ms", f"{opt_summary.latency_p90_ms:.1f} ms", f"{base_summary.latency_p90_ms - opt_summary.latency_p90_ms:+.1f} ms"],
        ["95th Percentile (p95)", f"{base_summary.latency_p95_ms:.1f} ms", f"{opt_summary.latency_p95_ms:.1f} ms", f"{base_summary.latency_p95_ms - opt_summary.latency_p95_ms:+.1f} ms"],
        ["Mean Request Latency", f"{base_summary.latency_mean_ms:.1f} ms", f"{opt_summary.latency_mean_ms:.1f} ms", f"{base_summary.latency_mean_ms - opt_summary.latency_mean_ms:+.1f} ms"],
    ]

    for r in rows:
        print(format_table_row(r, widths))
    print(sep)

    # =======================================================================
    # PART 4: VERIFICATION CRITERIA CHECK
    # =======================================================================
    cost_target_met = cost_reduction_pct >= 40.0
    pass_target_met = pass_rate_diff <= 2.0

    print("\n" + "=" * 88)
    print("                    CURRICULUM SUCCESS VERIFICATION")
    print("=" * 88)
    print(f" 1. Cost Reduction Target (>= 40.0%):  {cost_reduction_pct:.1f}%  ->  {'✓ PASS' if cost_target_met else '✗ FAIL'}")
    print(f" 2. Pass Rate Parity Target (<= 2.0%): {pass_rate_diff:.1f}% pts ->  {'✓ PASS' if pass_target_met else '✗ FAIL'}")
    print("=" * 88)

    if cost_target_met and pass_target_met:
        print("\n🎉 SUCCESS: All cost and latency optimization targets successfully achieved!")
        print(f"   • Slashed cost per query by {cost_reduction_pct:.1f}% (Required: >= 40.0%).")
        print(f"   • Maintained {opt_summary.pass_rate:.1f}% pass rate (within {pass_rate_diff:.1f} points of baseline).\n")
    else:
        print("\n[!] Warning: One or more optimization targets fell short of curriculum requirements.\n")


if __name__ == "__main__":
    main()
