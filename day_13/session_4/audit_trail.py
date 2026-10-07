"""
Day 13 - Session 4: Tamper-Evident Append-Only Audit Trail
==========================================================
Implements:
  1. Cryptographic SHA-256 Hash Chaining (blockchain-style tamper detection)
  2. Granular Tool Telemetry: Capturing tool name, inputs, outputs, status, latency
  3. Operator Attribution: Logging session_id, tenant_id, and operator_id
  4. Blast Radius & Approval Decision Tracking
  5. Cryptographic Integrity Auditor (verify_integrity)
"""

import time
import json
import hashlib
import uuid
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class AuditRecord:
    event_id: str
    session_id: str
    tenant_id: str
    operator_id: str
    timestamp: str
    event_type: str            # "TOOL_CALL" | "TOOL_OUTCOME" | "APPROVAL_GATE" | "COMPENSATING_ACTION"
    tool_name: Optional[str]
    payload: Dict[str, Any]
    blast_radius: str          # "READ_ONLY" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    status: str                # "PENDING" | "SUCCESS" | "FAILED" | "BLOCKED" | "APPROVED" | "REJECTED"
    previous_hash: str
    record_hash: str

    def compute_hash(self) -> str:
        """Computes SHA-256 digest of record contents combined with previous_hash."""
        content = {
            "event_id": self.event_id,
            "session_id": self.session_id,
            "tenant_id": self.tenant_id,
            "operator_id": self.operator_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "tool_name": self.tool_name,
            "payload": self.payload,
            "blast_radius": self.blast_radius,
            "status": self.status,
            "previous_hash": self.previous_hash,
        }
        raw = json.dumps(content, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class AuditTrailStore:
    """
    Immutable, append-only operational audit ledger.
    Every tool call, input argument, return value, and human decision is cryptographically logged.
    """

    GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

    def __init__(self):
        self._records: List[AuditRecord] = []

    def _get_last_hash(self) -> str:
        return self._records[-1].record_hash if self._records else self.GENESIS_HASH

    def log_event(
        self,
        session_id: str,
        tenant_id: str,
        operator_id: str,
        event_type: str,
        tool_name: Optional[str],
        payload: Dict[str, Any],
        blast_radius: str = "READ_ONLY",
        status: str = "SUCCESS",
    ) -> AuditRecord:
        """Appends a new cryptographically signed record to the audit chain."""
        event_id = f"AUD-{uuid.uuid4().hex[:10].upper()}"
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        prev_hash = self._get_last_hash()

        # Temporary record to compute hash
        rec = AuditRecord(
            event_id=event_id,
            session_id=session_id,
            tenant_id=tenant_id,
            operator_id=operator_id,
            timestamp=ts,
            event_type=event_type,
            tool_name=tool_name,
            payload=payload,
            blast_radius=blast_radius,
            status=status,
            previous_hash=prev_hash,
            record_hash="",
        )
        rec.record_hash = rec.compute_hash()
        self._records.append(rec)
        return rec

    def log_tool_call(
        self,
        session_id: str,
        tenant_id: str,
        operator_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        blast_radius: str,
    ) -> AuditRecord:
        return self.log_event(
            session_id=session_id,
            tenant_id=tenant_id,
            operator_id=operator_id,
            event_type="TOOL_CALL",
            tool_name=tool_name,
            payload={"arguments": arguments},
            blast_radius=blast_radius,
            status="PENDING",
        )

    def log_tool_outcome(
        self,
        session_id: str,
        tenant_id: str,
        operator_id: str,
        tool_name: str,
        output: Dict[str, Any],
        status: str,
        latency_ms: float,
        blast_radius: str = "READ_ONLY",
    ) -> AuditRecord:
        return self.log_event(
            session_id=session_id,
            tenant_id=tenant_id,
            operator_id=operator_id,
            event_type="TOOL_OUTCOME",
            tool_name=tool_name,
            payload={"output": output, "latency_ms": latency_ms},
            blast_radius=blast_radius,
            status=status,
        )

    def verify_integrity(self) -> Tuple[bool, Optional[str]]:
        """
        Cryptographically validates the entire audit chain from genesis to head.
        Guarantees that no logs were modified, inserted, or purged.
        """
        if not self._records:
            return True, None

        expected_prev = self.GENESIS_HASH
        for idx, rec in enumerate(self._records):
            # Check hash chaining link
            if rec.previous_hash != expected_prev:
                return False, f"Broken chain link at index {idx} (Event {rec.event_id}). Expected prev {expected_prev[:8]}, got {rec.previous_hash[:8]}"

            # Check content tamper detection
            recalculated = rec.compute_hash()
            if rec.record_hash != recalculated:
                return False, f"Tampered record at index {idx} (Event {rec.event_id}). Stored hash {rec.record_hash[:8]} != computed {recalculated[:8]}"

            expected_prev = rec.record_hash

        return True, None

    def get_session_records(self, session_id: str) -> List[AuditRecord]:
        """Returns all audit events belonging to a specific incident session."""
        return [r for r in self._records if r.session_id == session_id]

    def get_all_records(self) -> List[AuditRecord]:
        return list(self._records)
