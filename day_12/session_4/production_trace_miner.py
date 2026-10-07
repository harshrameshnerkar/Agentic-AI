"""
Day 12 - Session 4: Production Trace Miner & Distillation Dataset Extractor
===========================================================================
Implements:
  1. Ingestion of raw production traces (Prompts, Tool Outputs, Latencies, Eval Scores)
  2. Multi-tier quality curation (Filtering failed turns, retries, and negative user feedback)
  3. PII & Secret Redaction (Sanitizing tokens, IP addresses, credentials)
  4. Transformation into instruction-response distillation pairs for the Small Model
  5. Statistical yield scorecard (Raw Traces -> Verified Pristine Distillation Pairs)
"""

import os
import sys
import re
import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class ProductionTrace:
    trace_id: str
    timestamp: str
    user_query: str
    operator_role: str
    teacher_response: str
    tools_executed: List[str]
    tool_status: str              # "SUCCESS" | "FAILED" | "TIMEOUT"
    user_feedback_score: float   # 0.0 to 1.0 (thumbs down = 0.0, thumbs up = 1.0)
    evaluator_rubric_pass: bool  # Automated post-execution guardrail verification
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int


@dataclass
class DistillationMiningSummary:
    total_raw_traces: int
    failed_tool_traces_pruned: int
    low_feedback_traces_pruned: int
    evaluator_rejections_pruned: int
    pii_redactions_applied: int
    final_distilled_pairs: int
    mining_yield_pct: float


class ProductionTraceMiner:
    """Extracts, sanitizes, and prepares high-fidelity distillation training datasets from live traces."""

    PII_REGEX = {
        "EMAIL": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
        "IPV4": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
        "AUTH_TOKEN": r"AUTH-[A-Z0-9_-]{8,32}",
        "API_KEY": r"(?:sk-|AQ\.)[a-zA-Z0-9_-]{24,64}",
    }

    def __init__(self, min_feedback_score: float = 0.85):
        self.min_feedback_score = min_feedback_score

    def sanitize_text(self, text: str) -> Tuple[str, int]:
        """Redacts sensitive PII, internal tokens, and customer secrets."""
        redactions = 0
        cleaned = text

        for label, pattern in self.PII_REGEX.items():
            matches = re.findall(pattern, cleaned)
            if matches:
                redactions += len(matches)
                cleaned = re.sub(pattern, f"[{label}_REDACTED]", cleaned)

        return cleaned, redactions

    def mine_traces(self, traces: List[ProductionTrace]) -> Tuple[List[Dict[str, Any]], DistillationMiningSummary]:
        """Filters raw production logs and yields pristine student distillation pairs."""
        distilled_pairs: List[Dict[str, Any]] = []

        failed_tools_cnt = 0
        low_feedback_cnt = 0
        evaluator_reject_cnt = 0
        total_pii_redacted = 0

        for t in traces:
            # Gate 1: Tool execution failure check
            if t.tool_status != "SUCCESS":
                failed_tools_cnt += 1
                continue

            # Gate 2: Human operator thumbs-up / feedback score threshold
            if t.user_feedback_score < self.min_feedback_score:
                low_feedback_cnt += 1
                continue

            # Gate 3: Automated eval rubric verification
            if not t.evaluator_rubric_pass:
                evaluator_reject_cnt += 1
                continue

            # Gate 4: PII Redaction
            clean_query, r1 = self.sanitize_text(t.user_query)
            clean_resp, r2 = self.sanitize_text(t.teacher_response)
            total_pii_redacted += (r1 + r2)

            # Build Standard Chat Distillation Sample
            distillation_sample = {
                "trace_id": t.trace_id,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are OpsSentinel AI, an Autonomous SRE Incident Response Assistant. "
                            "Given an incident alert, formulate a deterministic JSON TriageActionPlan."
                        ),
                    },
                    {"role": "user", "content": clean_query},
                    {"role": "assistant", "content": clean_resp},
                ],
                "metadata": {
                    "source": "production_trace_mining",
                    "original_latency_ms": t.latency_ms,
                    "teacher_tokens": t.prompt_tokens + t.completion_tokens,
                },
            }
            distilled_pairs.append(distillation_sample)

        total_raw = len(traces)
        final_cnt = len(distilled_pairs)
        yield_pct = (final_cnt / max(1, total_raw)) * 100.0

        summary = DistillationMiningSummary(
            total_raw_traces=total_raw,
            failed_tool_traces_pruned=failed_tools_cnt,
            low_feedback_traces_pruned=low_feedback_cnt,
            evaluator_rejections_pruned=evaluator_reject_cnt,
            pii_redactions_applied=total_pii_redacted,
            final_distilled_pairs=final_cnt,
            mining_yield_pct=round(yield_pct, 1),
        )

        return distilled_pairs, summary


def generate_synthetic_production_traces(count: int = 50) -> List[ProductionTrace]:
    """Generates realistic production telemetry traces to demonstrate trace mining."""
    traces = []
    services = ["payment-api", "auth-service", "postgres-primary", "nginx-ingress", "redis-cluster"]
    severities = ["SEV-1", "SEV-2", "SEV-3"]
    tools = ["query_telemetry_db", "read_system_logs", "search_runbooks", "restart_service", "calculate_metrics"]

    for i in range(1, count + 1):
        svc = services[i % len(services)]
        sev = severities[i % len(severities)]
        tool = tools[i % len(tools)]

        # Simulate natural noise in live production logs:
        # ~10% tool execution failures, ~14% low feedback scores, ~8% rubric failures
        tool_status = "FAILED" if (i % 10 == 0) else "SUCCESS"
        feedback = 0.4 if (i % 7 == 0) else (0.95 if i % 2 == 0 else 1.0)
        rubric_pass = False if (i % 12 == 0) else True

        # Synthesize realistic action plan JSON
        action_plan = {
            "severity": sev,
            "affected_service": svc,
            "category": "APPLICATION" if "api" in svc else ("DATABASE" if "postgres" in svc or "redis" in svc else "NETWORK_INGRESS"),
            "root_cause_hypothesis": f"Detected operational anomaly on {svc} during routine load window.",
            "proposed_tool": tool,
            "tool_parameters": {"service_id": svc, "limit": 10},
            "blast_radius": "HIGH" if tool == "restart_service" else "LOW",
            "requires_approval": tool == "restart_service",
            "remediation_steps": [f"Query telemetry on {svc}", f"Execute {tool}"],
            "runbook_citation": f"RUNBOOK-0{(i % 8) + 1}",
        }

        trace = ProductionTrace(
            trace_id=f"TRACE-PROD-{i:04d}",
            timestamp=f"2026-10-06T12:{i % 60:02d}:00Z",
            user_query=f"Investigate high error rate on {svc} reported by user alice@ops.internal from IP 192.168.1.{i % 255}.",
            operator_role="Admin" if i % 3 == 0 else "Engineer",
            teacher_response=json.dumps(action_plan, indent=2),
            tools_executed=[tool],
            tool_status=tool_status,
            user_feedback_score=feedback,
            evaluator_rubric_pass=rubric_pass,
            latency_ms=740.0 + (i % 15) * 20.0,
            prompt_tokens=65 + (i % 10),
            completion_tokens=180 + (i % 15),
        )
        traces.append(trace)

    return traces
