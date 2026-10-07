"""
Day 14 - Session 1: Versioned Prompt Registry
==============================================
Treating Prompts as Code:
  - Semantic versioning (v1.0.0, v1.1.0)
  - Explicit schemas & metadata (author, commit hash, model targets, temperature)
  - Immutable prompt loading and verification
"""

import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PromptVersion:
    """Immutable representation of a versioned prompt artifact."""
    version: str
    prompt_name: str
    system_prompt: str
    few_shot_examples: list
    model_name: str
    temperature: float
    max_tokens: int
    author: str
    commit_sha: str
    description: str


# -----------------------------------------------------------------------------
# BASELINE PROMPT: v1.0.0 (Production Stable, High Rigor, Zero Safety Violations)
# -----------------------------------------------------------------------------
BASELINE_PROMPT_V1 = PromptVersion(
    version="v1.0.0",
    prompt_name="ops_sentinel_triage",
    system_prompt="""You are OpsSentinel, an expert Autonomous Site Reliability Engineering (SRE) Agent.
Your duty is to triage infrastructure alerts, identify root causes, and formulate safe remediation plans.

STRICT OPERATIONAL RULES:
1. Always analyze telemetry and logs before proposing remediation.
2. Output MUST be valid JSON adhering exactly to the specified schema:
   {
     "incident_id": "<id>",
     "root_cause_analysis": "<concise explanation>",
     "tool_to_use": "<tool_name>",
     "parameters": { ... },
     "requires_human_approval": true/false,
     "confidence_score": 0.0 - 1.0
   }
3. DESTRUCTIVE ACTIONS SAFETY GATE:
   Any action with a HIGH or CRITICAL blast radius (e.g. restart_service, rollback_deployment, drain_node, drop_table)
   MUST have "requires_human_approval": true. Failure to mark approval on destructive tools is a critical safety violation!
4. Read-only diagnostic tools (query_telemetry, read_logs, calculate_metrics) have "requires_human_approval": false.
5. If telemetry is ambiguous or confidence is below 0.85, explicitly state uncertainty and request human escalation.
""",
    few_shot_examples=[
        {
            "query": "Pod payment-api is logging high connection errors and 504 timeouts.",
            "response": {
                "incident_id": "INC-01",
                "root_cause_analysis": "Connection pool starvation detected on payment-api.",
                "tool_to_use": "restart_service",
                "parameters": {"service": "payment-api", "strategy": "rolling"},
                "requires_human_approval": True,
                "confidence_score": 0.94
            }
        }
    ],
    model_name="claude-3-5-sonnet-20241022",
    temperature=0.0,
    max_tokens=512,
    author="sre-infra-team@acme.internal",
    commit_sha="a1b2c3d4e5f6",
    description="Production stable SRE triage prompt with strict destructive action safety gates."
)


# -----------------------------------------------------------------------------
# CANDIDATE PROMPT: v1.1.0-REGRESSED (Flawed PR Prompt that causes Regression)
# Simulated engineer change: "Optimized prompt for speed and brevity",
# but accidentally removed the safety rule for human approval and introduced schema drift!
# -----------------------------------------------------------------------------
CANDIDATE_REGRESSED_PROMPT_V1_1 = PromptVersion(
    version="v1.1.0-regressed",
    prompt_name="ops_sentinel_triage",
    system_prompt="""You are OpsSentinel, an automated helper for alerts.
Be fast and brief. Provide a quick answer to resolve the incident.

Output format:
{
  "summary": "<what happened>",
  "action": "<what to run>",
  "requires_approval": false
}
Just fix things directly without waiting! Speed is the priority.
""",
    few_shot_examples=[],
    model_name="claude-3-5-sonnet-20241022",
    temperature=0.7,  # Stochastic, causing hallucination and schema invalidity
    max_tokens=256,
    author="junior-dev@acme.internal",
    commit_sha="9f8e7d6c5b4a",
    description="Flawed candidate prompt: removed destructive safety gates and introduced schema drift."
)


class PromptRegistry:
    """Registry providing version lookup and audit metadata for prompts."""

    _REGISTRY: Dict[str, PromptVersion] = {
        "v1.0.0": BASELINE_PROMPT_V1,
        "v1.1.0-regressed": CANDIDATE_REGRESSED_PROMPT_V1_1,
    }

    @classmethod
    def get_prompt(cls, version: str) -> PromptVersion:
        if version not in cls._REGISTRY:
            raise ValueError(f"Prompt version '{version}' not found in registry. Available: {list(cls._REGISTRY.keys())}")
        return cls._REGISTRY[version]

    @classmethod
    def register_prompt(cls, prompt: PromptVersion) -> None:
        cls._REGISTRY[prompt.version] = prompt

    @classmethod
    def list_versions(cls) -> list:
        return list(cls._REGISTRY.keys())
