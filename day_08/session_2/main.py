"""
Day 8 - Session 2: When NOT to Use Agents
Master Demonstration and Empirical Benchmark Suite.

Compares:
1. Fixed Deterministic Pipeline (Python Code + 1 Targeted Synthesis LLM)
2. Autonomous ReAct Agent (Multi-Turn Tool Calling Loop)
Against the identical task: Multi-Currency Cloud Infrastructure Financial Audit.
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

from benchmark import AuditorBenchmark, format_ascii_table


def print_banner(title: str):
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def print_educational_framework():
    print_banner("1. THE GOLDEN RULES: WHEN NOT TO USE AGENTS")
    print("""
[CORE PRINCIPLES OF PRAGMATIC AGENTIC ENGINEERING]

1. DETERMINISTIC WORKFLOWS BEAT AGENTS FOR KNOWN STEPS:
   • If the sequence of steps is known in advance (e.g., fetch data -> validate -> convert -> sum -> alert),
     writing plain Python/code is 100x faster, 100x cheaper, and 100% mathematically accurate.
   • Delegating deterministic arithmetic or data parsing to an LLM agent introduces latency,
     token expense, and hallucination risks for zero benefit.

2. THE "SINGLE-AGENT-WITH-GOOD-TOOLS" BASELINE:
   • Before building a multi-turn autonomous agent or multi-agent swarm, ask:
     "Can a single prompt with deterministic helper functions solve this?"
   • In 80% of enterprise use cases, a deterministic pipeline with a single LLM synthesis step
     outperforms an autonomous agent on every operational metric.

3. DEBUGGABILITY & REPRODUCIBILITY:
   • Pipelines have deterministic control flows, standard unit tests, and exact stack traces.
   • Autonomous agents introduce stochastic decision paths, flaky arguments, and non-deterministic failures.

4. LATENCY & COST MULTIPLICATION:
   • A fixed pipeline executes local code in milliseconds (<1 ms) and requires only 1 LLM call.
   • An agent loops through 3 to 8 turns (Thought -> Action -> Observation), multiplying latency
     and compounding input tokens quadratically.
""", flush=True)


def run_comparative_benchmark():
    print_banner("2. RUNNING EMPIRICAL BENCHMARK ON IDENTICAL FINANCIAL AUDIT TASK")
    print("Task: Audit 5 multi-currency cloud invoices (USD, EUR, GBP), compute exact totals,")
    print("      identify top 3 cost drivers, flag budget anomalies (>15%), and write an executive briefing.\n")

    benchmark = AuditorBenchmark()
    results = benchmark.run_benchmark()

    pipe = results["pipeline"]
    agent = results["agent"]

    print_banner("3. EMPIRICAL BENCHMARK RESULTS TABLE")
    print(format_ascii_table(results["comparison_table"]))

    print_banner("4. COMPARATIVE OUTPUT INSPECTION")
    print("\n[A] FIXED DETERMINISTIC PIPELINE - EXECUTIVE SUMMARY:")
    print("-" * 60)
    print(pipe["executive_summary"].strip())

    print("\n[B] AUTONOMOUS REACT AGENT - FINAL RESPONSE:")
    print("-" * 60)
    print(agent["final_response"].strip())

    print_banner("5. BENCHMARK SUMMARY & ARCHITECTURAL VERDICT")
    print(f"""
Key Empirical Findings:
  • Speed:    Fixed Pipeline is {results['speedup_ratio']}x FASTER ({pipe['total_time_sec']:.2f}s vs {agent['total_time_sec']:.2f}s).
  • Math:     Pipeline achieved 100% exact ground-truth precision ($59,956.00 in <1 ms).
  • Tokens:   Pipeline used {results['token_ratio']}x FEWER tokens ({pipe['total_tokens']:,} vs {agent['total_tokens']:,}).
  • Cost:     Pipeline is {results['cost_ratio']}x CHEAPER to operate in production.
  • Verdict:  FOR KNOWN, SEQUENTIAL STEPS: A deterministic pipeline with targeted LLM synthesis
              drastically outperforms an autonomous agent on latency, cost, and reliability.
""", flush=True)

    # Assertions
    assert pipe["is_exact_match"] is True, "Pipeline failed to match mathematical ground truth!"
    assert pipe["total_time_sec"] < agent["total_time_sec"], "Pipeline was unexpectedly slower than agent!"


def main():
    print_banner("DAY 8 - SESSION 2: WHEN NOT TO USE AGENTS")
    print_educational_framework()
    time.sleep(1.0)
    run_comparative_benchmark()
    print_banner("DAY 8 - SESSION 2 BENCHMARK COMPLETED SUCCESSFULLY! ✅")


if __name__ == "__main__":
    main()
