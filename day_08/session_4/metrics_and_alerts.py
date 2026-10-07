"""
Metrics Aggregation and Failure Rate Alerting Engine.
Demonstrates:
- Metric extraction across distributed trace spans.
- Failure rate calculation.
- Automated SLA threshold alerting.
"""

from typing import Any, Dict, List
from tracer import Tracer


class FailureRateAlerter:
    """Aggregates trace logs, tracks failure trends, and evaluates alert thresholds."""

    def __init__(self, tracer: Tracer, failure_threshold_pct: float = 20.0):
        self.tracer = tracer
        self.failure_threshold_pct = failure_threshold_pct

    def calculate_metrics(self) -> Dict[str, Any]:
        """Scans all spans from persistent JSONL log and computes operational SLIs."""
        all_traces = self.tracer.load_traces()
        total_traces = len(all_traces)
        if total_traces == 0:
            return {
                "total_traces": 0,
                "failed_traces": 0,
                "failure_rate_pct": 0.0,
                "total_tokens": 0,
                "avg_duration_ms": 0.0,
            }

        failed_count = 0
        total_tokens = 0
        total_duration = 0.0

        for t_id, spans in all_traces.items():
            has_error = any(s["status"] == "ERROR" for s in spans)
            if has_error:
                failed_count += 1

            root_span = next((s for s in spans if s.get("parent_span_id") is None), spans[0])
            total_duration += root_span.get("duration_ms", 0.0)

            for s in spans:
                total_tokens += s.get("attributes", {}).get("total_tokens", 0)

        failure_rate_pct = round((failed_count / total_traces) * 100.0, 2)
        avg_duration = round(total_duration / total_traces, 2)

        return {
            "total_traces": total_traces,
            "failed_traces": failed_count,
            "successful_traces": total_traces - failed_count,
            "failure_rate_pct": failure_rate_pct,
            "total_tokens": total_tokens,
            "avg_duration_ms": avg_duration,
        }

    def evaluate_alert(self) -> Dict[str, Any]:
        """Checks if current failure rate breaches the configured SLA threshold."""
        metrics = self.calculate_metrics()
        rate = metrics["failure_rate_pct"]
        is_triggered = rate >= self.failure_threshold_pct and metrics["total_traces"] > 0

        alert = {
            "alert_status": "TRIGGERED" if is_triggered else "NORMAL",
            "severity": "CRITICAL" if is_triggered else "INFO",
            "current_failure_rate_pct": rate,
            "threshold_limit_pct": self.failure_threshold_pct,
            "sample_size_traces": metrics["total_traces"],
            "message": (
                f"🚨 SRE ALERT: Agent failure rate at {rate}% (Exceeds SLA threshold of {self.failure_threshold_pct}%)!"
                if is_triggered
                else f"✅ System Healthy: Agent failure rate at {rate}% (Within SLA threshold of {self.failure_threshold_pct}%)."
            ),
            "remediation_action": (
                "Review failing spans in traces.jsonl and invoke ReplayEngine to patch tool/prompt discrepancies."
                if is_triggered
                else "No action required."
            ),
        }
        return alert
