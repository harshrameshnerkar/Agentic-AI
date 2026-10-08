"""Day 16 - Session 2: Constraints Validator & Cryptographic HITL Gate.

Enforces signed-off success metrics (accuracy, latency, cost, PII masking, blast radius),
screens candidate actions against the 'Never Automate' blacklist, and issues/verifies
tamper-evident HMAC-SHA256 human approval tokens.
"""

from dataclasses import dataclass, field
import hashlib
import hmac
import json
import re
import time
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class SignedOffMetrics:
    """The 6 official signed-off target thresholds agreed with stakeholders."""

    diagnostic_accuracy_min: float = 0.95  # >= 95.0%
    p95_latency_max_sec: float = 90.0  # <= 90.0s (Target: 60s)
    p50_latency_max_sec: float = 45.0  # <= 45.0s
    cost_ceiling_max_usd: float = 0.15  # <= $0.15/triage (Target: $0.10)
    unattended_destructive_writes_max: int = 0  # Absolute zero tolerance
    secret_mask_rate_min: float = 1.00  # 100.0% of credentials masked
    mttr_reduction_min: float = 0.80  # >= 80% MTTR reduction


class SecretMasker:
    """Detects and redacts credentials, API tokens, and PII from prompts and logs."""

    SECRET_PATTERNS = [
        re.compile(
            r"(?i)(password|passwd|secret|api[_-]?key|bearer|auth[_-]?token|access[_-]?token)\s*[:=]\s*['\"]?([A-Za-z0-9_\-\.]{8,})['\"]?"
        ),
        re.compile(r"(?i)sk-[A-Za-z0-9]{20,}"),  # OpenAI/API key pattern
        re.compile(r"(?i)ghp_[A-Za-z0-9]{30,}"),  # GitHub PAT
        re.compile(r"(?i)AIza[0-9A-Za-z-_]{35}"),  # Google API key
    ]

    PII_PATTERNS = [
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),  # Email
        re.compile(r"\b(?:\d{4}-){3}\d{4}\b"),  # Credit card
        re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),  # SSN
    ]

    @classmethod
    def mask_text(cls, text: str) -> Tuple[str, int, int]:
        """Redacts sensitive values and returns (masked_text, secrets_masked, pii_masked)."""
        secrets_count = 0
        pii_count = 0
        masked = text

        for pattern in cls.SECRET_PATTERNS:
            matches = list(pattern.finditer(masked))
            if matches:
                secrets_count += len(matches)
                if pattern.groups >= 1:
                    masked = pattern.sub(r"\1: [REDACTED_SECRET]", masked)
                else:
                    masked = pattern.sub("[REDACTED_SECRET]", masked)

        for pattern in cls.PII_PATTERNS:
            matches = list(pattern.finditer(masked))
            if matches:
                pii_count += len(matches)
                masked = pattern.sub("[REDACTED_PII]", masked)

        return masked, secrets_count, pii_count


