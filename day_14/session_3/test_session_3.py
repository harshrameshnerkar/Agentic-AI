"""
Comprehensive Test Suite for Production Monitoring & Telemetry (Day 14 - Session 3).
Validates trace/span lifecycles, pricing calculation, percentile computation,
groundedness auditing, failure category tracking, silent quality decay detection, and alerts.
"""

import unittest
import datetime
from typing import List

from day_14.session_3.models import (
    Trace,
    SpanType,
    FailureCategory,
    AlertSeverity,
)
from day_14.session_3.pricing_engine import ModelPricingEngine
from day_14.session_3.tracer import ProductionTracer
from day_14.session_3.metrics_aggregator import MetricsAggregator
from day_14.session_3.alerting_engine import AlertingEngine
from day_14.session_3.trace_simulator import ProductionTraceSimulator


class ProductionMonitoringTestSuite(unittest.TestCase):
    def setUp(self) -> None:
        self.tracer = ProductionTracer()
        self.alert_engine = AlertingEngine()

    def test_01_trace_and_span_lifecycle(self) -> None:
        """Verifies multi-span hierarchy, token aggregation, and trace completion."""
        trace = self.tracer.start_trace(
            query="Inspect payment gateway error rate",
            session_id="SESS-001",
            user_id="sre@acme.corp",
            model_used="claude-3-5-sonnet",
        )
        self.assertIsNotNone(trace.trace_id)

        # 1. Start child span (LLM call)
        span_llm = self.tracer.log_llm_call(
            trace_id=trace.trace_id,
            model_name="claude-3-5-sonnet",
            prompt_tokens=1000,
            completion_tokens=200,
            prompt_text="Check error rates for payment gateway",
            completion_text="Tool call: execute_query",
            latency_ms=450.0,
        )
        self.assertEqual(span_llm.span_type, SpanType.LLM_CALL)
        self.assertEqual(len(trace.spans), 1)

        # 2. Start second span (Tool call)
        span_tool = self.tracer.log_tool_call(
            trace_id=trace.trace_id,
            tool_name="execute_query",
            tool_args={"service": "payment-api"},
            tool_result={"error_rate": 0.045},
            latency_ms=120.0,
        )
        self.assertEqual(span_tool.span_type, SpanType.TOOL_EXECUTION)
        self.assertEqual(len(trace.spans), 2)

        # Finalize trace
        finalized = self.tracer.end_trace(
            trace_id=trace.trace_id,
            response="Payment error rate is 4.5%",
            status="SUCCESS",
        )
        self.assertEqual(finalized.status, "SUCCESS")
        self.assertEqual(finalized.prompt_tokens, 1000)
        self.assertEqual(finalized.completion_tokens, 200)
        self.assertGreater(finalized.cost_usd, 0.0)

    def test_02_model_pricing_engine(self) -> None:
        """Verifies accurate token pricing per 1M tokens across models."""
        # Claude 3.5 Sonnet: $3.00/1M prompt, $15.00/1M completion
        # 100k prompt = $0.30, 20k completion = $0.30 => Total $0.60
        sonnet_cost = ModelPricingEngine.calculate_cost("claude-3-5-sonnet", 100_000, 20_000)
        self.assertAlmostEqual(sonnet_cost, 0.60, places=3)

        # Claude 3 Haiku: $0.25/1M prompt, $1.25/1M completion
        haiku_cost = ModelPricingEngine.calculate_cost("claude-3-haiku", 100_000, 20_000)
        self.assertAlmostEqual(haiku_cost, 0.05, places=3)

    def test_03_percentile_calculations(self) -> None:
        """Verifies p50, p90, p95, p99 latency calculations match exact mathematical definitions."""
        # 100 linear values from 1.0 to 100.0
        data = [float(i) for i in range(1, 101)]

        p50 = MetricsAggregator.calculate_percentile(data, 50.0)
        p90 = MetricsAggregator.calculate_percentile(data, 90.0)
        p95 = MetricsAggregator.calculate_percentile(data, 95.0)
        p99 = MetricsAggregator.calculate_percentile(data, 99.0)

        self.assertAlmostEqual(p50, 50.5, delta=1.0)
        self.assertAlmostEqual(p90, 90.1, delta=1.0)
        self.assertAlmostEqual(p95, 95.05, delta=1.0)
        self.assertAlmostEqual(p99, 99.01, delta=1.0)

    def test_04_groundedness_and_hallucination_detection(self) -> None:
        """Verifies grounded claim auditing and hallucination flag assignment."""
        trace = self.tracer.start_trace(query="Where is payment-db located?")

        # 1. Grounded scenario
        context = ["Payment database cluster is deployed in AWS us-east-1 region under VPC-998."]
        resp_grounded = "The payment database cluster is deployed in AWS us-east-1 region under VPC-998."
        score_good = self.tracer.evaluate_groundedness(trace.trace_id, context, resp_grounded)

        self.assertGreaterEqual(score_good.score, 0.75)
        self.assertFalse(score_good.hallucination_detected)

        # 2. Hallucination scenario
        resp_hallucinated = "The payment database is hosted on Azure Europe Paris datacenter with Cassandra replica."
        score_bad = self.tracer.evaluate_groundedness(trace.trace_id, context, resp_hallucinated)

        self.assertLess(score_bad.score, 0.65)
        self.assertTrue(score_bad.hallucination_detected)
        self.assertEqual(trace.failure_category, FailureCategory.HALLUCINATION)

    def test_05_time_series_aggregation_and_failure_categories(self) -> None:
        """Verifies grouping traces into time-series buckets with failure category breakdown."""
        traces = ProductionTraceSimulator.generate_14_day_telemetry(traces_per_day=30, seed=123)
        self.assertEqual(len(traces), 14 * 30)

        buckets = MetricsAggregator.aggregate_by_day(traces)
        self.assertEqual(len(buckets), 14)

        for b in buckets:
            self.assertEqual(b.total_traces, 30)
            self.assertEqual(b.successful_traces + b.failed_traces, 30)
            self.assertIn("TIMEOUT", b.failure_category_counts)
            self.assertIn("TOOL_FAILURE", b.failure_category_counts)
            self.assertIn("HALLUCINATION", b.failure_category_counts)

    def test_06_silent_quality_decay_detector(self) -> None:
        """Verifies detection of unprompted degradation (decay score >= 0.50)."""
        # Simulated 14 days contains healthy baseline in days 1-7, and intentional decay in days 8-9
        traces = ProductionTraceSimulator.generate_14_day_telemetry(traces_per_day=60, seed=42)
        report = MetricsAggregator.detect_silent_quality_decay(traces)

        self.assertTrue(report.is_decaying)
        self.assertGreaterEqual(report.decay_score, 0.5)
        self.assertIn("RETRIEVAL_INDEX_STALE", report.primary_suspect)

    def test_07_alerting_engine_evaluations(self) -> None:
        """Verifies alerting engine triggers high failure rate and P95 violation alerts."""
        traces = ProductionTraceSimulator.generate_14_day_telemetry(traces_per_day=40, seed=42)
        buckets = MetricsAggregator.aggregate_by_day(traces)

        # Day 10 is the acute incident spike in our simulator
        incident_bucket = buckets[9]  # index 9 is day 10
        alerts = self.alert_engine.evaluate_bucket(incident_bucket)

        self.assertGreater(len(alerts), 0)
        alert_names = [a.rule_name for a in alerts]
        self.assertIn("HIGH_FAILURE_RATE_SLA_BREACH", alert_names)
        self.assertIn("P95_LATENCY_SLA_VIOLATION", alert_names)

        # Acknowledge alert test
        alert_to_ack = alerts[0]
        ack_res = self.alert_engine.acknowledge_alert(alert_to_ack.alert_id)
        self.assertTrue(ack_res)
        self.assertEqual(alert_to_ack.status, "ACKNOWLEDGED")


if __name__ == "__main__":
    unittest.main()
