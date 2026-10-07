"""
Production Monitoring & Observability Hub - Master CLI & Server Launcher.
Demonstrates trace collection, sliding window percentile aggregations,
silent quality decay audits, and launches the live web dashboard.
"""

import os
import sys
import argparse
import uvicorn
from typing import List

from day_14.session_3.models import Trace
from day_14.session_3.trace_simulator import ProductionTraceSimulator
from day_14.session_3.tracer import ProductionTracer
from day_14.session_3.metrics_aggregator import MetricsAggregator
from day_14.session_3.alerting_engine import AlertingEngine


def print_banner(title: str) -> None:
    print("\n" + "=" * 95)
    print(f"{title:^95}")
    print("=" * 95)


def render_terminal_dashboard(traces: List[Trace]) -> None:
    """Renders comprehensive time-series monitoring dashboard in the terminal."""
    time_series = MetricsAggregator.aggregate_by_day(traces)
    summary = MetricsAggregator.generate_summary(traces)
    decay_report = MetricsAggregator.detect_silent_quality_decay(traces)

    print_banner("1. PRODUCTION KPI SCORECARD (14-DAY ROLLING WINDOW)")
    print(f"Total Telemetry Traces Captured : {summary.total_traces:,}")
    print(f"Overall SLA Pass Rate          : {summary.overall_pass_rate}% (Target: >= 95.0%)")
    print(f"Total Token Spend (USD)        : ${summary.total_cost_usd:,.2f} (Avg: ${summary.avg_cost_per_trace_usd:.4f}/trace)")
    print(f"Latency SLA Percentiles        : p50: {summary.p50_latency_ms}ms | p90: {summary.p90_latency_ms}ms | p95: {summary.p95_latency_ms}ms | p99: {summary.p99_latency_ms}ms")
    print(f"Mean Groundedness Score        : {summary.avg_groundedness:.3f} / 1.000")
    print(f"Hallucination Occurrence Rate  : {summary.hallucination_rate}%")
    print(f"User CSAT (Thumbs Up Ratio)    : {summary.positive_feedback_ratio}%")
    print(f"Silent Quality Decay Detected? : {'[ALERT] YES' if summary.silent_decay_detected else '[PASS] NO'}")

    print_banner("2. TIME-SERIES DAILY METRICS & DRIFT BREAKDOWN")
    print(f"{'Date':<12} | {'Traces':<7} | {'Pass %':<8} | {'p50 (ms)':<9} | {'p95 (ms)':<9} | {'Cost ($)':<9} | {'Grounded':<9} | {'Halluc %':<8}")
    print("-" * 95)
    for b in time_series:
        pass_indicator = f"{b.pass_rate:>5.1f}%"
        print(f"{b.timestamp_bucket:<12} | {b.total_traces:<7} | {pass_indicator:<8} | {b.p50_latency_ms:<9.1f} | {b.p95_latency_ms:<9.1f} | ${b.total_cost_usd:<8.2f} | {b.avg_groundedness:<9.3f} | {b.hallucination_rate:>5.1f}%")

    print_banner("3. FAILURE CATEGORIES OVER TIME")
    print(f"{'Date':<12} | {'TIMEOUT':<9} | {'TOOL_FAIL':<10} | {'HALLUC':<8} | {'RATE_LIMIT':<11} | {'UNAUTH_ACT':<11}")
    print("-" * 95)
    for b in time_series:
        fc = b.failure_category_counts
        timeout_cnt = fc.get("TIMEOUT", 0)
        tool_cnt = fc.get("TOOL_FAILURE", 0)
        halluc_cnt = fc.get("HALLUCINATION", 0)
        rl_cnt = fc.get("RATE_LIMIT_ERROR", 0)
        unauth_cnt = fc.get("UNAUTHORIZED_DESTRUCTIVE_ACTION", 0)
        print(f"{b.timestamp_bucket:<12} | {timeout_cnt:<9} | {tool_cnt:<10} | {halluc_cnt:<8} | {rl_cnt:<11} | {unauth_cnt:<11}")

    print_banner("4. SILENT QUALITY DECAY STATISTICAL AUDIT")
    print(f"Decay Detected           : {'[ALERT] YES' if decay_report.is_decaying else '[PASS] NO'}")
    print(f"Composite Decay Score    : {decay_report.decay_score:.2f} (Threshold: >= 0.50)")
    print(f"Pass Rate Drift          : {decay_report.pass_rate_drift_pct:+.2f}%")
    print(f"Groundedness Drift       : {decay_report.groundedness_drift_pct:+.2f}%")
    print(f"Token Cost Inflation     : {decay_report.cost_inflation_pct:+.2f}%")
    print(f"P95 Latency Creep        : {decay_report.latency_p95_creep_pct:+.2f}%")
    print(f"Primary Suspect Root Cause: {decay_report.primary_suspect}")
    print(f"Actionable Remediation   : {decay_report.actionable_remediation}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Agentic Observability Hub & Telemetry Pipeline")
    parser.add_argument("--simulate", action="store_true", help="Generate fresh 14-day production traces JSON")
    parser.add_argument("--audit-decay", action="store_true", help="Run statistical silent decay detector")
    parser.add_argument("--dashboard-terminal", action="store_true", help="Print ASCII terminal dashboard")
    parser.add_argument("--serve", action="store_true", help="Start FastAPI web dashboard server")
    parser.add_argument("--port", type=int, default=8000, help="Web server port (default: 8000)")

    args = parser.parse_args()
    data_path = os.path.join(os.path.dirname(__file__), "production_traces.json")

    tracer = ProductionTracer()
    if args.simulate or not os.path.exists(data_path):
        print("[INFO] Generating 14-day multi-span production telemetry traces...")
        traces = ProductionTraceSimulator.generate_14_day_telemetry(traces_per_day=80)
        for t in traces:
            tracer.traces[t.trace_id] = t
        tracer.export_traces_json(data_path)
        print(f"[PASS] Successfully generated and exported {len(traces)} traces to: {data_path}")
    else:
        traces = tracer.load_traces_json(data_path)
        print(f"[INFO] Loaded {len(traces)} traces from existing artifact: {data_path}")

    if args.audit_decay:
        decay_report = MetricsAggregator.detect_silent_quality_decay(traces)
        print_banner("SILENT QUALITY DECAY STATISTICAL AUDIT")
        print(f"Decaying: {decay_report.is_decaying}")
        print(f"Decay Score: {decay_report.decay_score}")
        print(f"Suspect: {decay_report.primary_suspect}")
        return

    if args.dashboard_terminal or not args.serve:
        render_terminal_dashboard(traces)

    if args.serve:
        print_banner(f"LAUNCHING LIVE AGENTIC OBSERVABILITY WEB DASHBOARD (PORT {args.port})")
        print(f"Dashboard URL : http://127.0.0.1:{args.port}/")
        print(f"API Docs      : http://127.0.0.1:{args.port}/docs")
        print("Press Ctrl+C to stop the server.")
        uvicorn.run("day_14.session_3.app:app", host="127.0.0.1", port=args.port, reload=False)


if __name__ == "__main__":
    main()
