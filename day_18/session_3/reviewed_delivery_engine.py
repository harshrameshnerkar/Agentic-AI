"""
Day 18 - Session 3: Code Review
Hardened Production Delivery Engine implementing all 5 Code Review fixes:
1. Single-use Nonce / Replay Registry for HMAC signatures.
2. Hardened compiled regexes with input length guard (Anti-ReDoS).
3. Enum-based Blast Radius tiers and frozenset constants.
4. Thread-safe re-entrant lock on cryptographic audit log writes.
5. Typed dataclass TriageResult return payload.
"""

import os
import sys
import json
import time
import re
import hmac
import hashlib
import threading
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Tuple, Optional, Set


class BlastRadiusTier(str, Enum):
    TIER_1_READ_ONLY = "Tier 1 (Read-Only - Informational)"
    TIER_2_SCOPED_SAFE = "Tier 2 (Scoped Safe - Automated)"
    TIER_3_CONSEQUENTIAL = "Tier 3 (Consequential - HITL Required)"


@dataclass
class TriageResult:
    incident_id: str
    service_name: str
    sanitized_query: str
    root_cause_diagnosis: str
    proposed_remediation: str
    blast_radius_tier: BlastRadiusTier
    execution_status: str
    hitl_message: str
    audit_hash: str

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["blast_radius_tier"] = self.blast_radius_tier.value
        return d


class HardenedPIISanitizer:
    """Pre-compiled, bounded regex sanitizer with input length protection (Anti-ReDoS)."""

    MAX_INPUT_LENGTH = 100_000  # 100 KB limit

    # Pre-compiled bounded regex patterns
    PATTERN_SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
    PATTERN_CC = re.compile(r"\b(?:\d{4}[-\s]\d{4}[-\s]\d{4}[-\s]\d{4}|\d{16})\b")
    PATTERN_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
    PATTERN_JWT = re.compile(r"\beyJ[A-Za-z0-9-_]{10,}\.[A-Za-z0-9-_]{10,}\.[A-Za-z0-9-_]{10,}\b")
    PATTERN_SECRET = re.compile(r"(?i)(password|secret|api_key|token)\s*[:=]\s*['\"]?([A-Za-z0-9\-_+=]{8,})['\"]?")

    @classmethod
    def sanitize(cls, text: str) -> Tuple[str, int]:
        if len(text) > cls.MAX_INPUT_LENGTH:
            text = text[:cls.MAX_INPUT_LENGTH]

        count = 0
        text, n = cls.PATTERN_SSN.subn("[REDACTED_SSN]", text)
        count += n
        text, n = cls.PATTERN_CC.subn("[REDACTED_CREDIT_CARD]", text)
        count += n
        text, n = cls.PATTERN_EMAIL.subn("[REDACTED_EMAIL]", text)
        count += n
        text, n = cls.PATTERN_JWT.subn("[REDACTED_JWT_TOKEN]", text)
        count += n
        text, n = cls.PATTERN_SECRET.subn(r"\1=[REDACTED_SECRET]", text)
        count += n

        return text, count


class HardenedBlastRadiusClassifier:
    """Classifies actions using frozenset constants and Enum returns."""

    TIER_3_KEYWORDS = frozenset([
        "rollback", "scale deployment", "kill query", "kill", "restart pod",
        "patch configmap", "revert corefile", "delete", "drop", "terminate"
    ])

    TIER_2_KEYWORDS = frozenset([
        "clean up /tmp", "flush cache", "resend", "logrotate", "trigger external secrets sync"
    ])

    @classmethod
    def classify_action(cls, action_text: str) -> BlastRadiusTier:
        act_lower = action_text.lower()
        for kw in cls.TIER_3_KEYWORDS:
            if kw in act_lower:
                return BlastRadiusTier.TIER_3_CONSEQUENTIAL
        for kw in cls.TIER_2_KEYWORDS:
            if kw in act_lower:
                return BlastRadiusTier.TIER_2_SCOPED_SAFE
        return BlastRadiusTier.TIER_1_READ_ONLY