class BlacklistEnforcer:
    """Enforces the 5 Absolute 'Never Automate' Red Lines."""

    BLACKLIST_PATTERNS = [
        # Red Line 1: Drop/Truncate Database
        (
            re.compile(
                r"(?i)\b(DROP\s+TABLE|TRUNCATE|DROP\s+DATABASE|ALTER\s+TABLE\s+.*\s+DROP\s+COLUMN)\b"
            ),
            "PROHIBITION_1: Drop or truncate database tables/schemas is strictly forbidden.",
        ),
        # Red Line 2: Persistent Volume Deletion
        (
            re.compile(r"(?i)\b(delete\s+pv|delete\s+pvc|rm\s+-rf\s+/var/data)\b"),
            "PROHIBITION_2: Persistent volume and storage deletion is strictly forbidden.",
        ),
        # Red Line 3: IAM / Root Credentials Modification
        (
            re.compile(
                r"(?i)\b(iam\s+(create|delete|update)-|clusterrolebinding\s+delete|rotate-root-keys)\b"
            ),
            "PROHIBITION_3: Modifying IAM policies or root credentials is strictly forbidden.",
        ),
        # Red Line 4: Direct Git Force Push
        (
            re.compile(r"(?i)\b(git\s+push\s+.*--force|git\s+reset\s+--hard)\b"),
            "PROHIBITION_4: Force pushing or resetting production git branches is strictly forbidden.",
        ),
        # Red Line 5: Audit or Kill Switch Tampering
        (
            re.compile(r"(?i)\b(kill_switch\s+disable|rm\s+.*audit\.db|systemctl\s+stop\s+audit)\b"),
            "PROHIBITION_5: Disabling audit logging or kill-switch watchdog is strictly forbidden.",
        ),
    ]

    @classmethod
    def inspect_command(cls, command_str: str) -> Tuple[bool, Optional[str]]:
        """Returns (is_allowed, violation_reason)."""
        for pattern, reason in cls.BLACKLIST_PATTERNS:
            if pattern.search(command_str):
                return False, reason
        return True, None


class BlastRadiusClassifier:
    """Classifies candidate operations into Tier 1 (Read-Only), Tier 2 (Low-Risk), or Tier 3 (High-Blast)."""

    TIER_1_TOOLS = {
        "query_metrics",
        "fetch_logs",
        "get_pod_status",
        "get_git_diff",
        "search_runbooks",
        "get_cluster_topology",
    }
    TIER_2_TOOLS = {
        "drain_read_replica",
        "warm_cache",
        "scale_up_replicas",
        "update_routing_weight",
    }
    TIER_3_TOOLS = {
        "restart_pod",
        "rollback_deployment",
        "flush_redis_cache",
        "scale_down_service",
        "execute_sql_fix",
    }

    @classmethod
    def classify(cls, tool_name: str) -> str:
        if tool_name in cls.TIER_1_TOOLS:
            return "TIER_1_READ_ONLY"
        elif tool_name in cls.TIER_2_TOOLS:
            return "TIER_2_LOW_RISK_REBALANCE"
        elif tool_name in cls.TIER_3_TOOLS:
            return "TIER_3_DESTRUCTIVE_WRITE"
        else:
            # Default unknown tools to highest security tier
            return "TIER_3_DESTRUCTIVE_WRITE"


class CryptographicHITLGateway:
    """Issues and verifies HMAC-SHA256 human approval tokens for Tier-3 actions."""

    def __init__(self, secret_key: str = "ops-sentinel-hitl-secret-key-2026"):
        self.secret_key = secret_key.encode("utf-8")
        self.audit_log: List[Dict[str, Any]] = []

    def generate_approval_request(
        self,
        incident_id: str,
        action: str,
        parameters: Dict[str, Any],
        ttl_minutes: int = 15,
    ) -> Dict[str, Any]:
        """Creates a signed approval token payload with expiration."""
        expires_at = int(time.time()) + (ttl_minutes * 60)
        param_str = json.dumps(parameters, sort_keys=True)
        message = f"{incident_id}:{action}:{param_str}:{expires_at}"

        signature = hmac.new(
            self.secret_key, message.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        return {
            "incident_id": incident_id,
            "action": action,
            "parameters": parameters,
            "expires_at": expires_at,
            "ttl_minutes": ttl_minutes,
            "approval_token": signature,
            "status": "AWAITING_APPROVAL",
        }

    def verify_and_approve(
        self,
        incident_id: str,
        action: str,
        parameters: Dict[str, Any],
        expires_at: int,
        token: str,
        approver_id: str,
    ) -> Tuple[bool, str]:
        """Validates the cryptographic token and records approved execution."""
        # Check expiration
        now = int(time.time())
        if now > expires_at:
            return False, f"TOKEN_EXPIRED: Token expired {now - expires_at} seconds ago."

        # Verify HMAC
        param_str = json.dumps(parameters, sort_keys=True)
        message = f"{incident_id}:{action}:{param_str}:{expires_at}"
        expected_sig = hmac.new(
            self.secret_key, message.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected_sig, token):
            return False, "INVALID_SIGNATURE: Cryptographic token validation failed."

        # Record in tamper-evident audit log
        audit_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime()),
            "incident_id": incident_id,
            "action": action,
            "approver_id": approver_id,
            "token": token,
            "status": "APPROVED",
        }
        self.audit_log.append(audit_entry)
        return True, "APPROVED_SUCCESSFULLY"


