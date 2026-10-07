"""
Langfuse / LangSmith Style Tracing Engine for Agentic Telemetry.
Manages trace and span lifecycles, groundedness audits, and user feedback attachment.
"""

import json
import uuid
import datetime
from typing import Dict, List, Optional, Any
from day_14.session_3.models import (
    Trace,
    Span,
    SpanType,
    FailureCategory,
    GroundednessScore,
    UserFeedback,
    LLMUsage,
)
from day_14.session_3.pricing_engine import ModelPricingEngine


class ProductionTracer:
    """
    In-memory trace collector and lifecycle manager.
    Can export/import from JSON for persistent analysis.
    """

    def __init__(self) -> None:
        self.traces: Dict[str, Trace] = {}
        self.active_spans: Dict[str, Span] = {}

    def start_trace(
        self,
        query: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        model_used: str = "claude-3-5-sonnet",
        timestamp: Optional[datetime.datetime] = None,
    ) -> Trace:
        trace_id = f"TRC-{uuid.uuid4().hex[:8].upper()}"
        now = timestamp or datetime.datetime.now(datetime.timezone.utc)
        trace = Trace(
            trace_id=trace_id,
            session_id=session_id or f"SESS-{uuid.uuid4().hex[:6]}",
            user_id=user_id or "user_production",
            timestamp=now,
            query=query,
            response="",
            latency_ms=0.0,
            status="SUCCESS",
            failure_category=FailureCategory.NONE,
            cost_usd=0.0,
            model_used=model_used,
            prompt_tokens=0,
            completion_tokens=0,
            spans=[],
            metadata=metadata or {},
        )
        self.traces[trace_id] = trace
        return trace

    def start_span(
        self,
        trace_id: str,
        name: str,
        span_type: SpanType,
        parent_span_id: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        start_time: Optional[datetime.datetime] = None,
    ) -> Span:
        if trace_id not in self.traces:
            raise KeyError(f"Trace ID {trace_id} does not exist.")

        span_id = f"SPAN-{uuid.uuid4().hex[:8].upper()}"
        now = start_time or datetime.datetime.now(datetime.timezone.utc)
        span = Span(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            name=name,
            span_type=span_type,
            start_time=now,
            end_time=now,
            latency_ms=0.0,
            status="SUCCESS",
            input_data=input_data or {},
            output_data={},
        )
        self.active_spans[span_id] = span
        return span

    def end_span(
        self,
        span_id: str,
        output_data: Optional[Dict[str, Any]] = None,
        status: str = "SUCCESS",
        error_message: Optional[str] = None,
        usage: Optional[LLMUsage] = None,
        end_time: Optional[datetime.datetime] = None,
    ) -> Span:
        if span_id not in self.active_spans:
            raise KeyError(f"Span ID {span_id} is not active.")

        span = self.active_spans.pop(span_id)
        now = end_time or datetime.datetime.now(datetime.timezone.utc)
        span.end_time = now
        span.latency_ms = max(0.1, (span.end_time - span.start_time).total_seconds() * 1000.0)
        span.status = status
        span.error_message = error_message
        span.output_data = output_data or {}
        span.usage = usage

        # Append span to parent trace
        trace = self.traces[span.trace_id]
        trace.spans.append(span)

        # Accumulate usage to trace
        if usage:
            trace.prompt_tokens += usage.prompt_tokens
            trace.completion_tokens += usage.completion_tokens
            trace.cost_usd = round(trace.cost_usd + usage.estimated_cost_usd, 6)

        return span

    def log_llm_call(
        self,
        trace_id: str,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        prompt_text: str,
        completion_text: str,
        latency_ms: float,
        start_time: Optional[datetime.datetime] = None,
        end_time: Optional[datetime.datetime] = None,
    ) -> Span:
        """Helper to create and end an LLM call span in one step."""
        now = start_time or datetime.datetime.now(datetime.timezone.utc)
        finish = end_time or (now + datetime.timedelta(milliseconds=latency_ms))
        cost = ModelPricingEngine.calculate_cost(model_name, prompt_tokens, completion_tokens)
        usage = LLMUsage(
            model_name=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            estimated_cost_usd=cost,
        )

        span = self.start_span(
            trace_id=trace_id,
            name=f"LLM_Inference_{model_name}",
            span_type=SpanType.LLM_CALL,
            input_data={"prompt": prompt_text[:200]},
            start_time=now,
        )
        return self.end_span(
            span_id=span.span_id,
            output_data={"completion": completion_text[:200]},
            usage=usage,
            end_time=finish,
        )

    def log_tool_call(
        self,
        trace_id: str,
        tool_name: str,
        tool_args: Dict[str, Any],
        tool_result: Dict[str, Any],
        latency_ms: float,
        is_error: bool = False,
        error_msg: Optional[str] = None,
    ) -> Span:
        """Helper to record tool execution span."""
        span = self.start_span(
            trace_id=trace_id,
            name=f"tool::{tool_name}",
            span_type=SpanType.TOOL_EXECUTION,
            input_data=tool_args,
        )
        return self.end_span(
            span_id=span.span_id,
            output_data=tool_result,
            status="ERROR" if is_error else "SUCCESS",
            error_message=error_msg,
        )

    def evaluate_groundedness(
        self,
        trace_id: str,
        retrieved_contexts: List[str],
        generated_response: str,
    ) -> GroundednessScore:
        """
        Groundedness and Hallucination Auditor:
        Evaluates token overlap and claim support against retrieved documents.
        """
        if not retrieved_contexts:
            score = GroundednessScore(
                score=1.0,
                verified_claims=1,
                total_claims=1,
                ungrounded_claims=0,
                hallucination_detected=False,
                context_overlap_ratio=1.0,
                rationale="Direct response, no context retrieval required.",
            )
            if trace_id in self.traces:
                self.traces[trace_id].groundedness = score
            return score

        # Aggregate context tokens
        context_corpus = " ".join(retrieved_contexts).lower()
        context_words = set(w.strip(".,;:?!()[]{}\"'") for w in context_corpus.split() if len(w) > 0)

        # Response words
        resp_words = [w.strip(".,;:?!()[]{}\"'") for w in generated_response.lower().split() if len(w) > 3]
        if not resp_words:
            overlap = 1.0
        else:
            supported = [w for w in resp_words if w in context_words]
            overlap = len(supported) / len(resp_words)

        is_hallucinating = overlap < 0.65
        claims_total = max(1, len(resp_words) // 5)
        ungrounded = int(claims_total * (1.0 - overlap)) if is_hallucinating else 0
        verified = claims_total - ungrounded

        score = GroundednessScore(
            score=round(overlap, 3),
            verified_claims=verified,
            total_claims=claims_total,
            ungrounded_claims=ungrounded,
            hallucination_detected=is_hallucinating,
            context_overlap_ratio=round(overlap, 3),
            rationale=(
                "Hallucination detected: Response introduces entities not found in context."
                if is_hallucinating
                else "Response claims are strongly supported by retrieved context."
            ),
        )

        if trace_id in self.traces:
            self.traces[trace_id].groundedness = score
            if is_hallucinating and self.traces[trace_id].failure_category == FailureCategory.NONE:
                self.traces[trace_id].failure_category = FailureCategory.HALLUCINATION
                self.traces[trace_id].status = "FAILURE"

        return score

    def record_feedback(
        self,
        trace_id: str,
        rating: int,
        thumbs_up: bool,
        comment: Optional[str] = None,
        user_escalated_to_hitl: bool = False,
        user_retried_within_30s: bool = False,
    ) -> UserFeedback:
        """Captures explicit and implicit user feedback for a trace."""
        if trace_id not in self.traces:
            raise KeyError(f"Trace ID {trace_id} does not exist.")

        feedback = UserFeedback(
            feedback_id=f"FB-{uuid.uuid4().hex[:8].upper()}",
            trace_id=trace_id,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            rating=rating,
            thumbs_up=thumbs_up,
            comment=comment,
            user_escalated_to_hitl=user_escalated_to_hitl,
            user_retried_within_30s=user_retried_within_30s,
        )
        self.traces[trace_id].feedback = feedback
        return feedback

    def end_trace(
        self,
        trace_id: str,
        response: str,
        status: str = "SUCCESS",
        failure_category: FailureCategory = FailureCategory.NONE,
        latency_ms: Optional[float] = None,
    ) -> Trace:
        """Finalizes an agent trace."""
        if trace_id not in self.traces:
            raise KeyError(f"Trace ID {trace_id} does not exist.")

        trace = self.traces[trace_id]
        trace.response = response
        trace.status = status
        trace.failure_category = failure_category

        if latency_ms is not None:
            trace.latency_ms = latency_ms
        else:
            # Sum up span latencies if present, or compute from time
            if trace.spans:
                trace.latency_ms = sum(s.latency_ms for s in trace.spans)
            else:
                trace.latency_ms = 120.0

        return trace

    def export_traces_json(self, file_path: str) -> None:
        """Serializes all traces to a JSON file."""
        data = [t.model_dump(mode="json") for t in self.traces.values()]
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def load_traces_json(self, file_path: str) -> List[Trace]:
        """Loads traces from a serialized JSON file."""
        with open(file_path, "r", encoding="utf-8") as f:
            raw_list = json.load(f)

        self.traces.clear()
        for item in raw_list:
            trace = Trace.model_validate(item)
            self.traces[trace.trace_id] = trace
        return list(self.traces.values())
