"""
Day 8 - Session 1: Multi-Agent Systems & Orchestration
Master Demonstration and Verification Suite.

Demonstrates:
1. Supervisor / Orchestrator-Worker with Dynamic Routing (LangGraph StateGraph)
2. Sequential Handoff Pattern (A -> B)
3. Parallel Fan-Out with Aggregation (A || B -> C)
4. Shared vs Isolated State Architectures
5. The Honest Costs: Latency Multiplication, Token Compounding, and Error Propagation
"""

import sys
import json
import time

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from supervisor_graph import MultiAgentOrchestrator
from patterns_comparison import (
    SequentialHandoffPipeline,
    ParallelFanOutAggregator,
    HonestCostsModel,
)


def print_banner(title: str):
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def print_educational_overview():
    print_banner("1. MULTI-AGENT ARCHITECTURAL PATTERNS & THE HONEST COSTS")
    print("""
[1. SUPERVISOR / ORCHESTRATOR-WORKER]
   • Central LLM acts as the conductor / project manager.
   • Inspects the shared project state and dynamically decides which worker to activate.
   • Supports iterative quality loops (can reject worker drafts and request revision).
   • Handles routing conditionally: Supervisor -> Worker -> Supervisor -> Finish.

[2. SEQUENTIAL HANDOFF (PIPELINES)]
   • Rigid, linear chain: Agent A -> Agent B -> Agent C.
   • Predictable and low orchestration overhead, but zero flexibility or self-correction.
   • If Agent A produces flawed data, Agent B blindly processes it.

[3. PARALLEL FAN-OUT WITH AGGREGATION]
   • Splits independent sub-queries to execute concurrently across worker threads.
   • Merges disparate streams via an Aggregator / Synthesis node.
   • Minimizes wall-clock latency: max(T1, T2) + T_agg vs (T1 + T2 + T_agg).

[4. SHARED VS ISOLATED STATE]
   • Shared State: Global contracts (final artifacts, high-level task goals, routing directives).
   • Isolated State: Worker-private reasoning scratchpads. Isolating worker scratchpads
     prevents context pollution (e.g. Writer doesn't inherit raw HTTP trace logs).

[5. THE HONEST COSTS OF MULTI-AGENT SYSTEMS]
   • Latency Multiplies: N sequential agents = sum of all LLM execution times (often 20s-60s).
   • Errors Compound: At 90% accuracy per node, a 3-agent chain succeeds only 0.9^3 = 72.9% of the time!
   • Token Bloat: Passing full conversation histories to all workers causes O(N^2) token growth.
""", flush=True)


def test_supervisor_orchestration():
    print_banner("2. EXECUTING 2-AGENT RESEARCHER + WRITER WITH SUPERVISOR ROUTING")
    
    orchestrator = MultiAgentOrchestrator(max_iterations=6)
    
    task_prompt = (
        "Prepare an authoritative strategic briefing on the enterprise transition to "
        "Post-Quantum Cryptography (PQC), including finalized NIST standards, timelines, and primary risks."
    )
    print(f"Goal: \"{task_prompt}\"\n")
    print("Starting LangGraph Multi-Agent Execution (Supervisor -> Researcher -> Supervisor -> Writer -> Supervisor -> FINISH)...")
    
    t0 = time.monotonic()
    final_state = orchestrator.run(task=task_prompt)
    total_time = time.monotonic() - t0
    
    print("\n--- Execution History & Routing Trace ---")
    for step in final_state["execution_history"]:
        node = step["node"]
        elapsed = step["elapsed_sec"]
        if node == "supervisor":
            print(f"  👑 [SUPERVISOR (Turn {step['iteration']})] -> Routing Decision: '{step['target'].upper()}' ({elapsed:.2f}s)")
            print(f"     Rationale: {step['rationale']}")
            print(f"     Directive: {step['instructions']}")
        elif node == "researcher":
            print(f"  🔍 [RESEARCHER (Turn {step['iteration']})] -> Completed Domain Research ({elapsed:.2f}s)")
            print(f"     Artifact Preview: {step['output_preview']}")
        elif node == "writer":
            print(f"  ✍️ [WRITER (Turn {step['iteration']})] -> Synthesized Executive Briefing ({elapsed:.2f}s)")
            print(f"     Artifact Preview: {step['output_preview']}")

    print("\n" + "-" * 80)
    print(" FINAL EXECUTIVE BRIEFING PRODUCED BY WRITER AGENT")
    print("-" * 80)
    print(final_state["draft_report"].strip())

    print("\n--- Telemetry & Performance Metrics ---")
    print(f"Total Workflow Latency: {total_time:.2f}s")
    print(f"Iterations Completed:   {final_state['iteration']}")
    print(f"Node Latency Breakdown:")
    for node, lat in final_state["telemetry"]["node_latencies"].items():
        print(f"  • {node:<25} : {lat:.2f}s")

    # Assertions
    assert final_state["research_notes"] is not None, "Researcher failed to produce research notes!"
    assert final_state["draft_report"] is not None, "Writer failed to produce draft report!"
    assert final_state["next_agent"] == "FINISH", "Supervisor did not cleanly complete the workflow!"
    print("\n✓ TEST PASSED: Supervisor successfully coordinated Researcher and Writer to completion.")


