"""
Day 08 - Session 01: Multi-Agent Systems & Orchestration
Demonstrates Supervisor-Worker pattern (LangGraph), Sequential handoff,
Parallel fan-out with aggregation, and models the true costs (latency & error compounding).
"""

from __future__ import annotations
import time
from dotenv import load_dotenv

load_dotenv()

from supervisor_graph import MultiAgentOrchestrator
from patterns_comparison import (
    SequentialHandoffPipeline,
    ParallelFanOutAggregator,
    HonestCostsModel,
)


def run_supervisor_orchestration():
    print("\n--- 1. Supervisor-Worker Pattern (Researcher + Writer) ---")
    orchestrator = MultiAgentOrchestrator(max_iterations=6)
    task = (
        "Prepare an authoritative strategic briefing on the enterprise transition to "
        "Post-Quantum Cryptography (PQC), including finalized NIST standards, timelines, and primary risks."
    )
    print(f"Goal: {task}\n")

    start = time.monotonic()
    state = orchestrator.run(task=task)
    duration = time.monotonic() - start

    print("\nExecution History:")
    for step in state["execution_history"]:
        node = step["node"]
        elapsed = step["elapsed_sec"]
        if node == "supervisor":
            print(f"  Supervisor -> Next: '{step['target'].upper()}' ({elapsed:.2f}s)")
        else:
            print(f"  Worker '{node}' finished in {elapsed:.2f}s")

    print(f"\nFinal Report:\n{state['draft_report'].strip()}")
    print(f"\nTotal workflow duration: {duration:.2f}s across {state['iteration']} iterations.")
    assert state["draft_report"] is not None


def run_sequential_vs_parallel():
    print("\n--- 2. Sequential Handoff vs Parallel Fan-Out ---")

    # Sequential
    seq = SequentialHandoffPipeline()
    t0 = time.monotonic()
    seq_res = seq.run(task="Post-Quantum Cryptography")
    dur_seq = time.monotonic() - t0
    print(f"Sequential Wall-Clock: {dur_seq:.2f}s (Researcher: {seq_res['latency_breakdown']['researcher_sec']:.2f}s, Writer: {seq_res['latency_breakdown']['writer_sec']:.2f}s)")

    # Parallel
    fanout = ParallelFanOutAggregator()
    t0 = time.monotonic()
    par_res = fanout.run(topic_a="post_quantum_cryptography", topic_b="agentic_ai_orchestration")
    dur_par = time.monotonic() - t0
    print(f"Parallel Fan-Out Wall-Clock: {dur_par:.2f}s (Concurrent tasks fetched together!)")


def run_honest_costs_analysis():
    print("\n--- 3. The Honest Costs: Error Compounding & Token Bloat ---")

    print("Compounding Error Risk (assuming 90% single-step accuracy):")
    for n in [1, 2, 3, 4]:
        stats = HonestCostsModel.calculate_error_compounding(step_success_rate=0.90, num_agents=n)
        print(f"  {n} Agents: Success Rate = {stats['overall_system_success_pct']:.1f}% (Risk = {stats['compounded_error_risk_pct']:.1f}%)")

    print("\nToken Bloat (Shared Context vs Isolated State):")
    for turns in [2, 4, 6]:
        bloat = HonestCostsModel.calculate_token_bloat(num_turns=turns, tokens_per_turn=1500)
        print(f"  {turns} Turns: Shared = {bloat['shared_history_total_tokens']} tokens vs Isolated = {bloat['isolated_state_total_tokens']} tokens ({bloat['token_overhead_factor']}x)")


def main():
    print("Day 08 Session 01: Multi-Agent Systems & Patterns")
    run_supervisor_orchestration()
    run_sequential_vs_parallel()
    run_honest_costs_analysis()


if __name__ == "__main__":
    main()
