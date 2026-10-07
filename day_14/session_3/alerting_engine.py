"""
Production Alerting Engine for Agentic Telemetry.
Evaluates failure-rate thresholds, p95 latency SLAs, groundedness drops,
and silent quality decay alarms.
"""

import uuid
import datetime
from typing import List
from day_14.session_3.models import (
    ProductionAlert,
    AlertSeverity,
    TimeSeriesBucket,
)
from day_14.session_3.metrics_aggregator import SilentDecayReport


class AlertingEngine:
    def __init__(
        self,
        failure_rate_threshold_pct: float = 5.0,  # Alert if failures > 5% (pass rate < 95%)
        p95_latency_threshold_ms: float = 1500.0,  # Alert if p95 > 1500ms
        min_groundedness_threshold: float = 0.85,  # Alert if groundedness < 0.85
        max_hallucination_rate_pct: float = 10.0,  # Alert if hallucinations > 10%
    ) -> None:
        self.failure_rate_threshold_pct = failure_rate_threshold_pct
        self.p95_latency_threshold_ms = p95_latency_threshold_ms
        self.min_groundedness_threshold = min_groundedness_threshold
        self.max_hallucination_rate_pct = max_hallucination_rate_pct
        self.alerts: List[ProductionAlert] = []

    def evaluate_bucket(self, bucket: TimeSeriesBucket) -> List[ProductionAlert]:
        """
        Evaluates a specific time-series bucket against operational SLOs.
        """
        new_alerts: List[ProductionAlert] = []
        failure_rate = round(100.0 - bucket.pass_rate, 2)

        # 1. Failure Rate Alert
        if failure_rate > self.failure_rate_threshold_pct:
            severity = AlertSeverity.CRITICAL if failure_rate > 15.0 else AlertSeverity.WARNING
            alert = ProductionAlert(
                alert_id=f"ALT-{uuid.uuid4().hex[:6].upper()}",
                timestamp=datetime.datetime.now(datetime.timezone.utc),
                rule_name="HIGH_FAILURE_RATE_SLA_BREACH",
                severity=severity,
                message=f"Agent failure rate spiked to {failure_rate}% in bucket '{bucket.timestamp_bucket}' (SLA threshold: <= {self.failure_rate_threshold_pct}%).",
                metric_value=failure_rate,
                threshold_value=self.failure_rate_threshold_pct,
                runbook_url="https://runbooks.corp.local/alerts/llm-failure-rate",
            )
            new_alerts.append(alert)

        # 2. P95 Latency SLA Alert
        if bucket.p95_latency_ms > self.p95_latency_threshold_ms:
            alert = ProductionAlert(
                alert_id=f"ALT-{uuid.uuid4().hex[:6].upper()}",
                timestamp=datetime.datetime.now(datetime.timezone.utc),
                rule_name="P95_LATENCY_SLA_VIOLATION",
                severity=AlertSeverity.WARNING,
                message=f"P95 latency reached {bucket.p95_latency_ms}ms in bucket '{bucket.timestamp_bucket}' (SLA threshold: <= {self.p95_latency_threshold_ms}ms).",
                metric_value=bucket.p95_latency_ms,
                threshold_value=self.p95_latency_threshold_ms,
                runbook_url="https://runbooks.corp.local/alerts/llm-latency-p95",
            )
            new_alerts.append(alert)

        # 3. Groundedness / Hallucination Alert
        if bucket.avg_groundedness < self.min_groundedness_threshold or bucket.hallucination_rate > self.max_hallucination_rate_pct:
            alert = ProductionAlert(
                alert_id=f"ALT-{uuid.uuid4().hex[:6].upper()}",
                timestamp=datetime.datetime.now(datetime.timezone.utc),
                rule_name="GROUNDEDNESS_DEGRADATION_DETECTED",
                severity=AlertSeverity.CRITICAL,
                message=f"Groundedness dropped to {bucket.avg_groundedness} (min: {self.min_groundedness_threshold}) and hallucination rate is {bucket.hallucination_rate}% in bucket '{bucket.timestamp_bucket}'.",
                metric_value=bucket.avg_groundedness,
                threshold_value=self.min_groundedness_threshold,
                runbook_url="https://runbooks.corp.local/alerts/llm-groundedness-drift",
            )
            new_alerts.append(alert)

        self.alerts.extend(new_alerts)
        return new_alerts

    def evaluate_silent_decay(self, decay_report: SilentDecayReport) -> List[ProductionAlert]:
        """
        Evaluates silent quality decay report.
        """
        new_alerts: List[ProductionAlert] = []
        if decay_report.is_decaying:
            alert = ProductionAlert(
                alert_id=f"ALT-{uuid.uuid4().hex[:6].upper()}",
                timestamp=datetime.datetime.now(datetime.timezone.utc),
                rule_name="SILENT_QUALITY_DECAY_ALARM",
                severity=AlertSeverity.CRITICAL,
                message=f"Silent quality decay detected! Decay score: {decay_report.decay_score}. Root suspect: {decay_report.primary_suspect}. Action: {decay_report.actionable_remediation}",
                metric_value=decay_report.decay_score,
                threshold_value=0.5,
                runbook_url="https://runbooks.corp.local/alerts/silent-quality-decay",
            )
            new_alerts.append(alert)
            self.alerts.append(alert)
        return new_alerts

    def get_active_alerts(self) -> List[ProductionAlert]:
        return [a for a in self.alerts if a.status == "ACTIVE"]

    def acknowledge_alert(self, alert_id: str) -> bool:
        for a in self.alerts:
            if a.alert_id == alert_id:
                a.status = "ACKNOWLEDGED"
                return True
        return False