class HardenedHITLGateway:
    """Cryptographic HMAC gateway with single-use nonce registry to prevent replay attacks."""

    SECRET_KEY = b"enterprise-sre-hitl-secret-key-2026"
    MAX_CLOCK_SKEW_SEC = 300

    # In-memory registry of consumed signatures: {signature: expiry_epoch}
    _consumed_signatures: Dict[str, int] = {}
    _lock = threading.Lock()

    @classmethod
    def _cleanup_expired_nonces(cls, current_epoch: int):
        with cls._lock:
            cls._consumed_signatures = {
                sig: exp for sig, exp in cls._consumed_signatures.items() if exp > current_epoch
            }

    @classmethod
    def generate_signature(cls, incident_id: str, action_command: str, approver_email: str, timestamp_epoch: int) -> str:
        payload = f"{incident_id}:{action_command}:{approver_email}:{timestamp_epoch}".encode("utf-8")
        return hmac.new(cls.SECRET_KEY, payload, hashlib.sha256).hexdigest()

    @classmethod
    def verify_and_consume_approval(
        cls,
        incident_id: str,
        action_command: str,
        approver_email: str,
        timestamp_epoch: int,
        provided_signature: str
    ) -> Tuple[bool, str]:
        current_epoch = int(time.time())
        cls._cleanup_expired_nonces(current_epoch)

        # 1. Clock skew check
        if abs(current_epoch - timestamp_epoch) > cls.MAX_CLOCK_SKEW_SEC:
            return False, f"Signature expired or clock skew > {cls.MAX_CLOCK_SKEW_SEC}s."

        # 2. Replay check (Single-use nonce)
        with cls._lock:
            if provided_signature in cls._consumed_signatures:
                return False, "REPLAY_ATTACK_DETECTED: This signature has already been consumed and cannot be reused."

        # 3. Cryptographic HMAC verification
        expected_sig = cls.generate_signature(incident_id, action_command, approver_email, timestamp_epoch)
        if not hmac.compare_digest(expected_sig, provided_signature):
            return False, "Cryptographic verification failed: Unauthorized or corrupted signature."

        # 4. Mark signature as consumed
        with cls._lock:
            cls._consumed_signatures[provided_signature] = current_epoch + cls.MAX_CLOCK_SKEW_SEC

        return True, "Signature verified and consumed successfully. Action authorized."


