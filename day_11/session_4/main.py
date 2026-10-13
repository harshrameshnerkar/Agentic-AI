"""
Day 11 - Session 04: Context Engineering at Scale
Demonstrates:
1. Side-by-side comparison: Baseline vs Context-Engineered Capstone Agent.
2. Tool schema pruning & Sub-agent context isolation.
3. Automated token reduction benchmark (achieving >= 40% reduction).
"""

from __future__ import annotations
import time
from dotenv import load_dotenv

load_dotenv()

from memory_manager import MemoryManager
from context_optimizer import context_optimizer
from optimized_capstone_agent import (
    ContextEngineeredCapstoneAgent,
    CAPSTONE_TOOL_SCHEMAS,
    estimate_schema_tokens,
)
from benchmark_context_reduction import run_context_reduction_benchmark


def run_side_by_side_demo():
    print("\n--- 1. Side-by-Side Execution Comparison ---")
    query = "Search runbooks for PostgreSQL connection pool exhaustion SOP."
    print(f"Query: '{query}'")

    # Baseline
    mem_base = MemoryManager()
    agent_base = ContextEngineeredCapstoneAgent(memory=mem_base, optimized=False)
    res_base = agent_base.run(query)

    # Optimized
    mem_opt = MemoryManager()
    agent_opt = ContextEngineeredCapstoneAgent(memory=mem_opt, optimized=True)
    res_opt = agent_opt.run(query)

    b_tok = res_base["tokens_used"]
    o_tok = res_opt["tokens_used"]
    savings_pct = ((b_tok - o_tok) / b_tok * 100) if b_tok > 0 else 0

    print(f"Baseline Tokens:  {b_tok}")
    print(f"Optimized Tokens: {o_tok}")
    print(f"Token Reduction:  {savings_pct:.1f}%")


def run_tool_pruning_demo():
    print("\n--- 2. Tool Schema Pruning (Context Isolation) ---")
    queries = [
        "What is our Sev-1 on-call SLA in the runbooks?",
        "Which microservices are currently reporting degraded status?",
    ]
    for q in queries:
        pruned = context_optimizer.prune_tool_schemas(q, CAPSTONE_TOOL_SCHEMAS)
        base_tok = estimate_schema_tokens(CAPSTONE_TOOL_SCHEMAS)
        opt_tok = estimate_schema_tokens(pruned)
        cut = ((base_tok - opt_tok) / base_tok) * 100
        tool_names = [s["function"]["name"] for s in pruned]
        print(f"Query: '{q}' -> Active Tools: {tool_names} (Tokens: {base_tok} -> {opt_tok}, -{cut:.0f}%)")


def main():
    print("Day 11 Session 04: Context Engineering at Scale\n")
    run_side_by_side_demo()
    run_tool_pruning_demo()

    print("\n--- 3. Running 20-Case Context Reduction Benchmark ---")
    run_context_reduction_benchmark()


if __name__ == "__main__":
    main()
