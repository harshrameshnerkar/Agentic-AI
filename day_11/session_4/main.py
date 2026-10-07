"""
Day 11 - Session 4: Context Engineering at Scale
================================================
Interactive CLI and Demonstration Suite for Advanced Context Optimization:
  1. Full 20-Case Capstone Token Reduction Benchmark (Proving >= 40% token cut at 100% pass rate)
  2. Side-by-Side Query Inspector (Comparing Baseline vs Context-Engineered execution)
  3. Long-Context vs Retrieval Economics Calculator (Cost Tracker Tab comparison)
  4. Lost-in-the-Middle Phenomenon & Compaction Dynamics
  5. Prompt Caching & Cache-Aware Prompt Ordering
  6. Sub-Agent Context Isolation & Tool Schema Pruning
"""

import os
import sys
import json
import time

# Self-contained session imports from local session directory
current_dir = os.path.abspath(os.path.dirname(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from memory_manager import MemoryManager
from context_optimizer import context_optimizer, COMPACT_SYSTEM_PROMPT
from optimized_capstone_agent import (
    ContextEngineeredCapstoneAgent,
    BASELINE_SYSTEM_PROMPT,
    CAPSTONE_TOOL_SCHEMAS,
    estimate_tokens,
    estimate_schema_tokens,
)
from benchmark_context_reduction import run_context_reduction_benchmark


def print_header(title: str):
    print("\n" + "=" * 90)
    print(f" {title.center(88)} ")
    print("=" * 90)


def run_side_by_side_demo(query: str, history: list = None, role: str = "Admin", token: str = "AUTH-OPS-APPROVE-2026"):
    print_header("SIDE-BY-SIDE EXECUTION INSPECTOR")
    print(f"User Query : '{query}'")
    print(f"Active Role: {role} | Token: {token}")
    if history:
        print(f"History    : {len(history)} turns provided")

    # Baseline Agent
    mem_base = MemoryManager()
    mem_base.entity_store.set_entity("user_role", role)
    mem_base.entity_store.set_entity("approval_token", token)
    agent_base = ContextEngineeredCapstoneAgent(memory=mem_base, optimized=False)
    t0 = time.perf_counter()
    res_base = agent_base.run(query, raw_multi_turn_history=history)
    dur_base = (time.perf_counter() - t0) * 1000.0

    # Optimized Agent
    mem_opt = MemoryManager()
    mem_opt.entity_store.set_entity("user_role", role)
    mem_opt.entity_store.set_entity("approval_token", token)
    agent_opt = ContextEngineeredCapstoneAgent(memory=mem_opt, optimized=True)
    t0 = time.perf_counter()
    res_opt = agent_opt.run(query, raw_multi_turn_history=history)
    dur_opt = (time.perf_counter() - t0) * 1000.0

    b_tok = res_base["tokens_used"]
    o_tok = res_opt["tokens_used"]
    savings_pct = ((b_tok - o_tok) / b_tok * 100.0) if b_tok > 0 else 0.0

    bd_base = res_base.get("token_breakdown", {})
    bd_opt = res_opt.get("token_breakdown", {})

    print("\n" + "-" * 90)
    print(f"| Component / Metric          | Baseline (Monolithic) | Optimized (Context-Eng) | Delta / Reduction     |")
    print("-" * 90)
    sys_b = bd_base.get("system_tokens", 0)
    sys_o = bd_opt.get("system_tokens", 0)
    ent_b = bd_base.get("entity_tokens", 0)
    ent_o = bd_opt.get("entity_tokens", 0)
    his_b = bd_base.get("history_tokens", 0)
    his_o = bd_opt.get("history_tokens", 0)
    sch_b = bd_base.get("schema_tokens", 0)
    sch_o = bd_opt.get("schema_tokens", 0)
    res_b = bd_base.get("tool_result_tokens", 0)
    res_o = bd_opt.get("tool_result_tokens", 0)

    print(f"| System Prompt Tokens        | {sys_b:>21} | {sys_o:>23} | -{sys_b - sys_o:>3} tokens (-{((sys_b - sys_o) / max(1, sys_b) * 100):.1f}%) |")
    print(f"| Entity State Tokens         | {ent_b:>21} | {ent_o:>23} | -{ent_b - ent_o:>3} tokens (-{((ent_b - ent_o) / max(1, ent_b) * 100):.1f}%) |")
    print(f"| Dialogue History Tokens     | {his_b:>21} | {his_o:>23} | -{his_b - his_o:>3} tokens (-{((his_b - his_o) / max(1, his_b) * 100):.1f}%) |")
    print(f"| Tool Schema Tokens          | {sch_b:>21} | {sch_o:>23} | -{sch_b - sch_o:>3} tokens (-{((sch_b - sch_o) / max(1, sch_b) * 100):.1f}%) |")
    print(f"| Tool Output Tokens          | {res_b:>21} | {res_o:>23} | -{res_b - res_o:>3} tokens (-{((res_b - res_o) / max(1, res_b) * 100):.1f}%) |")
    print(f"| Completion Output Tokens    | {res_base['completion_tokens']:>21} | {res_opt['completion_tokens']:>23} | {res_opt['completion_tokens'] - res_base['completion_tokens']:>+4} tokens            |")
    print("-" * 90)
    print(f"| TOTAL CONTEXT TOKENS        | {b_tok:>21} | {o_tok:>23} | {savings_pct:>5.1f}% REDUCTION      |")
    print(f"| Execution Latency           | {dur_base:>18.2f} ms | {dur_opt:>20.2f} ms | {dur_base - dur_opt:>+5.2f} ms speedup     |")
    print("-" * 90)

    print("\n[TOOLS CALLED]:")
    print(f"  Baseline  : {res_base['tools_called']}")
    print(f"  Optimized : {res_opt['tools_called']}")

    print("\n[ACTIVE SCHEMAS EXPOSED]:")
    print(f"  Baseline  : All 7 Tool Schemas (Monolithic)")
    print(f"  Optimized : {bd_opt.get('active_tool_names', [])} (Sub-Agent Isolated)")

    print("\n[FINAL ANSWERS COMPARED]:")
    print(f"  Baseline  : {res_base['final_answer']}")
    print(f"  Optimized : {res_opt['final_answer']}")
    print("-" * 90)


def show_economics_calculator():
    print_header("LONG-CONTEXT VS RETRIEVAL ECONOMICS (COST TRACKER)")
    print("Comparison of Monolithic 'Full-Document Ingestion' vs 'Context-Engineered RAG + Compaction'")
    print("Pricing Model (Gemini 1.5 Flash / GPT-4o-mini Tier):")
    print("  - Input Tokens           : $0.150 per 1,000,000 tokens ($0.00015 / 1k)")
    print("  - Output Tokens          : $0.600 per 1,000,000 tokens ($0.00060 / 1k)")
    print("  - Prompt Cache Read (HIT): $0.0375 per 1,000,000 tokens (75% discount)")
    print("  - Chunk Embedding Cost   : $0.020 per 1,000,000 tokens (One-time index)")

    scenarios = [
        ("Small Enterprise (10k ops/month)", 10000),
        ("Mid-Market Ops (50k ops/month)", 50000),
        ("High-Scale Platform (250k ops/month)", 250000),
        ("Massive Enterprise (1,000k ops/month)", 1000000),
    ]

    base_avg_tok = 1085.8
    opt_avg_tok = 407.9
    raw_long_context_tok = 125000.0  # Ingesting full 500-page logs & codebases into 1M context

    print("\n" + "=" * 105)
    print(f"| Scale / Monthly Volume              | Monolithic Stuffing | Baseline Capstone   | Context-Engineered  | Monthly Savings |")
    print(f"|                                     | (125k tok / query)  | (1,085 tok / query) | (408 tok / query)   | (Opt vs Base)   |")
    print("=" * 105)

    for name, vol in scenarios:
        cost_stuff = vol * (raw_long_context_tok / 1_000_000) * 0.15
        cost_base = vol * (base_avg_tok / 1_000_000) * 0.15
        cost_opt = vol * (opt_avg_tok / 1_000_000) * 0.15
        savings = cost_base - cost_opt
        pct = (savings / cost_base) * 100.0

        print(f"| {name:<35} | ${cost_stuff:>17.2f} | ${cost_base:>17.2f} | ${cost_opt:>17.2f} | ${savings:>6.2f} ({pct:.1f}%) |")

    print("=" * 105)
    print("""
KEY ECONOMIC TAKEAWAYS:
1. Long-Context Window Fallacy: Stuffing 125k tokens of raw runbooks & log dumps into every turn
   costs $187.50 / 10k queries. Context-Engineered Capstone costs only $0.61 (99.7% cheaper).
2. Context Compaction Breakeven: Context engineering produces an immediate 62.4% token cut over
   standard Capstone, slashing cloud LLM spend while eliminating context buffer saturation.
3. Prompt Cache Bonus: Structuring static system instructions at the prompt head enables 75% cache
   discounts on repeated invocations, reducing marginal cost to ~$0.015 / 1k queries.
""")


def show_lost_in_the_middle_demo():
    print_header("LOST-IN-THE-MIDDLE & ATTENTION DYNAMICS")
    print("""
BACKGROUND:
The 'Lost-in-the-Middle' phenomenon (Liu et al., Stanford/Berkeley) proves that LLMs exhibit a
U-shaped attention curve:
  - High recall for tokens at the very beginning (Primacy Effect)
  - High recall for tokens at the very end (Recency Effect)
  - Sharp degradation (up to 40% accuracy drop) for critical facts placed in the middle 30%-70% of context.

HOW DAY 11 CONTEXT ENGINEERING ELIMINATES THIS:
1. Prompt Schema Ordering:
   [START] -> System Instructions (Primacy Zone)
   [EARLY] -> Session & Entity State (User identity, active incident tickets)
   [MIDDLE]-> Distilled Tool Results & Compaction Summaries (Stripped of boilerplate)
   [END]   -> Current User Intent & Immediate Prompt (Recency Zone)

2. Rolling Compaction vs Accumulation:
   Instead of appending 20 turns of raw conversation into the dangerous middle zone,
   we compact dialogue into a dense state tuple:
   '[COMPACTED DIALOGUE STATE: T1: User='...' -> Agent='...']'
   This keeps total context under 700 tokens, safely inside the high-attention band.
""")


def show_prompt_caching_guide():
    print_header("PROMPT CACHING & CACHE-AWARE PROMPT ORDERING")
    print("""
CACHE-AWARE PROMPT ARCHITECTURE:
Providers like Anthropic, OpenAI, and Google Gemini support prompt caching for exact prefix matches.
To maximize cache hit rate (target >= 85% cache hit), context must be ordered by volatility:

+-----------------------------------------------------------------------------------------------+
| 1. STATIC PREFIX (Invariant across all queries, 100% Cache Hit)                              |
|    - System Prompt: Role definition, security policies, core tool schemas                     |
|    - Tokens: ~120 tokens (Frozen in memory)                                                   |
+-----------------------------------------------------------------------------------------------+
| 2. SEMI-STATIC PREFIX (Invariant across user session, High Cache Hit)                         |
|    - Entity Memory: Active user, user role, environment (production), datacenter (us-east-1)   |
|    - Tokens: ~25 tokens                                                                       |
+-----------------------------------------------------------------------------------------------+
| 3. DYNAMIC CONTEXT (Updated periodically, Rolling Compaction)                                 |
|    - Rolling Summary: Compacted dialogue turns                                                |
|    - Tokens: ~30-60 tokens                                                                    |
+-----------------------------------------------------------------------------------------------+
| 4. DYNAMIC SUFFIX (Volatile per query, Never Cached)                                          |
|    - Current User Prompt + Pruned Tool Result                                                 |
|    - Tokens: ~50-150 tokens                                                                   |
+-----------------------------------------------------------------------------------------------+

CACHE HIT BENCHMARKS:
  - Cache Read Latency : ~40% faster Time-To-First-Token (TTFT)
  - Cache Pricing      : 75% to 80% cheaper than base input tokens
""")


def show_subagent_isolation_demo():
    print_header("SUB-AGENT CONTEXT ISOLATION & TOOL PRUNING")
    print("""
THE PROBLEM: MONOLITHIC TOOL OVERHEAD
In unoptimized systems, every agent turn loads ALL tool definitions into the prompt:
  - 7 Capstone tools = 680 prompt tokens consumed BEFORE the user even speaks!
  - 50 enterprise tools = 5,000+ prompt tokens per query!

THE SOLUTION: SUB-AGENT CONTEXT ISOLATION
We dynamically route queries to targeted tool subsets based on semantic intent:
""")
    sample_queries = [
        "What is our Sev-1 on-call SLA in the runbooks?",
        "Which microservices are currently reporting degraded status?",
        "Calculate availability percentage for 45 minutes downtime.",
        "Restart service payment-api with approval token.",
    ]
    for q in sample_queries:
        pruned = context_optimizer.prune_tool_schemas(q, CAPSTONE_TOOL_SCHEMAS)
        p_names = [s["function"]["name"] for s in pruned]
        tok_base = estimate_schema_tokens(CAPSTONE_TOOL_SCHEMAS)
        tok_opt = estimate_schema_tokens(pruned)
        cut = ((tok_base - tok_opt) / tok_base) * 100.0
        print(f"Query: '{q}'")
        print(f"  -> Isolated Tools: {p_names}")
        print(f"  -> Schema Tokens : {tok_base} tok (Monolithic) -> {tok_opt} tok (Isolated) [{cut:.1f}% reduction]\n")


def interactive_menu():
    while True:
        print_header("DAY 11 - SESSION 4: CONTEXT ENGINEERING AT SCALE")
        print(" [1] Run Full 20-Case Capstone Token Reduction Benchmark (Live Log Proof)")
        print(" [2] Interactive Side-by-Side Query Inspector (Baseline vs Optimized)")
        print(" [3] Long-Context vs Retrieval Economics Calculator (Cost Tracker Tab)")
        print(" [4] Lost-in-the-Middle Phenomenon & Compaction Dynamics")
        print(" [5] Prompt Caching & Cache-Aware Prompt Ordering Architecture")
        print(" [6] Sub-Agent Context Isolation & Tool Schema Pruning Demo")
        print(" [0] Exit")
        print("=" * 90)

        choice = input("Select an option (0-6): ").strip()
        if choice == "1":
            run_context_reduction_benchmark()
        elif choice == "2":
            print("\nSelect a pre-configured scenario or enter a custom query:")
            print("  (a) RAG Runbook Query (SOP lookup)")
            print("  (b) Diagnostic Tool Execution (System logs & error filtering)")
            print("  (c) Multi-turn Dialogue (Referential memory recall)")
            print("  (d) Blast-Radius Control (Privileged service restart)")
            print("  (e) Custom query input")
            sub = input("Choice (a-e): ").strip().lower()
            if sub == "a":
                run_side_by_side_demo("Under our Sev-1 escalation protocol runbook, what is the on-call response SLA?")
            elif sub == "b":
                run_side_by_side_demo("Check the ingress log for upstream timeout errors.")
            elif sub == "c":
                hist = [
                    ("Show me active ticket INC-801 in the database.", "Incident INC-801 is assigned to alice@ops.internal for payment gateway latency."),
                ]
                run_side_by_side_demo("Who is the assigned owner for that active incident ticket we just referenced?", history=hist)
            elif sub == "d":
                run_side_by_side_demo("Restart service payment-api with token AUTH-OPS-APPROVE-2026 because it is degraded.", role="Auditor")
            elif sub == "e":
                custom_q = input("Enter custom query: ").strip()
                if custom_q:
                    run_side_by_side_demo(custom_q)
            else:
                print("[!] Invalid selection.")
        elif choice == "3":
            show_economics_calculator()
        elif choice == "4":
            show_lost_in_the_middle_demo()
        elif choice == "5":
            show_prompt_caching_guide()
        elif choice == "6":
            show_subagent_isolation_demo()
        elif choice == "0":
            print("\nExiting Day 11 Session 4 Context Engineering Workspace. Goodbye!\n")
            break
        else:
            print("[!] Invalid option. Please enter 0-6.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--benchmark":
        run_context_reduction_benchmark()
    else:
        interactive_menu()
