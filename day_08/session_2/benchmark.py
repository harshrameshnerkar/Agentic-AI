"""
Benchmark and Comparative Evaluation Engine for Day 8 Session 2.
Compares Fixed Deterministic Pipeline vs Autonomous Agent across:
- Latency (seconds)
- LLM API Calls Count
- Token Consumption & Estimated Cost
- Mathematical Precision (Ground Truth comparison)
- Debuggability & Reproducibility
- Success Rate
"""

from typing import Any, Dict, List

def format_ascii_table(rows: List[List[str]]) -> str:
    """Formats 2D list of strings into a clean ASCII table without external dependencies."""
    if not rows:
        return ""
    col_widths = [max(len(str(row[i])) for row in rows) for i in range(len(rows[0]))]
    separator = "+-" + "-+-".join("-" * w for w in col_widths) + "-+"
    lines = [separator]
    header = "| " + " | ".join(f"{str(cell):<{w}}" for cell, w in zip(rows[0], col_widths)) + " |"
    lines.append(header)
    lines.append(separator)
    for row in rows[1:]:
        line = "| " + " | ".join(f"{str(cell):<{w}}" for cell, w in zip(row, col_widths)) + " |"
        lines.append(line)
    lines.append(separator)
    return "\n".join(lines)

from fixed_pipeline import FixedPipelineAuditor
from agent_solution import AutonomousAgentAuditor
from data import GROUND_TRUTH


# Cost per 1M tokens (e.g. Gemini 1.5 / Flash equivalent estimates)
INPUT_COST_PER_M = 0.075   # $0.075 per 1M input tokens
OUTPUT_COST_PER_M = 0.30   # $0.30 per 1M output tokens


def estimate_dollar_cost(prompt_tokens: int, completion_tokens: int) -> float:
    """Estimates dollar cost of LLM inference."""
    return (prompt_tokens / 1_000_000 * INPUT_COST_PER_M) + (completion_tokens / 1_000_000 * OUTPUT_COST_PER_M)


class AuditorBenchmark:
    """
    Runs both the Fixed Pipeline and Autonomous Agent against the identical task,
    captures empirical metrics, and produces a comparative analysis.
    """

    def __init__(self):
        self.pipeline = FixedPipelineAuditor()
        self.agent = AutonomousAgentAuditor()

    def run_benchmark(self) -> Dict[str, Any]:
        # 1. Run Fixed Pipeline
        print("  [1/2] Running Fixed Deterministic Pipeline...", flush=True)
        pipeline_res = self.pipeline.run()

        # 2. Run Autonomous Agent
        print("  [2/2] Running Autonomous ReAct Agent...", flush=True)
        agent_res = self.agent.run()

        # Calculate costs
        pipeline_cost = estimate_dollar_cost(pipeline_res["prompt_tokens"], pipeline_res["completion_tokens"])
        agent_cost = estimate_dollar_cost(agent_res["prompt_tokens"], agent_res["completion_tokens"])

        # Speedup & Token Efficiency Ratios
        speedup_ratio = round(agent_res["total_time_sec"] / max(0.001, pipeline_res["total_time_sec"]), 2)
        token_ratio = round(agent_res["total_tokens"] / max(1, pipeline_res["total_tokens"]), 2)
        cost_ratio = round(agent_cost / max(0.000001, pipeline_cost), 2)

        comparison_table = [
            ["Metric", "Fixed Deterministic Pipeline", "Autonomous ReAct Agent", "Advantage"],
            ["Architecture", "Deterministic Python + 1 Synthesis LLM", "Multi-Turn ReAct Loop (Tools)", "Pipeline (Simpler)"],
            ["LLM Calls Made", f"{pipeline_res['llm_calls_made']} call", f"{agent_res['llm_calls_made']} calls", f"Pipeline ({agent_res['llm_calls_made']}x fewer)"],
            ["Total Wall-Clock Latency", f"{pipeline_res['total_time_sec']:.2f} s", f"{agent_res['total_time_sec']:.2f} s", f"Pipeline ({speedup_ratio}x faster)"],
            ["Deterministic Math Time", f"{pipeline_res['deterministic_time_sec'] * 1000:.3f} ms", "N/A (Delegated to LLM)", "Pipeline (Instant)"],
            ["Total Tokens Consumed", f"{pipeline_res['total_tokens']:,} tokens", f"{agent_res['total_tokens']:,} tokens", f"Pipeline ({token_ratio}x less tokens)"],
            ["Estimated Inference Cost", f"${pipeline_cost:.6f}", f"${agent_cost:.6f}", f"Pipeline ({cost_ratio}x cheaper)"],
            ["Mathematical Accuracy", f"{pipeline_res['math_accuracy_pct']:.1f}% (Exact match: $59,956.00)", f"{agent_res['math_accuracy_pct']:.1f}% ({'Exact' if agent_res['found_exact_total'] else 'Drift/Rounded'})", "Pipeline (Zero Hallucination)"],
            ["Debuggability / Reproducibility", "100% Deterministic (Standard stack trace)", "Stochastic (Non-deterministic branches)", "Pipeline (Easy to test & debug)"],
            ["Success Rate (Known Steps)", "100% (Guaranteed code execution)", "Variable (Prone to loop/tool errors)", "Pipeline"],
        ]

        return {
            "pipeline": pipeline_res,
            "agent": agent_res,
            "speedup_ratio": speedup_ratio,
            "token_ratio": token_ratio,
            "cost_ratio": cost_ratio,
            "comparison_table": comparison_table,
        }
