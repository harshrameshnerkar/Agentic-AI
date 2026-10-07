"""
Cost & Latency Tracking Engine.
Tracks and computes:
- Prompt tokens, completion tokens, cached tokens, and total tokens.
- Model tier cost calculations (USD).
- Latency metrics: p50 (median), p90, p95, p99, mean, min, max.
"""

import time
from typing import Dict, List, Any, Optional
import numpy as np
from pydantic import BaseModel, Field

# Pricing per 1 Million Tokens (USD)
# Gemini 3.1 Flash-Lite: $0.075 / 1M prompt, $0.30 / 1M completion
# Gemini 2.5 Pro: $1.25 / 1M prompt, $5.00 / 1M completion
MODEL_PRICING = {
    "gemini-3.1-flash-lite": {
        "prompt_per_million": 0.075,
        "completion_per_million": 0.30,
    },
    "gemini-2.5-pro": {
        "prompt_per_million": 1.25,
        "completion_per_million": 5.00,
    },
    "gemini-1.5-pro": {
        "prompt_per_million": 1.25,
        "completion_per_million": 5.00,
    },
    "cached": {
        "prompt_per_million": 0.0,
        "completion_per_million": 0.0,
    },
}


class QueryExecutionMetric(BaseModel):
    query_id: str
    model_used: str
    is_cache_hit: bool = False
    cache_type: Optional[str] = None  # "exact", "semantic", None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    passed: bool = True
    error_message: Optional[str] = None


class AggregatePerformanceSummary(BaseModel):
    total_queries: int = 0
    successful_queries: int = 0
    pass_rate: float = 0.0
    cache_hits: int = 0
    cache_hit_rate: float = 0.0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    cost_per_query_usd: float = 0.0
    latency_p50_ms: float = 0.0
    latency_p90_ms: float = 0.0
    latency_p95_ms: float = 0.0
    latency_p99_ms: float = 0.0
    latency_mean_ms: float = 0.0


class CostTracker:
    """Tracks token usage, costs, and latency percentiles across queries."""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.metrics: List[QueryExecutionMetric] = []

    def calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int, is_cache_hit: bool = False) -> float:
        """Calculates precise dollar cost for an invocation."""
        if is_cache_hit:
            return 0.0
        pricing = MODEL_PRICING.get(model, MODEL_PRICING["gemini-3.1-flash-lite"])
        prompt_cost = (prompt_tokens / 1_000_000.0) * pricing["prompt_per_million"]
        completion_cost = (completion_tokens / 1_000_000.0) * pricing["completion_per_million"]
        return prompt_cost + completion_cost

    def record_run(
        self,
        query_id: str,
        model_used: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        passed: bool,
        is_cache_hit: bool = False,
        cache_type: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> QueryExecutionMetric:
        """Records a completed query run."""
        cost = self.calculate_cost(model_used, prompt_tokens, completion_tokens, is_cache_hit)
        metric = QueryExecutionMetric(
            query_id=query_id,
            model_used=model_used,
            is_cache_hit=is_cache_hit,
            cache_type=cache_type,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost_usd=cost,
            latency_ms=latency_ms,
            passed=passed,
            error_message=error_message,
        )
        self.metrics.append(metric)
        return metric

    def compute_summary(self) -> AggregatePerformanceSummary:
        """Computes aggregate statistical summary including p50, p95 latencies."""
        if not self.metrics:
            return AggregatePerformanceSummary()

        total = len(self.metrics)
        passed = sum(1 for m in self.metrics if m.passed)
        cache_hits = sum(1 for m in self.metrics if m.is_cache_hit)
        total_tokens = sum(m.total_tokens for m in self.metrics)
        total_cost = sum(m.cost_usd for m in self.metrics)

        latencies = [m.latency_ms for m in self.metrics]
        p50 = float(np.percentile(latencies, 50))
        p90 = float(np.percentile(latencies, 90))
        p95 = float(np.percentile(latencies, 95))
        p99 = float(np.percentile(latencies, 99))
        mean_lat = float(np.mean(latencies))

        return AggregatePerformanceSummary(
            total_queries=total,
            successful_queries=passed,
            pass_rate=(passed / total) * 100.0,
            cache_hits=cache_hits,
            cache_hit_rate=(cache_hits / total) * 100.0,
            total_tokens=total_tokens,
            total_cost_usd=total_cost,
            cost_per_query_usd=total_cost / total if total > 0 else 0.0,
            latency_p50_ms=p50,
            latency_p90_ms=p90,
            latency_p95_ms=p95,
            latency_p99_ms=p99,
            latency_mean_ms=mean_lat,
        )
