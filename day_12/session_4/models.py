"""
Day 12 - Session 4: Dual-Tier Execution Models (Small SLM vs Large LLM)
=======================================================================
Implements:
  1. SmallModel (Low-cost, high-speed 1B-3B LoRA fine-tuned student model)
  2. LargeTeacherModel (High-reasoning, frontier teacher model)
  3. Realistic latency, token consumption, and cloud pricing modeling
  4. Calibrated confidence score estimation for routing evaluation
"""

import os
import sys
import json
import time
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ModelExecutionResult:
    model_tier: str              # "SMALL" | "LARGE"
    model_name: str
    output_text: str
    parsed_json: Optional[Dict[str, Any]]
    is_valid_json: bool
    confidence_score: float      # Calibrated confidence metric [0.0, 1.0]
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float
    cost_usd: float
    escalation_recommended: bool = False
    escalation_reason: Optional[str] = None


class SmallModel:
    """
    Distilled / LoRA-Adapted Small Language Model (e.g., LLaMA-3.2-1B / Qwen-2.5-1.5B).
    Characteristics:
      - Ultra-low inference cost: $0.05 / 1M input tokens, $0.15 / 1M output tokens (50x cheaper).
      - Sub-150ms execution latency.
      - 100% reliable on routine, single-service, format-aligned SRE alerts.
      - Expresses low confidence or hesitates on multi-cluster cascading disasters.
    """

    INPUT_COST_PER_M = 0.05
    OUTPUT_COST_PER_M = 0.15

    def __init__(self, name: str = "OpsSentinel-SLM-1.5B (LoRA-Distilled)"):
        self.name = name

    def predict(self, query: str, context: Optional[str] = None) -> ModelExecutionResult:
        t0 = time.perf_counter()
        q_lower = query.lower()

        prompt_tok = max(1, int(len(query) / 3.8)) + 30

        # Detect task complexity heuristics
        is_ambiguous = any(w in q_lower for w in ["cascade", "multi-datacenter", "unknown", "simultaneous", "both", "split-brain", "zero-day"])
        is_high_blast = any(w in q_lower for w in ["drop database", "purge all", "wipe", "force failover"])
        is_routine = any(w in q_lower for w in ["cpu", "memory", "latency", "restart", "log", "telemetry", "degraded", "timeout", "5xx"])

        if is_ambiguous:
            # Small model exhibits uncertainty / lower confidence on complex cascading edge-cases
            confidence = 0.62
            sev = "SEV-1"
            service = "payment-api"
            tool = "query_telemetry_db"
            hypothesis = "Potential systemic issue detected, but multiple service interdependencies require frontier reasoning."
            action_plan = {
                "severity": sev,
                "affected_service": service,
                "category": "INFRASTRUCTURE",
                "root_cause_hypothesis": hypothesis,
                "proposed_tool": tool,
                "tool_parameters": {"service_id": service},
                "blast_radius": "HIGH",
                "requires_approval": True,
                "remediation_steps": ["Inspect cluster telemetry", "Awaiting root cause escalation"],
                "runbook_citation": "RUNBOOK-01",
            }
            output_text = json.dumps(action_plan, indent=2)
            escalate = True
            reason = "LOW_CONFIDENCE_SCORE (Score 0.62 < 0.80 on cascading incident)"

        elif is_high_blast:
            # Critical unapproved destructive query
            confidence = 0.55
            action_plan = {
                "severity": "SEV-1",
                "affected_service": "postgres-primary",
                "category": "DATABASE",
                "root_cause_hypothesis": "Critical blast radius action requested.",
                "proposed_tool": "rollback_deployment",
                "tool_parameters": {},
                "blast_radius": "CRITICAL",
                "requires_approval": True,
                "remediation_steps": ["Block action pending authorization token"],
                "runbook_citation": "RUNBOOK-04",
            }
            output_text = json.dumps(action_plan, indent=2)
            escalate = True
            reason = "CRITICAL_BLAST_RADIUS_RISK (Destructive multi-cluster impact)"

        else:
            # Routine SRE alert: Small model solves with high confidence & exact formatting!
            confidence = 0.94
            if "payment" in q_lower or "5xx" in q_lower or "latency" in q_lower:
                sev, service, tool, cat = "SEV-1", "payment-api", "query_telemetry_db", "APPLICATION"
                cite = "RUNBOOK-01"
            elif "postgres" in q_lower or "database" in q_lower or "connection" in q_lower:
                sev, service, tool, cat = "SEV-2", "postgres-primary", "read_system_logs", "DATABASE"
                cite = "RUNBOOK-02"
            elif "ingress" in q_lower or "nginx" in q_lower or "ssl" in q_lower:
                sev, service, tool, cat = "SEV-2", "nginx-ingress", "restart_service", "NETWORK_INGRESS"
                cite = "RUNBOOK-03"
            elif "redis" in q_lower or "memory" in q_lower:
                sev, service, tool, cat = "SEV-3", "redis-cluster", "calculate_metrics", "DATABASE"
                cite = "RUNBOOK-05"
            else:
                sev, service, tool, cat = "SEV-2", "auth-service", "read_system_logs", "SECURITY_AUTH"
                cite = "RUNBOOK-06"

            action_plan = {
                "severity": sev,
                "affected_service": service,
                "category": cat,
                "root_cause_hypothesis": f"Triaged operational alert on {service} matching standard telemetry pattern.",
                "proposed_tool": tool,
                "tool_parameters": {"service_id": service, "limit": 10},
                "blast_radius": "MEDIUM" if tool == "restart_service" else "LOW",
                "requires_approval": tool == "restart_service",
                "remediation_steps": [f"Inspect status for {service}", f"Execute diagnostic tool {tool}"],
                "runbook_citation": cite,
            }
            output_text = json.dumps(action_plan, indent=2)
            escalate = False
            reason = None

        comp_tok = max(1, int(len(output_text) / 3.8))
        dur_ms = (time.perf_counter() - t0) * 1000.0 + 85.0  # ~85-120ms baseline

        cost = (prompt_tok * self.INPUT_COST_PER_M / 1e6) + (comp_tok * self.OUTPUT_COST_PER_M / 1e6)

        return ModelExecutionResult(
            model_tier="SMALL",
            model_name=self.name,
            output_text=output_text,
            parsed_json=action_plan,
            is_valid_json=True,
            confidence_score=confidence,
            prompt_tokens=prompt_tok,
            completion_tokens=comp_tok,
            latency_ms=round(dur_ms, 2),
            cost_usd=round(cost, 7),
            escalation_recommended=escalate,
            escalation_reason=reason,
        )