def test_sequential_vs_parallel():
    print_banner("3. PATTERNS IN ACTION: SEQUENTIAL HANDOFF VS PARALLEL FAN-OUT")

    print("\n[A] Executing Sequential Handoff (Linear Chain: Researcher -> Writer)...")
    seq_pipeline = SequentialHandoffPipeline()
    t_seq_start = time.monotonic()
    seq_result = seq_pipeline.run(task="Post-Quantum Cryptography Enterprise Standards")
    dur_seq = time.monotonic() - t_seq_start
    print(f"  • Sequential Total Wall-Clock: {dur_seq:.2f}s")
    print(f"    - Researcher: {seq_result['latency_breakdown']['researcher_sec']:.2f}s")
    print(f"    - Writer:     {seq_result['latency_breakdown']['writer_sec']:.2f}s")

    print("\n[B] Executing Parallel Fan-Out with Aggregator (Concurrent Sub-Tasks)...")
    fanout = ParallelFanOutAggregator()
    t_par_start = time.monotonic()
    par_result = fanout.run(
        topic_a="post_quantum_cryptography",
        topic_b="agentic_ai_orchestration"
    )
    dur_par = time.monotonic() - t_par_start
    print(f"  • Parallel Fan-Out Wall-Clock: {dur_par:.2f}s")
    print(f"    - Concurrent Research Step:  {par_result['fanout_wall_clock_sec']:.2f}s (2 topics fetched in parallel!)")
    print(f"    - Aggregation Synthesis:     {par_result['aggregation_wall_clock_sec']:.2f}s")

    print("\n✓ PATTERN COMPARISON COMPLETE: Demonstrated linear handoff and parallel fan-out aggregation.")


def test_honest_costs_analysis():
    print_banner("4. THE HONEST COSTS: MATHEMATICAL & EMPIRICAL MODELING")

    print("\n[HONEST COST 1: COMPOUNDING ERROR RATES]")
    print("If each agent has a 90% single-step accuracy (p = 0.90):")
    for agents in [1, 2, 3, 4, 5]:
        stats = HonestCostsModel.calculate_error_compounding(step_success_rate=0.90, num_agents=agents)
        print(f"  • {agents}-Agent Chain: Success Rate = {stats['overall_system_success_pct']:>6.2f}% | Compounded Error Risk = {stats['compounded_error_risk_pct']:>6.2f}%")

    print("\nIf each agent has an 80% single-step accuracy (p = 0.80):")
    for agents in [1, 2, 3, 4, 5]:
        stats = HonestCostsModel.calculate_error_compounding(step_success_rate=0.80, num_agents=agents)
        print(f"  • {agents}-Agent Chain: Success Rate = {stats['overall_system_success_pct']:>6.2f}% | Compounded Error Risk = {stats['compounded_error_risk_pct']:>6.2f}%")

    print("\n[HONEST COST 2: TOKEN BLOAT (SHARED CONTEXT VS ISOLATED STATE)]")
    for turns in [2, 4, 6, 8]:
        bloat = HonestCostsModel.calculate_token_bloat(num_turns=turns, tokens_per_turn=1500)
        print(f"  • {turns} Turns: Shared Context = {bloat['shared_history_total_tokens']:>6} tokens vs Isolated State = {bloat['isolated_state_total_tokens']:>6} tokens ({bloat['token_overhead_factor']}x overhead)")

    print("\n[HONEST COST 3: LATENCY MULTIPLICATION]")
    print("  • Monolithic Single Agent: 1 LLM call (~3.0s total).")
    print("  • 3-Agent Supervisor Loop: Supervisor(3s) + Worker1(4s) + Supervisor(3s) + Worker2(5s) + Supervisor(3s) = ~18.0s total.")
    print("  • Conclusion: Multi-agent systems trade 6x latency and compounded error risk for modularity.")


def main():
    print_banner("DAY 8 - SESSION 1: MULTI-AGENT SYSTEMS & ORCHESTRATION")
    
    print_educational_overview()
    test_supervisor_orchestration()
    time.sleep(1.0)
    test_sequential_vs_parallel()
    time.sleep(1.0)
    test_honest_costs_analysis()
    
    print_banner("DAY 8 - SESSION 1 VERIFICATION COMPLETED SUCCESSFULLY! ✅")


if __name__ == "__main__":
    main()
