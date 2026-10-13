"""
Day 08 - Session 03: Context Engineering
Demonstrates how prompt pruning, anomaly filtering, and sub-agent context isolation
reduce token usage by >= 30% while maintaining 100% diagnostic accuracy.
"""

from __future__ import annotations
import time
from typing import Any, Dict
from dotenv import load_dotenv

load_dotenv()

from baseline_agent import BaselineAgent
from optimized_agent import ContextEngineeredAgent
from cost_tracker import calculate_savings


def evaluate_success(response: str) -> Dict[str, Any]:
    text = response.lower()
    has_metaspace = any(w in text for w in ["metaspace", "outofmemory", "oom"])
    has_culprit = any(w in text for w in ["hotreload", "bytebuddy", "class", "proxy"])
    has_remediation = any(w in text for w in ["remediation", "mitigat", "action", "increase"])
    return {
        "success": has_metaspace and (has_culprit or has_remediation)
    }


def main():
    task = (
        "Investigate microservice degradation incident INC-8821. "
        "Retrieve incident details, analyze telemetry metrics, inspect logs, "
        "and produce a concise Root Cause Analysis (RCA) report."
    )

    # 1. Baseline Agent (unengineered context)
    print("Running Baseline Agent (raw logs, unpruned metrics)...")
    baseline = BaselineAgent()
    base_res = baseline.run(task)
    base_eval = evaluate_success(base_res["final_answer"])
    print(f"  Baseline: {base_res['token_summary']['total_tokens']:,} tokens (Success: {base_eval['success']})")

    # 2. Context-Engineered Agent (pruned context & sub-agent isolation)
    print("\nRunning Context-Engineered Agent (pruned telemetry, isolated logs)...")
    optimized = ContextEngineeredAgent()
    opt_res = optimized.run(task)
    opt_eval = evaluate_success(opt_res["final_answer"])
    print(f"  Optimized: {opt_res['token_summary']['total_tokens']:,} tokens (Success: {opt_eval['success']})")

    # 3. Calculate savings
    savings = calculate_savings(baseline.tracker, optimized.tracker)
    print(f"\nToken Reduction: {savings['token_reduction_pct']}% (Target: >= 30%)")
    print(f"Cost Reduction: {savings['cost_reduction_pct']}% cheaper")

    assert savings["achieved_target_30pct"] is True, f"Achieved {savings['token_reduction_pct']}%, expected >= 30%"
    assert opt_eval["success"] is True, "Optimized agent failed diagnostic task"
    print("\nSuccess: > 30% token reduction achieved with 100% task accuracy.")


if __name__ == "__main__":
    main()
