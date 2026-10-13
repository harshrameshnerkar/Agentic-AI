"""
Day 08 - Session 02: When NOT to Use Agents
Compares a deterministic Python pipeline vs an autonomous ReAct agent
on a financial audit task to demonstrate where pipelines outperform agents.
"""

from __future__ import annotations
from dotenv import load_dotenv

load_dotenv()

from benchmark import AuditorBenchmark, format_ascii_table


def main():
    print("Running comparative benchmark: Fixed Pipeline vs Autonomous Agent...")
    benchmark = AuditorBenchmark()
    results = benchmark.run_benchmark()

    print("\nBenchmark Results:")
    print(format_ascii_table(results["comparison_table"]))

    pipe = results["pipeline"]
    agent = results["agent"]

    print(f"\nSpeedup: Pipeline is {results['speedup_ratio']}x faster ({pipe['total_time_sec']:.2f}s vs {agent['total_time_sec']:.2f}s)")
    print(f"Token Efficiency: Pipeline used {results['token_ratio']}x fewer tokens")
    print(f"Cost: Pipeline is {results['cost_ratio']}x cheaper")

    assert pipe["is_exact_match"] is True, "Pipeline failed to match mathematical ground truth!"
    assert pipe["total_time_sec"] < agent["total_time_sec"]
    print("\nVerdict: For known sequential workflows, deterministic code is faster, cheaper, and 100% accurate.")


if __name__ == "__main__":
    main()
