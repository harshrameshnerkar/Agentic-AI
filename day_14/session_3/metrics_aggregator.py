"""
Metrics Aggregation and Silent Quality Decay Detection Engine.
Calculates time-series percentiles (p50, p90, p95, p99), cost trends, failure category distributions,
and detects silent quality decay using sliding-window statistical drift.
"""

from typing import List, Dict, Tuple, Optional
from collections import defaultdict
from pydantic import BaseModel
from day_14.session_3.models import (
    Trace,
    TimeSeriesBucket,
    MetricSummary,
    FailureCategory,
)


class SilentDecayReport(BaseModel):
    is_decaying: bool
    decay_score: float  # Composite anomaly score (0.0 to 1.0)
    pass_rate_drift_pct: float
    groundedness_drift_pct: float
    cost_inflation_pct: float
    latency_p95_creep_pct: float
    primary_suspect: str
    actionable_remediation: str


class MetricsAggregator:
    @staticmethod
    def calculate_percentile(values: List[float], percentile: float) -> float:
        """
        Calculates exact percentile (0 to 100) using nearest-rank / linear interpolation.
        """
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        k = (len(sorted_vals) - 1) * (percentile / 100.0)
        f = int(k)
        c = min(f + 1, len(sorted_vals) - 1)
        d = k - f
        return round(sorted_vals[f] + d * (sorted_vals[c] - sorted_vals[f]), 2)

    @classmethod
    def aggregate_by_day(cls, traces: List[Trace]) -> List[TimeSeriesBucket]:
        """
        Groups traces by calendar day and computes all required time-series metrics.
        """
        day_buckets: Dict[str, List[Trace]] = defaultdict(list)
        for t in traces:
            day_str = t.timestamp.strftime("%Y-%m-%d")
            day_buckets[day_str].append(t)

        sorted_days = sorted(day_buckets.keys())
        time_series: List[TimeSeriesBucket] = []

        for day in sorted_days:
            day_traces = day_buckets[day]
            total = len(day_traces)
            successes = sum(1 for t in day_traces if t.status == "SUCCESS")
            failures = total - successes
            pass_rate = round((successes / total) * 100.0, 2) if total > 0 else 0.0

            total_cost = round(sum(t.cost_usd for t in day_traces), 4)
            avg_cost = round(total_cost / total, 5) if total > 0 else 0.0

            latencies = [t.latency_ms for t in day_traces]
            p50 = cls.calculate_percentile(latencies, 50.0)
            p90 = cls.calculate_percentile(latencies, 90.0)
            p95 = cls.calculate_percentile(latencies, 95.0)
            p99 = cls.calculate_percentile(latencies, 99.0)

            groundedness_vals = [t.groundedness.score for t in day_traces]
            avg_groundedness = round(sum(groundedness_vals) / total, 3) if total > 0 else 1.0

            hallucinations = sum(1 for t in day_traces if t.groundedness.hallucination_detected)
            hallucination_rate = round((hallucinations / total) * 100.0, 2) if total > 0 else 0.0

            # Feedback
            rated_traces = [t for t in day_traces if t.feedback is not None]
            positives = sum(1 for t in rated_traces if t.feedback and t.feedback.thumbs_up)
            feedback_ratio = round((positives / len(rated_traces)) * 100.0, 1) if rated_traces else 100.0

            # Failure categories breakdown
            cat_counts: Dict[str, int] = defaultdict(int)
            for cat in FailureCategory:
                if cat != FailureCategory.NONE:
                    cat_counts[cat.value] = 0
            for t in day_traces:
                if t.failure_category != FailureCategory.NONE:
                    cat_counts[t.failure_category.value] += 1

            time_series.append(
                TimeSeriesBucket(
                    timestamp_bucket=day,
                    total_traces=total,
                    successful_traces=successes,
                    failed_traces=failures,
                    pass_rate=pass_rate,
                    total_cost_usd=total_cost,
                    avg_cost_usd=avg_cost,
                    p50_latency_ms=p50,
                    p90_latency_ms=p90,
                    p95_latency_ms=p95,
                    p99_latency_ms=p99,
                    avg_groundedness=avg_groundedness,
                    hallucination_rate=hallucination_rate,
                    positive_feedback_ratio=feedback_ratio,
                    failure_category_counts=dict(cat_counts),
                )
            )

        return time_series

    @classmethod
    def generate_summary(cls, traces: List[Trace], active_alerts_count: int = 0) -> MetricSummary:
        """
        Produces top-level operational summary KPIs.
        """
        total = len(traces)
        if total == 0:
            return MetricSummary(
                total_traces=0,
                overall_pass_rate=0.0,
                total_cost_usd=0.0,
                avg_cost_per_trace_usd=0.0,
                p50_latency_ms=0.0,
                p90_latency_ms=0.0,
                p95_latency_ms=0.0,
                p99_latency_ms=0.0,
                avg_groundedness=1.0,
                hallucination_rate=0.0,
                positive_feedback_ratio=100.0,
                active_alerts_count=active_alerts_count,
                silent_decay_detected=False,
            )

        successes = sum(1 for t in traces if t.status == "SUCCESS")
        pass_rate = round((successes / total) * 100.0, 2)
        total_cost = round(sum(t.cost_usd for t in traces), 4)
        avg_cost = round(total_cost / total, 5)

        latencies = [t.latency_ms for t in traces]
        p50 = cls.calculate_percentile(latencies, 50.0)
        p90 = cls.calculate_percentile(latencies, 90.0)
        p95 = cls.calculate_percentile(latencies, 95.0)
        p99 = cls.calculate_percentile(latencies, 99.0)

        groundedness_vals = [t.groundedness.score for t in traces]
        avg_groundedness = round(sum(groundedness_vals) / total, 3)

        hallucinations = sum(1 for t in traces if t.groundedness.hallucination_detected)
        hallucination_rate = round((hallucinations / total) * 100.0, 2)

        rated_traces = [t for t in traces if t.feedback is not None]
        positives = sum(1 for t in rated_traces if t.feedback and t.feedback.thumbs_up)
        feedback_ratio = round((positives / len(rated_traces)) * 100.0, 1) if rated_traces else 100.0

        decay_report = cls.detect_silent_quality_decay(traces)

        return MetricSummary(
            total_traces=total,
            overall_pass_rate=pass_rate,
            total_cost_usd=total_cost,
            avg_cost_per_trace_usd=avg_cost,
            p50_latency_ms=p50,
            p90_latency_ms=p90,
            p95_latency_ms=p95,
            p99_latency_ms=p99,
            avg_groundedness=avg_groundedness,
            hallucination_rate=hallucination_rate,
            positive_feedback_ratio=feedback_ratio,
            active_alerts_count=active_alerts_count,
            silent_decay_detected=decay_report.is_decaying,
        )

    @classmethod
    def detect_silent_quality_decay(
        cls,
        traces: List[Trace],
        baseline_traces: Optional[List[Trace]] = None,
        recent_traces: Optional[List[Trace]] = None,
        baseline_fraction: float = 0.5,
    ) -> SilentDecayReport:
        """
        Silent Quality Decay Detector:
        Compares historical baseline window with operational evaluation windows.
        Detects unprompted degradation in Groundedness, Cost inflation, or Latency creep
        even when HTTP status codes remain 200 OK.
        """
        if len(traces) < 40 and not (baseline_traces and recent_traces):
            return SilentDecayReport(
                is_decaying=False,
                decay_score=0.0,
                pass_rate_drift_pct=0.0,
                groundedness_drift_pct=0.0,
                cost_inflation_pct=0.0,
                latency_p95_creep_pct=0.0,
                primary_suspect="INSUFFICIENT_SAMPLE_SIZE",
                actionable_remediation="Collect at least 40 traces before running drift detection.",
            )

        def _evaluate_window(base: List[Trace], candidate: List[Trace]) -> SilentDecayReport:
            if not base or not candidate:
                return SilentDecayReport(
                    is_decaying=False,
                    decay_score=0.0,
                    pass_rate_drift_pct=0.0,
                    groundedness_drift_pct=0.0,
                    cost_inflation_pct=0.0,
                    latency_p95_creep_pct=0.0,
                    primary_suspect="EMPTY_WINDOW",
                    actionable_remediation="No traces in window.",
                )

            # 1. Pass Rate Drift
            base_pass = sum(1 for t in base if t.status == "SUCCESS") / len(base)
            cand_pass = sum(1 for t in candidate if t.status == "SUCCESS") / len(candidate)
            pass_drift = round((cand_pass - base_pass) * 100.0, 2)

            # 2. Groundedness Drift
            base_ground = sum(t.groundedness.score for t in base) / len(base)
            cand_ground = sum(t.groundedness.score for t in candidate) / len(candidate)
            ground_drift = round(((cand_ground - base_ground) / max(0.001, base_ground)) * 100.0, 2)

            # 3. Cost Inflation
            base_cost = sum(t.cost_usd for t in base) / len(base)
            cand_cost = sum(t.cost_usd for t in candidate) / len(candidate)
            cost_drift = round(((cand_cost - base_cost) / max(0.0001, base_cost)) * 100.0, 2)

            # 4. Latency p95 Creep
            base_p95 = cls.calculate_percentile([t.latency_ms for t in base], 95.0)
            cand_p95 = cls.calculate_percentile([t.latency_ms for t in candidate], 95.0)
            lat_drift = round(((cand_p95 - base_p95) / max(1.0, base_p95)) * 100.0, 2)

            # Signal evaluation
            decay_signals = 0
            suspects: List[str] = []

            if ground_drift < -8.0:
                decay_signals += 1
                suspects.append("RETRIEVAL_INDEX_STALE (Groundedness dropped by >8%)")
            if pass_drift < -3.5:
                decay_signals += 1
                suspects.append("PROMPT_LOGIC_REGRESSION (Pass rate dropped)")
            if cost_drift > 25.0:
                decay_signals += 1
                suspects.append("TOKEN_INFLATION (Cost per query inflated by >25%)")
            if lat_drift > 30.0:
                decay_signals += 1
                suspects.append("DEPENDENCY_LATENCY_CREEP (p95 latency jumped by >30%)")

            is_decay = decay_signals >= 2
            score = round(min(1.0, decay_signals * 0.35), 2)
            suspect_str = " | ".join(suspects) if suspects else "NORMAL_OPERATION"
            rem = (
                "Trigger automated rollback to last verified golden prompt & reindex vector database."
                if is_decay
                else "System quality metrics operating within healthy historical parameters."
            )

            return SilentDecayReport(
                is_decaying=is_decay,
                decay_score=score,
                pass_rate_drift_pct=pass_drift,
                groundedness_drift_pct=ground_drift,
                cost_inflation_pct=cost_drift,
                latency_p95_creep_pct=lat_drift,
                primary_suspect=suspect_str,
                actionable_remediation=rem,
            )

        # Case 1: Explicit windows provided
        if baseline_traces and recent_traces:
            return _evaluate_window(baseline_traces, recent_traces)

        # Case 2: Auto-partition by timeline
        sorted_traces = sorted(traces, key=lambda t: t.timestamp)
        split_idx = int(len(sorted_traces) * baseline_fraction)
        baseline = sorted_traces[:split_idx]
        recent = sorted_traces[split_idx:]

        # Standard tail window report
        tail_report = _evaluate_window(baseline, recent)
        if tail_report.is_decaying:
            return tail_report

        # Rolling window check: check if any 2-day contiguous slice post-baseline exhibited decay
        day_buckets: Dict[str, List[Trace]] = defaultdict(list)
        for t in sorted_traces:
            day_str = t.timestamp.strftime("%Y-%m-%d")
            day_buckets[day_str].append(t)

        all_days = sorted(day_buckets.keys())
        baseline_days = all_days[:int(len(all_days) * baseline_fraction)]
        post_days = all_days[int(len(all_days) * baseline_fraction):]

        base_pool = [t for d in baseline_days for t in day_buckets[d]]

        for i in range(len(post_days)):
            # Look at 2-day window
            slice_days = post_days[i : i + 2]
            slice_traces = [t for d in slice_days for t in day_buckets[d]]
            if len(slice_traces) >= 20:
                report = _evaluate_window(base_pool, slice_traces)
                if report.is_decaying:
                    return report

        return tail_report
