"""
Pydantic Models and Data Schemas for Production Telemetry & Monitoring.
Conforms to OpenTelemetry / Langfuse / LangSmith span and trace specifications.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import datetime


class SpanType(str, Enum):
    TRACE = "TRACE"
    LLM_CALL = "LLM_CALL"
    TOOL_EXECUTION = "TOOL_EXECUTION"
    RETRIEVAL = "RETRIEVAL"
    GUARDRAIL = "GUARDRAIL"


class FailureCategory(str, Enum):
    NONE = "NONE"
    TIMEOUT = "TIMEOUT"
    TOOL_FAILURE = "TOOL_FAILURE"
    HALLUCINATION = "HALLUCINATION"
    UNGROUNDED_CLAIM = "UNGROUNDED_CLAIM"
    SCHEMA_PARSE_ERROR = "SCHEMA_PARSE_ERROR"
    UNAUTHORIZED_DESTRUCTIVE_ACTION = "UNAUTHORIZED_DESTRUCTIVE_ACTION"
    TOKEN_LIMIT_EXCEEDED = "TOKEN_LIMIT_EXCEEDED"
    RATE_LIMIT_ERROR = "RATE_LIMIT_ERROR"


class AlertSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


class LLMUsage(BaseModel):
    model_name: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0


class GroundednessScore(BaseModel):
    score: float = Field(default=1.0, ge=0.0, le=1.0)
    verified_claims: int = 0
    total_claims: int = 0
    ungrounded_claims: int = 0
    hallucination_detected: bool = False
    context_overlap_ratio: float = 1.0
    rationale: str = "Fully grounded in retrieved context."


class UserFeedback(BaseModel):
    feedback_id: str
    trace_id: str
    timestamp: datetime.datetime
    rating: int = Field(ge=1, le=5, default=5)  # 1 (terrible) to 5 (excellent)
    thumbs_up: bool = True
    comment: Optional[str] = None
    user_escalated_to_hitl: bool = False
    user_retried_within_30s: bool = False


class Span(BaseModel):
    span_id: str
    trace_id: str
    parent_span_id: Optional[str] = None
    name: str
    span_type: SpanType
    start_time: datetime.datetime
    end_time: datetime.datetime
    latency_ms: float
    status: str = "SUCCESS"  # SUCCESS or ERROR
    error_message: Optional[str] = None
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    usage: Optional[LLMUsage] = None


class Trace(BaseModel):
    trace_id: str
    session_id: str
    user_id: str
    timestamp: datetime.datetime
    query: str
    response: str
    latency_ms: float
    status: str = "SUCCESS"  # SUCCESS, DEGRADED, FAILURE
    failure_category: FailureCategory = FailureCategory.NONE
    cost_usd: float = 0.0
    model_used: str = "claude-3-5-sonnet"
    prompt_tokens: int = 0
    completion_tokens: int = 0
    spans: List[Span] = Field(default_factory=list)
    groundedness: GroundednessScore = Field(default_factory=GroundednessScore)
    feedback: Optional[UserFeedback] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TimeSeriesBucket(BaseModel):
    timestamp_bucket: str  # e.g. "2026-10-01" or "2026-10-01T14:00"
    total_traces: int
    successful_traces: int
    failed_traces: int
    pass_rate: float
    total_cost_usd: float
    avg_cost_usd: float
    p50_latency_ms: float
    p90_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    avg_groundedness: float
    hallucination_rate: float
    positive_feedback_ratio: float
    failure_category_counts: Dict[str, int]


class MetricSummary(BaseModel):
    total_traces: int
    overall_pass_rate: float
    total_cost_usd: float
    avg_cost_per_trace_usd: float
    p50_latency_ms: float
    p90_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    avg_groundedness: float
    hallucination_rate: float
    positive_feedback_ratio: float
    active_alerts_count: int
    silent_decay_detected: bool


class ProductionAlert(BaseModel):
    alert_id: str
    timestamp: datetime.datetime
    rule_name: str
    severity: AlertSeverity
    message: str
    metric_value: float
    threshold_value: float
    status: str = "ACTIVE"  # ACTIVE, ACKNOWLEDGED, RESOLVED
    runbook_url: str
