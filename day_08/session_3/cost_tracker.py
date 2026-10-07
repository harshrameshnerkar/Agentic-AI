"""
Cost and Token Tracker for Context Engineering Evaluation.
Measures:
- Turn-by-turn prompt tokens and completion tokens
- Context growth trajectory
- Estimated dollar cost
- Exact percentage reduction between Baseline and Context-Engineered systems
"""

from typing import Any, Dict, List


INPUT_COST_PER_M = 0.075   # $0.075 per 1M input tokens
OUTPUT_COST_PER_M = 0.30   # $0.30 per 1M output tokens


class SessionTokenTracker:
    """Tracks token usage across an agent execution session."""

    def __init__(self, session_name: str):
        self.session_name = session_name
        self.turns: List[Dict[str, Any]] = []

    def record_turn(self, turn_number: int, prompt_tokens: int, completion_tokens: int, context_type: str = "main"):
        total = prompt_tokens + completion_tokens
        cost = (prompt_tokens / 1_000_000 * INPUT_COST_PER_M) + (completion_tokens / 1_000_000 * OUTPUT_COST_PER_M)
        self.turns.append({
            "turn": turn_number,
            "context_type": context_type,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total,
            "cost_usd": cost,
        })

    @property
    def total_prompt_tokens(self) -> int:
        return sum(t["prompt_tokens"] for t in self.turns)

    @property
    def total_completion_tokens(self) -> int:
        return sum(t["completion_tokens"] for t in self.turns)

    @property
    def total_tokens(self) -> int:
        return sum(t["total_tokens"] for t in self.turns)

    @property
    def total_cost_usd(self) -> float:
        return sum(t["cost_usd"] for t in self.turns)

    def summary(self) -> Dict[str, Any]:
        return {
            "session_name": self.session_name,
            "total_turns": len(self.turns),
            "prompt_tokens": self.total_prompt_tokens,
            "completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": round(self.total_cost_usd, 6),
        }


def calculate_savings(baseline: SessionTokenTracker, optimized: SessionTokenTracker) -> Dict[str, Any]:
    """Calculates exact token reduction percentage and financial cost savings."""
    base_tokens = max(1, baseline.total_tokens)
    opt_tokens = optimized.total_tokens
    token_reduction_pct = round(((base_tokens - opt_tokens) / base_tokens) * 100.0, 2)

    base_cost = baseline.total_cost_usd
    opt_cost = optimized.total_cost_usd
    cost_reduction_pct = round(((base_cost - opt_cost) / max(0.000001, base_cost)) * 100.0, 2)

    return {
        "baseline_total_tokens": base_tokens,
        "optimized_total_tokens": opt_tokens,
        "token_reduction_pct": token_reduction_pct,
        "baseline_cost_usd": round(base_cost, 6),
        "optimized_cost_usd": round(opt_cost, 6),
        "cost_reduction_pct": cost_reduction_pct,
        "achieved_target_30pct": token_reduction_pct >= 30.0,
    }
