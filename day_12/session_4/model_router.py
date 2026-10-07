"""
Day 12 - Session 4: Cascading Model Router (Small First -> Escalate on Failure)
================================================================================
Implements:
  1. Speculative / Cascading Routing Architecture:
       Query -> Small Model (SLM) -> Quality & Confidence Gate -> Pass?
         [YES] -> Fast, Ultra-Low Cost Return (~100ms, $0.05/1M tokens)
         [NO]  -> Escalate to Large Teacher Model (LLM) (~850ms, $2.50/1M tokens)
  2. Multi-Tier Confidence & Failure Gates:
       - Gate 1: Strict JSON Format & Schema Integrity Check
       - Gate 2: Calibrated Confidence Threshold (tau = 0.80)
       - Gate 3: Critical Blast Radius & Operational Risk Guard
       - Gate 4: Ambiguity & Multi-System Complexity Guard
  3. Granular Telemetry & Cost Accounting per Query Turn
"""

import os
import sys
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

from models import SmallModel, LargeTeacherModel, ModelExecutionResult


@dataclass
class RoutingDecision:
    query_id: str
    query: str
    final_tier: str              # "SMALL" | "LARGE_ESCALATED"
    escalated: bool
    escalation_reason: Optional[str]
    small_confidence: float
    small_latency_ms: float
    large_latency_ms: float
    total_latency_ms: float
    total_tokens: int
    actual_cost_usd: float
    monolithic_large_cost_usd: float
    cost_savings_usd: float
    cost_savings_pct: float
    action_plan: Dict[str, Any]


class CascadingModelRouter:
    """
    Intelligent Cascading Model Router.
    Routes queries to the Small Model first, then audits confidence and schema validity.
    Escalates to the Large Teacher Model if confidence < tau or if failure occurs.
    """

    def __init__(
        self,
        confidence_threshold: float = 0.80,
        small_model: Optional[SmallModel] = None,
        large_model: Optional[LargeTeacherModel] = None,
    ):
        self.confidence_threshold = confidence_threshold
        self.small_model = small_model or SmallModel()
        self.large_model = large_model or LargeTeacherModel()
        self.routing_history: List[RoutingDecision] = []

    def evaluate_small_result(self, res: ModelExecutionResult) -> Tuple[bool, Optional[str]]:
        """
        Audits Small Model result across 4 Quality & Confidence Gates:
        Returns: (passes_gates: bool, rejection_reason: Optional[str])
        """
        # Gate 1: JSON Syntax & Structure
        if not res.is_valid_json or not res.parsed_json:
            return False, "INVALID_JSON_SYNTAX (Small model output failed parser)"

        plan = res.parsed_json

        # Gate 2: Required Schema Fields
        required_fields = ["severity", "affected_service", "proposed_tool", "runbook_citation"]
        missing = [f for f in required_fields if f not in plan or not plan[f]]
        if missing:
            return False, f"SCHEMA_INCOMPLETE (Missing required fields: {', '.join(missing)})"

        # Gate 3: Critical Blast Radius Action
        if plan.get("blast_radius") == "CRITICAL" and not plan.get("requires_approval"):
            return False, "SAFETY_VIOLATION (Critical blast radius tool without approval gate)"

        # Gate 4: Confidence Score Threshold
        if res.confidence_score < self.confidence_threshold:
            return False, (
                f"LOW_CONFIDENCE ({res.confidence_score:.2f} < {self.confidence_threshold:.2f} threshold)"
            )

        if res.escalation_recommended and res.escalation_reason:
            return False, res.escalation_reason

        return True, None

    def route_query(self, query: str, query_id: Optional[str] = None) -> RoutingDecision:
        """
        Executes cascading routing:
          1. Small Model runs first.
          2. Gates evaluate confidence & correctness.
          3. Escalate to Large Model on failure.
          4. Computes exact cost comparison against monolithic large serving.
        """
        qid = query_id or f"QRY-{len(self.routing_history) + 1:04d}"
        t_start = time.perf_counter()

        # Step 1: Small Model First
        small_res = self.small_model.predict(query)
        passes, rejection_reason = self.evaluate_small_result(small_res)

        # Baseline cost if we had blindly sent to the Large Model
        monolithic_large_prompt_tok = max(1, int(len(query) / 3.8)) + 120
        monolithic_large_comp_tok = 180
        monolithic_large_cost = (
            (monolithic_large_prompt_tok * LargeTeacherModel.INPUT_COST_PER_M / 1e6)
            + (monolithic_large_comp_tok * LargeTeacherModel.OUTPUT_COST_PER_M / 1e6)
        )

        if passes:
            # Succeeded at Tier 1 (Small Model)
            total_lat = small_res.latency_ms
            actual_cost = small_res.cost_usd
            saved_usd = monolithic_large_cost - actual_cost
            savings_pct = (saved_usd / monolithic_large_cost) * 100.0

            decision = RoutingDecision(
                query_id=qid,
                query=query,
                final_tier="SMALL",
                escalated=False,
                escalation_reason=None,
                small_confidence=small_res.confidence_score,
                small_latency_ms=small_res.latency_ms,
                large_latency_ms=0.0,
                total_latency_ms=round(total_lat, 2),
                total_tokens=small_res.prompt_tokens + small_res.completion_tokens,
                actual_cost_usd=round(actual_cost, 7),
                monolithic_large_cost_usd=round(monolithic_large_cost, 7),
                cost_savings_usd=round(saved_usd, 7),
                cost_savings_pct=round(savings_pct, 1),
                action_plan=small_res.parsed_json or {},
            )
        else:
            # Step 2: Escalate to Large Model
            large_res = self.large_model.predict(query)
            total_lat = small_res.latency_ms + large_res.latency_ms
            # Blended cost = Small Model attempt + Large Model execution
            actual_cost = small_res.cost_usd + large_res.cost_usd
            saved_usd = monolithic_large_cost - actual_cost
            savings_pct = (saved_usd / monolithic_large_cost) * 100.0 if monolithic_large_cost > 0 else 0.0

            decision = RoutingDecision(
                query_id=qid,
                query=query,
                final_tier="LARGE_ESCALATED",
                escalated=True,
                escalation_reason=rejection_reason,
                small_confidence=small_res.confidence_score,
                small_latency_ms=small_res.latency_ms,
                large_latency_ms=large_res.latency_ms,
                total_latency_ms=round(total_lat, 2),
                total_tokens=(
                    small_res.prompt_tokens + small_res.completion_tokens +
                    large_res.prompt_tokens + large_res.completion_tokens
                ),
                actual_cost_usd=round(actual_cost, 7),
                monolithic_large_cost_usd=round(monolithic_large_cost, 7),
                cost_savings_usd=round(saved_usd, 7),
                cost_savings_pct=round(savings_pct, 1),
                action_plan=large_res.parsed_json or {},
            )

        self.routing_history.append(decision)
        return decision
