"""
Day 14 - Session 1: Canary & Shadow Deployment Controller
==========================================================
Implements safe progressive delivery patterns for LLM Prompts and Models:
  1. Shadow Deployment (Dark Traffic Mirroring):
     - Production traffic served by Baseline (v1.0.0).
     - Cloned asynchronously to Candidate (v1.1.0) in background.
     - Compares output consistency, safety gates, and drift without impacting users.
  2. Canary Progressive Rollout:
     - Gradual traffic shift: 5% -> 25% -> 50% -> 100%.
     - Automated Health Watchdog: triggers instant rollback if error rate or safety violation exceeds threshold.
"""

import time
import random
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

try:
    from day_14.session_1.prompt_registry import PromptRegistry, PromptVersion
    from day_14.session_1.golden_dataset import GoldenTestCase, GOLDEN_EVAL_SUITE
    from day_14.session_1.agent_evaluator import AgentEvaluator
except ImportError:
    from prompt_registry import PromptRegistry, PromptVersion
    from golden_dataset import GoldenTestCase, GOLDEN_EVAL_SUITE
    from agent_evaluator import AgentEvaluator


@dataclass
class ShadowEvaluationRecord:
    request_id: str
    incident_query: str
    baseline_tool: str
    candidate_tool: str
    baseline_approval: bool
    candidate_approval: bool
    tool_agreement: bool
    safety_agreement: bool
    latency_delta_ms: float
    shadow_drift_detected: bool


@dataclass
class CanaryRolloutStage:
    traffic_percentage: int      # 5, 25, 50, 100
    requests_processed: int
    canary_errors: int
    canary_safety_violations: int
    rollback_triggered: bool
    status: str                  # "HEALTHY" | "ROLLED_BACK" | "PROMOTED"


class ShadowDeploymentRouter:
    """
    Mirrors live production requests to candidate prompt/model in background.
    Audits behavioral drift before any user traffic is touched.
    """

    def __init__(self, baseline_version: str = "v1.0.0", candidate_version: str = "v1.1.0-regressed"):
        self.baseline_prompt = PromptRegistry.get_prompt(baseline_version)
        self.candidate_prompt = PromptRegistry.get_prompt(candidate_version)
        self.base_evaluator = AgentEvaluator(self.baseline_prompt)
        self.cand_evaluator = AgentEvaluator(self.candidate_prompt)
        self.shadow_records: List[ShadowEvaluationRecord] = []

    def process_shadow_request(self, test_case: GoldenTestCase) -> Dict[str, Any]:
        """
        Serves user with baseline response while executing shadow candidate in background.
        """
        # User-facing execution (Baseline)
        base_res = self.base_evaluator.evaluate_case(test_case)

        # Shadow background execution (Candidate)
        cand_res = self.cand_evaluator.evaluate_case(test_case)

        # Audit comparison
        base_tool = base_res.parsed_response.get("tool_to_use") if base_res.parsed_response else "UNKNOWN"
        cand_tool = (
            cand_res.parsed_response.get("tool_to_use") or cand_res.parsed_response.get("action")
            if cand_res.parsed_response else "UNKNOWN"
        )

        base_appr = bool(base_res.parsed_response.get("requires_human_approval")) if base_res.parsed_response else False
        cand_appr = bool(
            cand_res.parsed_response.get("requires_human_approval") or cand_res.parsed_response.get("requires_approval")
        ) if cand_res.parsed_response else False

        tool_match = (base_tool == cand_tool)
        safety_match = (base_appr == cand_appr)
        drift_detected = not (tool_match and safety_match)

        record = ShadowEvaluationRecord(
            request_id=test_case.id,
            incident_query=test_case.incident_query,
            baseline_tool=str(base_tool),
            candidate_tool=str(cand_tool),
            baseline_approval=base_appr,
            candidate_approval=cand_appr,
            tool_agreement=tool_match,
            safety_agreement=safety_match,
            latency_delta_ms=round(cand_res.latency_ms - base_res.latency_ms, 2),
            shadow_drift_detected=drift_detected,
        )
        self.shadow_records.append(record)

        return {
            "user_response": base_res.raw_output,  # User receives ONLY baseline
            "shadow_record": record,
        }

    def compute_shadow_drift_summary(self) -> Dict[str, Any]:
        total = len(self.shadow_records)
        if total == 0:
            return {"total_requests": 0}

        drift_cnt = sum(1 for r in self.shadow_records if r.shadow_drift_detected)
        tool_agree_cnt = sum(1 for r in self.shadow_records if r.tool_agreement)
        safety_agree_cnt = sum(1 for r in self.shadow_records if r.safety_agreement)

        return {
            "total_shadow_requests": total,
            "drift_percentage": round((drift_cnt / total) * 100.0, 2),
            "tool_agreement_pct": round((tool_agree_cnt / total) * 100.0, 2),
            "safety_agreement_pct": round((safety_agree_cnt / total) * 100.0, 2),
            "safe_for_canary": (drift_cnt == 0),
        }


class CanaryDeploymentController:
    """
    Manages progressive traffic shifting with automated watchdog rollback.
    """

    def __init__(
        self,
        baseline_version: str = "v1.0.0",
        candidate_version: str = "v1.1.0-regressed",
        max_error_threshold_pct: float = 2.0,
    ):
        self.baseline_prompt = PromptRegistry.get_prompt(baseline_version)
        self.candidate_prompt = PromptRegistry.get_prompt(candidate_version)
        self.base_evaluator = AgentEvaluator(self.baseline_prompt)
        self.cand_evaluator = AgentEvaluator(self.candidate_prompt)
        self.max_error_threshold = max_error_threshold_pct
        self.stages: List[CanaryRolloutStage] = []

    def simulate_rollout(self, test_cases: List[GoldenTestCase]) -> List[CanaryRolloutStage]:
        """
        Simulates progressive rollout across 5% -> 25% -> 50% -> 100%.
        Automatically rolls back if error or safety threshold is breached.
        """
        rollout_steps = [5, 25, 50, 100]

        for step in rollout_steps:
            errors = 0
            safety_violations = 0
            processed = len(test_cases)

            for tc in test_cases:
                # In canary step, route a fraction to candidate
                # For deterministic demonstration, test candidate behavior
                res = self.cand_evaluator.evaluate_case(tc)
                if not res.passed:
                    errors += 1
                if not res.safety_compliant:
                    safety_violations += 1

            error_rate = (errors / processed) * 100.0
            rollback = (error_rate > self.max_error_threshold) or (safety_violations > 0)

            stage = CanaryRolloutStage(
                traffic_percentage=step,
                requests_processed=processed,
                canary_errors=errors,
                canary_safety_violations=safety_violations,
                rollback_triggered=rollback,
                status="ROLLED_BACK" if rollback else "PROMOTED",
            )
            self.stages.append(stage)

            if rollback:
                # Immediate halt and rollback!
                break

        return self.stages
