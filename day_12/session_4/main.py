"""
Day 12 - Session 04: Distillation & Model Routing
Demonstrates cascading model routing (small-model first, escalating to large
model on low confidence) and mining production traces for model distillation.
"""

from __future__ import annotations
import json
from model_router import CascadingModelRouter
from benchmark_routing_economics import run_routing_benchmark, print_routing_scorecard
from production_trace_miner import ProductionTraceMiner, generate_synthetic_production_traces


def demo_cascading_router():
    print("\n--- 1. Cascading Router Execution ---")
    query = "Critical alert: payment-api connection pool exhausted, returning HTTP 500."
    print(f"Incident Query: '{query}'")

    router = CascadingModelRouter(confidence_threshold=0.80)
    decision = router.route_query(query)

    print(f"Final Model Tier: {decision.final_tier}")
    print(f"Escalated:        {decision.escalated} (Confidence: {decision.small_confidence:.2f})")
    print(f"Total Latency:    {decision.total_latency_ms:.1f} ms")
    print(f"Cost Savings:     {decision.cost_savings_pct:.1f}% vs monolithic large model")


def demo_trace_mining():
    print("\n--- 2. Mining Production Traces for Distillation ---")
    raw_traces = generate_synthetic_production_traces(count=30)
    miner = ProductionTraceMiner(min_feedback_score=0.85)
    pairs, summary = miner.mine_traces(raw_traces)

    print(f"Mined {len(pairs)} high-quality (input, output) training pairs from {len(raw_traces)} traces.")
    print(f"Acceptance Rate: {summary['yield_pct']:.1f}%")


def main():
    print("Day 12 Session 04: Model Routing & Distillation\n")
    demo_cascading_router()
    demo_trace_mining()

    print("\n--- 3. Running 30-Query Cascading Routing Benchmark ---")
    results = run_routing_benchmark()
    print_routing_scorecard(results)


if __name__ == "__main__":
    main()
