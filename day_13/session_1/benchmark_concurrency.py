"""
Day 13 - Session 1: Concurrency Benchmark & Latency Reduction Measurement
=========================================================================
Compares:
  - Sequential Tool Execution (Synchronous Baseline)
  - Parallel Tool Execution (Async Capstone with asyncio.gather)
Across representative multi-tool Capstone SRE triage queries.
Measures wall-clock latency, latency reduction percentage, and speedup factor.
"""

import os
import sys
import json
import asyncio
import time
from typing import Dict, List, Any
from dataclasses import dataclass

# Ensure local session directory is in sys.path
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from async_capstone_agent import AsyncCapstoneAgent, AgentRunResult

BENCHMARK_SCENARIOS = [
    {
        "id": "SCEN-01",
        "name": "Payment Gateway Timeout (3 Tools)",
        "query": "Payment-api pod payment-core-9a is logging elevated 5xx error rate. Inspect telemetry, logs, and runbooks.",
        "expected_tools": ["query_telemetry_db", "read_system_logs", "search_runbooks"],
    },
    {
        "id": "SCEN-02",
        "name": "Postgres Connection Pool Saturation (3 Tools)",
        "query": "Postgres connection pool nearing 98% saturation on postgres-primary. Query telemetry, read logs, and search runbooks.",
        "expected_tools": ["query_telemetry_db", "read_system_logs", "search_runbooks"],
    },
    {
        "id": "SCEN-03",
        "name": "Nginx Ingress 504 Burst (3 Tools)",
        "query": "Inspect nginx-ingress error logs for upstream 504 gateway timeouts. Check telemetry and search runbooks.",
        "expected_tools": ["query_telemetry_db", "read_system_logs", "search_runbooks"],
    },
    {
        "id": "SCEN-04",
        "name": "Payment SLA Error Rate Calculation (4 Tools)",
        "query": "Calculate error rate delta and SLA breach for payment-api while inspecting logs, telemetry, and runbooks.",
        "expected_tools": ["query_telemetry_db", "read_system_logs", "search_runbooks", "calculate_metrics"],
    },
    {
        "id": "SCEN-05",
        "name": "General Cluster Health Sweep (4 Tools)",
        "query": "Calculate cluster capacity ratios, query telemetry services, read payment logs, and search general runbooks.",
        "expected_tools": ["query_telemetry_db", "read_system_logs", "search_runbooks", "calculate_metrics"],
    },
]


async def run_concurrency_benchmark() -> Dict[str, Any]:
    agent = AsyncCapstoneAgent()

    print("\n" + "=" * 105)
    print(" DAY 13 - SESSION 1: CAPSTONE ASYNC & PARALLEL TOOL CONCURRENCY BENCHMARK ".center(105))
    print("=" * 105)
    print("Measuring Wall-Clock Latency: Sequential Tool Execution vs. Parallel (asyncio.gather)...")
    print("-" * 105)
    print(f"| ID      | Scenario Name                   | Tools | Sequential (ms) | Parallel (ms) | Delta (ms) | Reduction %% | Speedup |")
    print("-" * 105)

    scenario_metrics = []
    total_seq_ms = 0.0
    total_par_ms = 0.0

    for sc in BENCHMARK_SCENARIOS:
        q = sc["query"]

        # 1. Sequential Execution (Baseline)
        seq_res: AgentRunResult = agent.run_sequential(q)

        # 2. Parallel Execution (Async Capstone)
        par_res: AgentRunResult = await agent.run_parallel(q)

        delta_ms = seq_res.wall_clock_latency_ms - par_res.wall_clock_latency_ms
        reduction_pct = (delta_ms / seq_res.wall_clock_latency_ms) * 100.0 if seq_res.wall_clock_latency_ms > 0 else 0.0
        speedup = seq_res.wall_clock_latency_ms / par_res.wall_clock_latency_ms if par_res.wall_clock_latency_ms > 0 else 1.0

        total_seq_ms += seq_res.wall_clock_latency_ms
        total_par_ms += par_res.wall_clock_latency_ms

        metric = {
            "scenario_id": sc["id"],
            "scenario_name": sc["name"],
            "tools_count": len(seq_res.tools_called),
            "tools_called": seq_res.tools_called,
            "sequential_latency_ms": seq_res.wall_clock_latency_ms,
            "parallel_latency_ms": par_res.wall_clock_latency_ms,
            "latency_reduction_ms": round(delta_ms, 2),
            "latency_reduction_pct": round(reduction_pct, 1),
            "speedup_factor": round(speedup, 2),
        }
        scenario_metrics.append(metric)

        print(
            f"| {sc['id']:<7} | {sc['name']:<31} | {len(seq_res.tools_called):>5} | "
            f"{seq_res.wall_clock_latency_ms:>13.1f}ms | {par_res.wall_clock_latency_ms:>11.1f}ms | "
            f"{delta_ms:>8.1f}ms | {reduction_pct:>10.1f}% | {speedup:>6.2f}x |"
        )

    overall_delta_ms = total_seq_ms - total_par_ms
    overall_reduction_pct = (overall_delta_ms / total_seq_ms) * 100.0 if total_seq_ms > 0 else 0.0
    overall_speedup = total_seq_ms / total_par_ms if total_par_ms > 0 else 1.0

    print("-" * 105)
    print(
        f"| TOTAL   | 5 Benchmark Workloads           |       | "
        f"{total_seq_ms:>13.1f}ms | {total_par_ms:>11.1f}ms | "
        f"{overall_delta_ms:>8.1f}ms | {overall_reduction_pct:>10.1f}% | {overall_speedup:>6.2f}x |"
    )
    print("=" * 105)

    summary = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_scenarios": len(BENCHMARK_SCENARIOS),
        "total_sequential_latency_ms": round(total_seq_ms, 2),
        "total_parallel_latency_ms": round(total_par_ms, 2),
        "average_sequential_ms": round(total_seq_ms / len(BENCHMARK_SCENARIOS), 2),
        "average_parallel_ms": round(total_par_ms / len(BENCHMARK_SCENARIOS), 2),
        "net_latency_reduction_ms": round(overall_delta_ms, 2),
        "net_latency_reduction_pct": round(overall_reduction_pct, 2),
        "net_speedup_factor": round(overall_speedup, 2),
        "scenarios": scenario_metrics,
    }

    # Save to JSON
    current_dir = os.path.dirname(os.path.abspath(__file__))
    out_file = os.path.join(current_dir, "latency_reduction_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\n[OK] Latency reduction scorecard saved to: {out_file}")
    return summary


if __name__ == "__main__":
    asyncio.run(run_concurrency_benchmark())
