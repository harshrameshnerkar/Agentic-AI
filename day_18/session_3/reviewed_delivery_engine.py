"""
Day 18 - Session 3: Code Review
Hardened production delivery engine implementing all 5 code review fixes:
1. Single-use Nonce / Replay Registry for HMAC signatures.
2. Hardened compiled regexes with input length limit (Anti-ReDoS).
3. Enum-based Blast Radius tiers.
4. Thread-safe lock on cryptographic audit log writes.
5. Typed dataclass TriageResult payload.
"""

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import hmac
import json
import os
import re
import threading
import time
from typing import Any, Dict, Optional, Tuple


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
    MAX_INPUT_LENGTH = 100_000

    PATTERNS = [
        (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_SSN]"),
        (re.compile(r"\b(?:\d{4}[-\s]\d{4}[-\s]\d{4}[-\s]\d{4}|\d{16})\b"), "[REDACTED_CREDIT_CARD]"),
        (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "[REDACTED_EMAIL]"),
        (re.compile(r"\beyJ[A-Za-z0-9-_]{10,}\.[A-Za-z0-9-_]{10,}\.[A-Za-z0-9-_]{10,}\b"), "[REDACTED_JWT_TOKEN]"),
        (re.compile(r"(?i)(password|secret|api_key|token)\s*[:=]\s*['\"]?([A-Za-z0-9\-_+=]{8,})['\"]?"), r"\1=[REDACTED_SECRET]"),
    ]

    @classmethod
    def sanitize(cls, text: str) -> Tuple[str, int]:
        if len(text) > cls.MAX_INPUT_LENGTH:
            text = text[:cls.MAX_INPUT_LENGTH]
        count = 0
        for pat, repl in cls.PATTERNS:
            text, n = pat.subn(repl, text)
            count += n
        return text, count


class HardenedBlastRadiusClassifier:
    TIER_3 = frozenset(["rollback", "scale deployment", "kill query", "kill", "restart pod", "patch configmap", "revert corefile", "delete", "drop", "terminate"])
    TIER_2 = frozenset(["clean up /tmp", "flush cache", "resend", "logrotate", "trigger external secrets sync"])

    @classmethod
    def classify_action(cls, action_text: str) -> BlastRadiusTier:
        act = action_text.lower()
        if any(kw in act for kw in cls.TIER_3):
            return BlastRadiusTier.TIER_3_CONSEQUENTIAL
        if any(kw in act for kw in cls.TIER_2):
            return BlastRadiusTier.TIER_2_SCOPED_SAFE
        return BlastRadiusTier.TIER_1_READ_ONLY


class HardenedHITLGateway:
    SECRET_KEY = b"enterprise-sre-hitl-secret-key-2026"
    MAX_CLOCK_SKEW_SEC = 300
    _consumed_signatures: Dict[str, int] = {}
    _lock = threading.Lock()

    @classmethod
    def generate_signature(cls, incident_id: str, action_command: str, approver_email: str, timestamp_epoch: int) -> str:
        payload = f"{incident_id}:{action_command}:{approver_email}:{timestamp_epoch}".encode("utf-8")
        return hmac.new(cls.SECRET_KEY, payload, hashlib.sha256).hexdigest()

    @classmethod
    def verify_and_consume_approval(
        cls, incident_id: str, action_command: str, approver_email: str, timestamp_epoch: int, provided_signature: str
    ) -> Tuple[bool, str]:
        now = int(time.time())
        with cls._lock:
            cls._consumed_signatures = {s: exp for s, exp in cls._consumed_signatures.items() if exp > now}
            if abs(now - timestamp_epoch) > cls.MAX_CLOCK_SKEW_SEC:
                return False, f"Signature expired or clock skew > {cls.MAX_CLOCK_SKEW_SEC}s."
            if provided_signature in cls._consumed_signatures:
                return False, "REPLAY_ATTACK_DETECTED: Signature already consumed."

            expected = cls.generate_signature(incident_id, action_command, approver_email, timestamp_epoch)
            if not hmac.compare_digest(expected, provided_signature):
                return False, "Cryptographic verification failed."

            cls._consumed_signatures[provided_signature] = now + cls.MAX_CLOCK_SKEW_SEC
            return True, "Signature verified and consumed successfully. Action authorized."