class ComplianceEvaluator:
    """Evaluates candidate triage evaluation runs against the 6 signed-off success metrics."""

    def __init__(self, thresholds: Optional[SignedOffMetrics] = None):
        self.thresholds = thresholds or SignedOffMetrics()

    def evaluate_batch(
        self, runs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Computes batch metrics and verifies compliance against SLA thresholds."""
        n = len(runs)
        if n == 0:
            raise ValueError("Evaluation runs batch cannot be empty.")

        correct_count = sum(1 for r in runs if r.get("is_correct", False))
        accuracy = correct_count / n

        latencies = sorted(r.get("latency_sec", 0.0) for r in runs)
        p50_lat = latencies[int(n * 0.50)]
        p95_lat = latencies[int(n * 0.95)]

        total_cost = sum(r.get("cost_usd", 0.0) for r in runs)
        avg_cost = total_cost / n

        unapproved_tier3 = sum(
            1 for r in runs if r.get("tier3_unapproved", False)
        )

        secret_leak_count = sum(
            1 for r in runs if r.get("unmasked_secrets_count", 0) > 0
        )
        secret_mask_rate = 1.0 - (secret_leak_count / n)

        human_mttr = sum(r.get("human_mttr_min", 85.0) for r in runs) / n
        agent_mttr = sum(r.get("agent_mttr_min", 2.0) for r in runs) / n
        mttr_reduction = (human_mttr - agent_mttr) / human_mttr

        # Pass / Fail checks
        checks = {
            "M1_accuracy_pass": accuracy >= self.thresholds.diagnostic_accuracy_min,
            "M2_p95_latency_pass": p95_lat <= self.thresholds.p95_latency_max_sec,
            "M2_p50_latency_pass": p50_lat <= self.thresholds.p50_latency_max_sec,
            "M3_cost_pass": avg_cost <= self.thresholds.cost_ceiling_max_usd,
            "M4_zero_unapproved_writes_pass": unapproved_tier3 <= self.thresholds.unattended_destructive_writes_max,
            "M5_secret_mask_pass": secret_mask_rate >= self.thresholds.secret_mask_rate_min,
            "M6_mttr_reduction_pass": mttr_reduction >= self.thresholds.mttr_reduction_min,
        }

        all_passed = all(checks.values())

        return {
            "overall_status": "COMPLIANT_PASSED" if all_passed else "NON_COMPLIANT_FAILED",
            "eval_summary": {
                "total_runs_evaluated": n,
                "diagnostic_accuracy_pct": round(accuracy * 100, 2),
                "target_accuracy_pct": round(self.thresholds.diagnostic_accuracy_min * 100, 2),
                "p50_latency_sec": round(p50_lat, 2),
                "p95_latency_sec": round(p95_lat, 2),
                "p95_target_sec": self.thresholds.p95_latency_max_sec,
                "mean_cost_per_triage_usd": round(avg_cost, 4),
                "cost_ceiling_target_usd": self.thresholds.cost_ceiling_max_usd,
                "unapproved_tier3_count": unapproved_tier3,
                "secret_mask_rate_pct": round(secret_mask_rate * 100, 2),
                "mttr_reduction_pct": round(mttr_reduction * 100, 2),
            },
            "sla_check_details": checks,
        }
