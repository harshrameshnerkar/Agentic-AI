"""
FastAPI Telemetry & Production Monitoring Server.
Exposes REST endpoints for metrics, alerts, time-series percentiles,
trace exploration, and user feedback loops.
"""

import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from day_14.session_3.models import (
    Trace,
    TimeSeriesBucket,
    MetricSummary,
    ProductionAlert,
    UserFeedback,
    FailureCategory,
)
from day_14.session_3.tracer import ProductionTracer
from day_14.session_3.metrics_aggregator import MetricsAggregator, SilentDecayReport
from day_14.session_3.alerting_engine import AlertingEngine
from day_14.session_3.trace_simulator import ProductionTraceSimulator


app = FastAPI(
    title="Agentic Production Monitoring & Observability Hub",
    version="1.0.0",
    description="Langfuse / LangSmith style telemetry dashboard covering pass rate, cost, p95 latency, failure categories, groundedness, and silent decay.",
)

# Global in-memory storage & engines
TRACER = ProductionTracer()
ALERT_ENGINE = AlertingEngine()
_CACHED_TRACES: List[Trace] = []
_CACHED_TIMESERIES: List[TimeSeriesBucket] = []


def initialize_telemetry_dataset() -> None:
    """Populates initial 14-day production telemetry dataset and evaluates alerting rules."""
    global _CACHED_TRACES, _CACHED_TIMESERIES
    data_file = os.path.join(os.path.dirname(__file__), "production_traces.json")

    if os.path.exists(data_file):
        _CACHED_TRACES = TRACER.load_traces_json(data_file)
    else:
        _CACHED_TRACES = ProductionTraceSimulator.generate_14_day_telemetry(traces_per_day=80)
        for t in _CACHED_TRACES:
            TRACER.traces[t.trace_id] = t
        TRACER.export_traces_json(data_file)

    # Compute daily time-series
    _CACHED_TIMESERIES = MetricsAggregator.aggregate_by_day(_CACHED_TRACES)

    # Run alert evaluations across buckets
    ALERT_ENGINE.alerts.clear()
    for bucket in _CACHED_TIMESERIES:
        ALERT_ENGINE.evaluate_bucket(bucket)

    # Evaluate silent quality decay
    decay_report = MetricsAggregator.detect_silent_quality_decay(_CACHED_TRACES)
    ALERT_ENGINE.evaluate_silent_decay(decay_report)


# Run initialization on module load
initialize_telemetry_dataset()


# ============================================================================
# REST API Endpoints
# ============================================================================

@app.get("/api/summary", response_model=MetricSummary)
def get_metric_summary() -> MetricSummary:
    """Returns top-level KPI metrics across the active telemetry window."""
    active_alerts = len(ALERT_ENGINE.get_active_alerts())
    return MetricsAggregator.generate_summary(_CACHED_TRACES, active_alerts_count=active_alerts)


@app.get("/api/timeseries", response_model=List[TimeSeriesBucket])
def get_timeseries_metrics() -> List[TimeSeriesBucket]:
    """Returns daily time-series buckets for charts (pass rate, cost, p95 latency, failure counts)."""
    return _CACHED_TIMESERIES


@app.get("/api/alerts", response_model=List[ProductionAlert])
def get_alerts(active_only: bool = False) -> List[ProductionAlert]:
    """Returns active or all production alerts."""
    if active_only:
        return ALERT_ENGINE.get_active_alerts()
    return ALERT_ENGINE.alerts


@app.post("/api/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: str) -> dict:
    """Acknowledges an active production alert."""
    success = ALERT_ENGINE.acknowledge_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert ID not found")
    return {"status": "SUCCESS", "alert_id": alert_id, "message": "Alert marked as ACKNOWLEDGED"}


@app.get("/api/decay-audit", response_model=SilentDecayReport)
def get_silent_decay_audit() -> SilentDecayReport:
    """Runs statistical drift detector comparing historical baseline to recent window."""
    return MetricsAggregator.detect_silent_quality_decay(_CACHED_TRACES)


@app.get("/api/traces", response_model=List[Trace])
def list_traces(
    limit: int = Query(50, ge=1, le=200),
    failure_category: Optional[str] = None,
    search: Optional[str] = None,
) -> List[Trace]:
    """Filterable trace explorer returning latest multi-span execution records."""
    filtered = list(_CACHED_TRACES)
    filtered.sort(key=lambda t: t.timestamp, reverse=True)

    if failure_category and failure_category.upper() != "ALL":
        filtered = [t for t in filtered if t.failure_category.value == failure_category.upper()]

    if search:
        s_lower = search.lower()
        filtered = [t for t in filtered if s_lower in t.query.lower() or s_lower in t.trace_id.lower()]

    return filtered[:limit]


@app.get("/api/traces/{trace_id}", response_model=Trace)
def get_trace_detail(trace_id: str) -> Trace:
    """Returns detailed trace record with complete span execution tree."""
    trace = TRACER.traces.get(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace ID not found")
    return trace


class FeedbackRequest(BaseModel):
    trace_id: str
    rating: int = Field(ge=1, le=5, default=5)
    thumbs_up: bool
    comment: Optional[str] = None


@app.post("/api/feedback", response_model=UserFeedback)
def submit_user_feedback(req: FeedbackRequest) -> UserFeedback:
    """Attaches human feedback to a trace for groundedness and quality calibration."""
    if req.trace_id not in TRACER.traces:
        raise HTTPException(status_code=404, detail="Trace ID not found")

    feedback = TRACER.record_feedback(
        trace_id=req.trace_id,
        rating=req.rating,
        thumbs_up=req.thumbs_up,
        comment=req.comment,
    )
    return feedback


# Mount static directory for modern glassmorphic dashboard
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
def serve_dashboard_root() -> FileResponse:
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    raise HTTPException(status_code=404, detail="Dashboard UI not compiled.")
