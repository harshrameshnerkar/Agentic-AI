"""
Comprehensive Multi-Agent Patterns Comparison and Honest Costs Analysis.
Demonstrates:
1. Supervisor / Orchestrator-Worker Pattern
2. Sequential Handoff Pattern (A -> B)
3. Parallel Fan-Out with Aggregation (A || B -> C)
4. Shared vs Isolated State Trade-Offs
5. The Honest Costs: Latency Multiplication, Token Compounding, and Error Propagation
"""

import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Tuple
from agents import ResearcherAgent, WriterAgent


class SequentialHandoffPipeline:
    """
    Pattern: Sequential Handoff (Chain / Pipeline).
    Data flows strictly linearly: Input -> Agent 1 (Researcher) -> Agent 2 (Writer) -> Output.
    Fastest to set up, but lacks dynamic feedback or conditional re-work.
    """

    def __init__(self):
        self.researcher = ResearcherAgent()
        self.writer = WriterAgent()

    def run(self, task: str) -> Dict[str, Any]:
        t0 = time.monotonic()

        # Step 1: Researcher performs work and produces notes
        t_r0 = time.monotonic()
        notes = self.researcher.research(task=task, supervisor_instructions="Direct pipeline research pass.")
        dur_research = time.monotonic() - t_r0

        # Step 2: Handoff directly to Writer without supervisor mediation
        t_w0 = time.monotonic()
        draft = self.writer.write(task=task, research_notes=notes, supervisor_instructions="Direct pipeline synthesis.")
        dur_writer = time.monotonic() - t_w0

        total_dur = time.monotonic() - t0

        return {
            "pattern": "Sequential Handoff",
            "task": task,
            "research_notes": notes,
            "final_report": draft,
            "latency_breakdown": {
                "researcher_sec": round(dur_research, 2),
                "writer_sec": round(dur_writer, 2),
                "total_wall_clock_sec": round(total_dur, 2)
            }
        }


class ParallelFanOutAggregator:
    """
    Pattern: Parallel Fan-Out with Aggregation.
    Two specialized workers execute independent research subtasks concurrently,
    then an aggregator joins the streams into a unified strategic briefing.
    Demonstrates wall-clock latency savings: max(T1, T2) + T_agg vs (T1 + T2 + T_agg).
    """

    def __init__(self):
        self.researcher_a = ResearcherAgent()
        self.researcher_b = ResearcherAgent()
        self.writer = WriterAgent()

    def run(self, topic_a: str, topic_b: str) -> Dict[str, Any]:
        t0 = time.monotonic()

        # Step 1: Parallel Fan-Out across 2 worker threads
        t_fanout_start = time.monotonic()
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_a = executor.submit(
                self.researcher_a.research,
                topic_a,
                "Focus on cryptographic primitives and NIST standards."
            )
            future_b = executor.submit(
                self.researcher_b.research,
                topic_b,
                "Focus on agent orchestration patterns and architectural trade-offs."
            )

            res_a = future_a.result()
            res_b = future_b.result()

        fanout_wall_clock = time.monotonic() - t_fanout_start

        # Step 2: Aggregation via Writer
        combined_notes = (
            f"=== RESEARCH TRACK A: {topic_a} ===\n{res_a}\n\n"
            f"=== RESEARCH TRACK B: {topic_b} ===\n{res_b}"
        )

        t_agg_start = time.monotonic()
        report = self.writer.write(
            task=f"Strategic Synthesis of {topic_a} and {topic_b}",
            research_notes=combined_notes,
            supervisor_instructions="Synthesize both research streams into a unified executive report."
        )
        agg_wall_clock = time.monotonic() - t_agg_start

        total_wall_clock = time.monotonic() - t0

        return {
            "pattern": "Parallel Fan-Out with Aggregation",
            "fanout_wall_clock_sec": round(fanout_wall_clock, 2),
            "aggregation_wall_clock_sec": round(agg_wall_clock, 2),
            "total_wall_clock_sec": round(total_wall_clock, 2),
            "final_report": report
        }


class HonestCostsModel:
    """
    Mathematical and empirical modeling of the three honest costs of multi-agent systems:
    1. Latency Multiplication
    2. Error Compounding
    3. Token Bloat (Shared vs Isolated Context)
    """

    @staticmethod
    def calculate_error_compounding(step_success_rate: float, num_agents: int) -> Dict[str, Any]:
        """
        Calculates compounded probability of end-to-end task success.
        Formula: P_total = p_1 * p_2 * ... * p_n
        Error Rate = 1 - P_total
        """
        p_total = step_success_rate ** num_agents
        error_risk = 1.0 - p_total
        return {
            "single_step_reliability_pct": round(step_success_rate * 100, 1),
            "number_of_sequential_nodes": num_agents,
            "overall_system_success_pct": round(p_total * 100, 2),
            "compounded_error_risk_pct": round(error_risk * 100, 2),
        }

    @staticmethod
    def calculate_token_bloat(num_turns: int, tokens_per_turn: int = 1500) -> Dict[str, Any]:
        """
        Compares token consumption between Shared History (O(N^2)) and Isolated State (O(N)).
        """
        # Shared history accumulates prior turns: sum_{i=1}^N (i * tokens_per_turn)
        shared_history_tokens = sum((i * tokens_per_turn) for i in range(1, num_turns + 1))
        # Isolated state only passes structured artifacts
        isolated_state_tokens = num_turns * tokens_per_turn

        return {
            "number_of_turns": num_turns,
            "shared_history_total_tokens": shared_history_tokens,
            "isolated_state_total_tokens": isolated_state_tokens,
            "token_overhead_factor": round(shared_history_tokens / max(1, isolated_state_tokens), 2),
        }
