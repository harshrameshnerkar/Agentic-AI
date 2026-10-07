"""
Production Telemetry Trace Simulator.
Generates 14 days of multi-span agent execution traces (1,200+ traces)
demonstrating baseline health, silent quality decay, incident spike, and recovery.
"""

import random
import datetime
from typing import List
from day_14.session_3.models import (
    Trace,
    FailureCategory,
    GroundednessScore,
    UserFeedback,
    LLMUsage,
    Span,
    SpanType,
)
from day_14.session_3.pricing_engine import ModelPricingEngine


class ProductionTraceSimulator:
    INCIDENT_QUERIES = [
        "Inspect telemetry metrics for checkout-api pod payment-core-01",
        "Restart degraded deployment pod inventory-sync-worker",
        "Query slow query logs for PostgreSQL customer-db primary",
        "Inspect Nginx ingress controller for 502 Bad Gateway bursts",
        "Analyze memory spike on Redis cluster shard-3",
        "Drain Kubernetes node worker-compute-04 for OS patch",
        "Validate TLS certificate expiration date on api.gateway.prod",
        "Investigate deadlock on billing_transactions table",
        "Fetch top 10 error traces from OpenTelemetry collector",
        "Rotate compromised service account credentials for analytics-job",
    ]

    MODELS = ["claude-3-5-sonnet", "claude-3-haiku", "gpt-4o", "gpt-4o-mini"]

    @classmethod
    def generate_14_day_telemetry(
        cls,
        traces_per_day: int = 80,
        start_date: datetime.datetime = datetime.datetime(2026, 9, 20, 0, 0, 0, tzinfo=datetime.timezone.utc),
        seed: int = 42,
    ) -> List[Trace]:
        random.seed(seed)
        all_traces: List[Trace] = []

        for day_offset in range(14):
            current_day = start_date + datetime.timedelta(days=day_offset)

            # Determine operational phase for the day
            if day_offset < 7:
                phase = "HEALTHY_BASELINE"
            elif day_offset in (7, 8):
                phase = "SILENT_QUALITY_DECAY"
            elif day_offset == 9:
                phase = "ACUTE_INCIDENT_SPIKE"
            else:
                phase = "RECOVERY_AND_STABILIZED"

            for i in range(traces_per_day):
                timestamp = current_day + datetime.timedelta(
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59),
                    seconds=random.randint(0, 59),
                )
                query = random.choice(cls.INCIDENT_QUERIES)
                trace_id = f"TRC-D{day_offset+1:02d}-{i+1:03d}"
                session_id = f"SESS-{random.randint(1000, 9999)}"
                user_id = f"sre_eng_{random.randint(1, 15)}@acme.corp"

                # Phase-dependent parameters
                if phase == "HEALTHY_BASELINE":
                    is_success = random.random() < 0.96
                    latency_base = random.gauss(650.0, 110.0)
                    prompt_toks = random.randint(700, 1100)
                    compl_toks = random.randint(200, 400)
                    groundedness_val = round(min(1.0, random.gauss(0.95, 0.03)), 3)
                    hallucinating = False
                    model = "claude-3-5-sonnet"
                    thumbs_up = random.random() < 0.93

                elif phase == "SILENT_QUALITY_DECAY":
                    # Silent decay: pass rate slips slightly, token inflation (+40%), groundedness drops, p95 creeps up
                    is_success = random.random() < 0.89
                    latency_base = random.gauss(1100.0, 200.0)
                    prompt_toks = random.randint(1100, 1700)  # Prompt inflation
                    compl_toks = random.randint(450, 800)  # Verbose completion
                    groundedness_val = round(max(0.65, min(0.88, random.gauss(0.79, 0.05))), 3)
                    hallucinating = groundedness_val < 0.70
                    model = "claude-3-5-sonnet"
                    thumbs_up = random.random() < 0.75

                elif phase == "ACUTE_INCIDENT_SPIKE":
                    # Acute incident: 502s, database timeouts, severe failure spike
                    is_success = random.random() < 0.74
                    latency_base = random.gauss(2100.0, 600.0)
                    prompt_toks = random.randint(900, 1400)
                    compl_toks = random.randint(150, 350)
                    groundedness_val = round(max(0.60, min(0.92, random.gauss(0.82, 0.09))), 3)
                    hallucinating = groundedness_val < 0.65
                    model = "claude-3-5-sonnet"
                    thumbs_up = random.random() < 0.55

                else:  # RECOVERY_AND_STABILIZED
                    is_success = random.random() < 0.97
                    latency_base = random.gauss(620.0, 95.0)
                    prompt_toks = random.randint(650, 950)
                    compl_toks = random.randint(180, 350)
                    groundedness_val = round(min(1.0, random.gauss(0.96, 0.02)), 3)
                    hallucinating = False
                    model = "claude-3-5-sonnet"
                    thumbs_up = random.random() < 0.95

                total_latency = max(120.0, latency_base)
                cost = ModelPricingEngine.calculate_cost(model, prompt_toks, compl_toks)

                # Determine failure category
                if is_success:
                    status = "SUCCESS"
                    fail_cat = FailureCategory.NONE
                    resp_text = f"Action successfully executed: verified state for query '{query}'."
                else:
                    status = "FAILURE"
                    if hallucinating:
                        fail_cat = FailureCategory.HALLUCINATION
                        resp_text = "Failed: Hallucinated nonexistent service dependency 'payment-v3-legacy'."
                    elif phase == "ACUTE_INCIDENT_SPIKE":
                        fail_cat = random.choice([
                            FailureCategory.TIMEOUT,
                            FailureCategory.TOOL_FAILURE,
                            FailureCategory.RATE_LIMIT_ERROR,
                        ])
                        resp_text = f"Execution failed due to downstream {fail_cat.value}."
                    else:
                        fail_cat = random.choice([
                            FailureCategory.TOOL_FAILURE,
                            FailureCategory.UNAUTHORIZED_DESTRUCTIVE_ACTION,
                            FailureCategory.SCHEMA_PARSE_ERROR,
                        ])
                        resp_text = f"Execution halted due to {fail_cat.value}."

                # Construct realistic spans
                llm_span_id = f"SPAN-{trace_id}-LLM"
                tool_span_id = f"SPAN-{trace_id}-TOOL"

                spans = [
                    Span(
                        span_id=llm_span_id,
                        trace_id=trace_id,
                        name=f"LLM_Inference_{model}",
                        span_type=SpanType.LLM_CALL,
                        start_time=timestamp,
                        end_time=timestamp + datetime.timedelta(milliseconds=total_latency * 0.65),
                        latency_ms=round(total_latency * 0.65, 2),
                        status="SUCCESS",
                        usage=LLMUsage(
                            model_name=model,
                            prompt_tokens=prompt_toks,
                            completion_tokens=compl_toks,
                            total_tokens=prompt_toks + compl_toks,
                            estimated_cost_usd=cost,
                        ),
                    ),
                    Span(
                        span_id=tool_span_id,
                        trace_id=trace_id,
                        name="tool::execute_telemetry_action",
                        span_type=SpanType.TOOL_EXECUTION,
                        start_time=timestamp + datetime.timedelta(milliseconds=total_latency * 0.65),
                        end_time=timestamp + datetime.timedelta(milliseconds=total_latency),
                        latency_ms=round(total_latency * 0.35, 2),
                        status="ERROR" if not is_success else "SUCCESS",
                        error_message=resp_text if not is_success else None,
                    ),
                ]

                # Feedback model
                feedback = UserFeedback(
                    feedback_id=f"FB-{trace_id}",
                    trace_id=trace_id,
                    timestamp=timestamp + datetime.timedelta(minutes=2),
                    rating=5 if thumbs_up else 2,
                    thumbs_up=thumbs_up,
                    comment="Accurate remediation" if thumbs_up else "Failed to diagnose root cause properly",
                    user_escalated_to_hitl=not is_success and random.random() < 0.6,
                    user_retried_within_30s=not is_success and random.random() < 0.4,
                )

                trace = Trace(
                    trace_id=trace_id,
                    session_id=session_id,
                    user_id=user_id,
                    timestamp=timestamp,
                    query=query,
                    response=resp_text,
                    latency_ms=round(total_latency, 2),
                    status=status,
                    failure_category=fail_cat,
                    cost_usd=cost,
                    model_used=model,
                    prompt_tokens=prompt_toks,
                    completion_tokens=compl_toks,
                    spans=spans,
                    groundedness=GroundednessScore(
                        score=groundedness_val,
                        verified_claims=4 if not hallucinating else 2,
                        total_claims=4,
                        ungrounded_claims=0 if not hallucinating else 2,
                        hallucination_detected=hallucinating,
                        context_overlap_ratio=groundedness_val,
                        rationale="Normal context match" if not hallucinating else "Contradicts retrieved context",
                    ),
                    feedback=feedback,
                    metadata={"phase": phase, "environment": "production-us-east-1"},
                )
                all_traces.append(trace)

        return all_traces