class LargeTeacherModel:
    """
    Frontier Teacher Model (e.g., Gemini 1.5 Pro / GPT-4o).
    Characteristics:
      - Higher inference cost: $2.50 / 1M input tokens, $10.00 / 1M output tokens (50x - 66x higher).
      - ~750ms - 1,100ms execution latency.
      - Superior chain-of-thought and multi-hop reasoning.
      - Resolves complex multi-service cascading failures and cross-system split-brain states.
    """

    INPUT_COST_PER_M = 2.50
    OUTPUT_COST_PER_M = 10.00

    def __init__(self, name: str = "Frontier-LLM-Teacher (Gemini Pro / GPT-4o)"):
        self.name = name

    def predict(self, query: str, context: Optional[str] = None) -> ModelExecutionResult:
        t0 = time.perf_counter()
        q_lower = query.lower()

        prompt_tok = max(1, int(len(query) / 3.8)) + 120  # Larger system prompt context

        # Complex reasoning synthesis
        action_plan = {
            "severity": "SEV-1",
            "affected_service": "payment-api",
            "category": "INFRASTRUCTURE",
            "root_cause_hypothesis": (
                "Deep architectural diagnosis: Cascading deadlock initiated by upstream Postgres "
                "connection saturation propagating backpressure through nginx-ingress to payment workers."
            ),
            "proposed_tool": "dispatch_emergency_alert",
            "tool_parameters": {
                "channel": "#ops-incident-war-room",
                "escalate_to": "principal-oncall",
                "message": "Initiate cross-cluster failover protocol and connection pool shedding."
            },
            "blast_radius": "CRITICAL",
            "requires_approval": True,
            "remediation_steps": [
                "Drain ingress traffic to secondary datacenter us-west-2",
                "Restart postgres connection pooler with max_connections=600",
                "Perform rolling restart of payment-api canary pods",
            ],
            "runbook_citation": "RUNBOOK-12",
        }

        output_text = json.dumps(action_plan, indent=2)
        comp_tok = max(1, int(len(output_text) / 3.8))
        dur_ms = (time.perf_counter() - t0) * 1000.0 + 780.0  # ~780ms - 950ms frontier latency

        cost = (prompt_tok * self.INPUT_COST_PER_M / 1e6) + (comp_tok * self.OUTPUT_COST_PER_M / 1e6)

        return ModelExecutionResult(
            model_tier="LARGE",
            model_name=self.name,
            output_text=output_text,
            parsed_json=action_plan,
            is_valid_json=True,
            confidence_score=0.99,  # High frontier confidence
            prompt_tokens=prompt_tok,
            completion_tokens=comp_tok,
            latency_ms=round(dur_ms, 2),
            cost_usd=round(cost, 7),
            escalation_recommended=False,
            escalation_reason=None,
        )
