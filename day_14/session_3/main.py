"""
Day 14 - Session 03: Production Monitoring & Observability Hub
Demonstrates:
1. Rolling-window KPI aggregation (pass rate, latency percentiles p50/p95, cost).
2. Daily time-series metrics and error category breakdown.
3. Silent quality decay detection.
"""

from __future__ import annotations
from trace_simulator import ProductionTraceSimulator
from metrics_aggregator import MetricsAggregator
from alerting_engine import AlertingEngine


def main():
    print("Day 14 Session 03: Production Telemetry & Quality Monitoring\n")
    sim = ProductionTraceSimulator()
    traces = sim.generate_sample_traces(count=150)

    summary = MetricsAggregator.generate_summary(traces)
    print("--- Production KPI Scorecard (14-Day Rolling Window) ---")
    print(f"Total Traces:         {summary.total_traces:,}")
    print(f"Overall Pass Rate:    {summary.overall_pass_rate}%")
    print(f"Latency Percentiles:  p50: {summary.p50_latency_ms}ms | p95: {summary.p95_latency_ms}ms")
    print(f"Groundedness:         {summary.avg_groundedness:.3f} / 1.000")
    print(f"Silent Quality Decay: {'DETECTED' if summary.silent_decay_detected else 'NONE (Healthy)'}")

    # Check alert rules
    alerts = AlertingEngine.evaluate_alerts(summary)
    print(f"\nTriggered Alerts ({len(alerts)}):")
    for a in alerts:
        print(f"  • [{a.severity}] {a.title}: {a.description}")


if __name__ == "__main__":
    main()