class ThreadSafeAuditLogger:
    """Thread-safe cryptographic audit logger protected by threading.RLock."""

    GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

    def __init__(self, log_path: str):
        self.log_path = log_path
        self._lock = threading.RLock()
        self._ensure_file()

    def _ensure_file(self):
        with self._lock:
            if not os.path.exists(self.log_path):
                with open(self.log_path, "w", encoding="utf-8") as f:
                    f.write("")

    def get_latest_hash(self) -> str:
        with self._lock:
            if not os.path.exists(self.log_path) or os.path.getsize(self.log_path) == 0:
                return self.GENESIS_HASH

            last_line = ""
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        last_line = line.strip()

            if not last_line:
                return self.GENESIS_HASH

            try:
                entry = json.loads(last_line)
                return entry.get("entry_hash", self.GENESIS_HASH)
            except Exception:
                return self.GENESIS_HASH

    def log_event(self, incident_id: str, event_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            prev_hash = self.get_latest_hash()
            timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

            payload_str = json.dumps(details, sort_keys=True)
            raw = f"{prev_hash}:{timestamp}:{incident_id}:{event_type}:{payload_str}".encode("utf-8")
            entry_hash = hashlib.sha256(raw).hexdigest()

            record = {
                "timestamp": timestamp,
                "incident_id": incident_id,
                "event_type": event_type,
                "details": details,
                "prev_hash": prev_hash,
                "entry_hash": entry_hash
            }

            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")

            return record

    def verify_integrity(self) -> Tuple[bool, int, str]:
        with self._lock:
            if not os.path.exists(self.log_path) or os.path.getsize(self.log_path) == 0:
                return True, 0, "Log file is empty (valid)."

            expected_prev = self.GENESIS_HASH
            count = 0

            with open(self.log_path, "r", encoding="utf-8") as f:
                for line_no, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                    entry = json.loads(line.strip())
                    if entry.get("prev_hash") != expected_prev:
                        return False, count, f"Broken chain at line {line_no}"

                    payload_str = json.dumps(entry["details"], sort_keys=True)
                    raw = f"{entry['prev_hash']}:{entry['timestamp']}:{entry['incident_id']}:{entry['event_type']}:{payload_str}".encode("utf-8")
                    recomputed = hashlib.sha256(raw).hexdigest()

                    if recomputed != entry["entry_hash"]:
                        return False, count, f"Hash mismatch at line {line_no}"

                    expected_prev = entry["entry_hash"]
                    count += 1

            return True, count, f"All {count} entries verified."


class ReviewedDeliveryService:
    """Hardened Delivery Service implementing all post-review enhancements."""

    def __init__(self, audit_log_path: str):
        self.audit_logger = ThreadSafeAuditLogger(audit_log_path)

    def process_incident(
        self,
        incident_id: str,
        service_name: str,
        raw_alert_query: str,
        live_telemetry: Optional[Dict[str, Any]] = None,
        approval_signature: Optional[str] = None,
        approver_email: Optional[str] = None,
        timestamp_epoch: Optional[int] = None
    ) -> TriageResult:
        # 1. PII Redaction
        clean_query, pii_c = HardenedPIISanitizer.sanitize(raw_alert_query)
        if pii_c > 0:
            self.audit_logger.log_event(incident_id, "PII_REDACTION", {"count": pii_c})

        # 2. Diagnostic reasoning
        q_lower = clean_query.lower()
        if any(w in q_lower for w in ["oom", "exit code 137", "crashing"]):
            root_cause = "JVM OutOfMemoryError caused by unbounded memory leak"
            remediation = "Rollback deployment and increase pod memory limits from 512Mi to 2Gi"
        elif any(w in q_lower for w in ["504", "pool"]):
            root_cause = "Database connection pool exhaustion"
            remediation = "Kill long-running unindexed query and scale connection pool"
        else:
            root_cause = "General infrastructure fault"
            remediation = "Inspect container logs and restart pod"

        # 3. Blast Radius Classification
        blast_tier = HardenedBlastRadiusClassifier.classify_action(remediation)

        # 4. HITL Approval Gate
        if blast_tier != BlastRadiusTier.TIER_3_CONSEQUENTIAL:
            status = "EXECUTED_AUTOMATICALLY"
            msg = "Safe action executed automatically."
            self.audit_logger.log_event(incident_id, "ACTION_EXECUTED_AUTO", {"action": remediation})
        else:
            if approval_signature and approver_email and timestamp_epoch:
                is_valid, verify_msg = HardenedHITLGateway.verify_and_consume_approval(
                    incident_id, remediation, approver_email, timestamp_epoch, approval_signature
                )
                if is_valid:
                    status = "EXECUTED_WITH_APPROVAL"
                    msg = f"Authorized by {approver_email}. Single-use HMAC consumed."
                    self.audit_logger.log_event(incident_id, "HITL_APPROVAL_GRANTED", {"approver": approver_email})
                else:
                    status = "BLOCKED_SECURITY_VIOLATION"
                    msg = f"REJECTED: {verify_msg}"
                    self.audit_logger.log_event(incident_id, "HITL_APPROVAL_REJECTED", {"reason": verify_msg})
            else:
                status = "BLOCKED_HITL_REQUIRED"
                msg = "Tier 3 action BLOCKED awaiting cryptographic HMAC approval."
                self.audit_logger.log_event(incident_id, "ACTION_BLOCKED_HITL", {"action": remediation})

        audit_hash = self.audit_logger.get_latest_hash()
        return TriageResult(
            incident_id=incident_id,
            service_name=service_name,
            sanitized_query=clean_query,
            root_cause_diagnosis=root_cause,
            proposed_remediation=remediation,
            blast_radius_tier=blast_tier,
            execution_status=status,
            hitl_message=msg,
            audit_hash=audit_hash
        )