class ThreadSafeAuditLogger:
    GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

    def __init__(self, log_path: str):
        self.log_path = log_path
        self._lock = threading.RLock()
        with self._lock:
            if not os.path.exists(self.log_path):
                open(self.log_path, "w", encoding="utf-8").close()

    def get_latest_hash(self) -> str:
        with self._lock:
            if not os.path.exists(self.log_path) or os.path.getsize(self.log_path) == 0:
                return self.GENESIS_HASH
            last = ""
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        last = line.strip()
            if not last:
                return self.GENESIS_HASH
            try:
                return json.loads(last).get("entry_hash", self.GENESIS_HASH)
            except Exception:
                return self.GENESIS_HASH

    def log_event(self, incident_id: str, event_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            prev_hash = self.get_latest_hash()
            timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            payload = f"{prev_hash}:{timestamp}:{incident_id}:{event_type}:{json.dumps(details, sort_keys=True)}"
            entry_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
            record = {
                "timestamp": timestamp,
                "incident_id": incident_id,
                "event_type": event_type,
                "details": details,
                "prev_hash": prev_hash,
                "entry_hash": entry_hash,
            }
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
            return record

    def verify_integrity(self) -> Tuple[bool, int, str]:
        with self._lock:
            if not os.path.exists(self.log_path) or os.path.getsize(self.log_path) == 0:
                return True, 0, "Log empty."
            expected_prev = self.GENESIS_HASH
            count = 0
            with open(self.log_path, "r", encoding="utf-8") as f:
                for idx, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                    e = json.loads(line.strip())
                    if e.get("prev_hash") != expected_prev:
                        return False, count, f"Broken chain at line {idx}"
                    payload = f"{e['prev_hash']}:{e['timestamp']}:{e['incident_id']}:{e['event_type']}:{json.dumps(e['details'], sort_keys=True)}"
                    if hashlib.sha256(payload.encode("utf-8")).hexdigest() != e["entry_hash"]:
                        return False, count, f"Hash mismatch at line {idx}"
                    expected_prev = e["entry_hash"]
                    count += 1
            return True, count, f"All {count} verified."


class ReviewedDeliveryService:
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
        timestamp_epoch: Optional[int] = None,
    ) -> TriageResult:
        clean_query, pii_c = HardenedPIISanitizer.sanitize(raw_alert_query)
        if pii_c > 0:
            self.audit_logger.log_event(incident_id, "PII_REDACTION", {"count": pii_c})

        q = clean_query.lower()
        if any(w in q for w in ["oom", "exit code 137", "crashing"]):
            root_cause = "JVM OutOfMemoryError caused by unbounded memory leak"
            remediation = "Rollback deployment and increase pod memory limits from 512Mi to 2Gi"
        elif any(w in q for w in ["504", "pool"]):
            root_cause = "Database connection pool exhaustion"
            remediation = "Kill long-running unindexed query and scale connection pool"
        else:
            root_cause = "General infrastructure fault"
            remediation = "Inspect container logs and restart pod"

        blast_tier = HardenedBlastRadiusClassifier.classify_action(remediation)
        if blast_tier != BlastRadiusTier.TIER_3_CONSEQUENTIAL:
            status = "EXECUTED_AUTOMATICALLY"
            msg = "Safe action executed automatically."
            self.audit_logger.log_event(incident_id, "ACTION_EXECUTED_AUTO", {"action": remediation})
        elif approval_signature and approver_email and timestamp_epoch:
            ok, v_msg = HardenedHITLGateway.verify_and_consume_approval(incident_id, remediation, approver_email, timestamp_epoch, approval_signature)
            if ok:
                status, msg = "EXECUTED_WITH_APPROVAL", f"Authorized by {approver_email}. Single-use HMAC consumed."
                self.audit_logger.log_event(incident_id, "HITL_APPROVAL_GRANTED", {"approver": approver_email})
            else:
                status, msg = "BLOCKED_SECURITY_VIOLATION", f"REJECTED: {v_msg}"
                self.audit_logger.log_event(incident_id, "HITL_APPROVAL_REJECTED", {"reason": v_msg})
        else:
            status, msg = "BLOCKED_HITL_REQUIRED", "Tier 3 action BLOCKED awaiting cryptographic HMAC approval."
            self.audit_logger.log_event(incident_id, "ACTION_BLOCKED_HITL", {"action": remediation})

        return TriageResult(
            incident_id=incident_id,
            service_name=service_name,
            sanitized_query=clean_query,
            root_cause_diagnosis=root_cause,
            proposed_remediation=remediation,
            blast_radius_tier=blast_tier,
            execution_status=status,
            hitl_message=msg,
            audit_hash=self.audit_logger.get_latest_hash(),
        )
