"""
Human-In-The-Loop (HITL) Approval Gateway & Cryptographic Audit Trail for OpsSentinel Enterprise.
Provides cryptographic tamper-evident logging with SHA-256 hash chaining and approval gates
for blast-radius control on Tier 3 destructive operations.
"""

import time
import json
import uuid
import hashlib
from pathlib import Path
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

import sys
_script_dir = Path(__file__).resolve().parent
_workspace_root = _script_dir.parent.parent
for _p in [str(_workspace_root), str(_script_dir)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from day_15.session_1.config import config
except ImportError:
    try:
        from .config import config
    except ImportError:
        from config import config

class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

class ApprovalRequest(BaseModel):
    approval_id: str
    session_id: str
    tool_name: str
    input_params: Dict[str, Any]
    blast_radius_summary: str
    compensating_action: Optional[Dict[str, Any]] = None
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: float = Field(default_factory=time.time)
    expires_at: float
    decision_by: Optional[str] = None
    decision_at: Optional[float] = None
    decision_rationale: Optional[str] = None

class AuditTrailLogger:
    """Tamper-evident append-only audit trail with forward SHA-256 hash chaining."""

    def __init__(self, log_path: Optional[Path] = None):
        self.log_path = log_path or config.audit_log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._last_hash = self._compute_chain_tip()

    def _compute_chain_tip(self) -> str:
        if not self.log_path.exists() or self.log_path.stat().st_size == 0:
            return "0" * 64
        last_hash = "0" * 64
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        record = json.loads(line)
                        last_hash = record.get("current_hash", last_hash)
                    except Exception:
                        pass
        return last_hash

    def log_event(
        self,
        event_type: str,
        session_id: str,
        operator_id: str,
        details: Dict[str, Any]
    ) -> Dict[str, Any]:
        audit_id = f"AUD-{uuid.uuid4().hex[:12]}"
        now = time.time()
        payload = {
            "audit_id": audit_id,
            "session_id": session_id,
            "operator_id": operator_id,
            "timestamp": now,
            "event_type": event_type,
            "details": details,
            "prev_hash": self._last_hash
        }
        serialized = json.dumps(payload, sort_keys=True)
        current_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        payload["current_hash"] = current_hash
        self._last_hash = current_hash

        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")

        return payload

    def verify_integrity(self) -> bool:
        """Verifies full cryptographic chain integrity from root to tip."""
        if not self.log_path.exists():
            return True
        last_hash = "0" * 64
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                record = json.loads(line)
                recorded_current = record.get("current_hash")
                recorded_prev = record.get("prev_hash")
                if recorded_prev != last_hash:
                    return False
                # Recompute hash
                verification_payload = {k: v for k, v in record.items() if k != "current_hash"}
                recomputed = hashlib.sha256(json.dumps(verification_payload, sort_keys=True).encode("utf-8")).hexdigest()
                if recomputed != recorded_current:
                    return False
                last_hash = recorded_current
        return True

class HITLApprovalGateway:
    """Manages pending approval requests, token verification, and operator decisions."""

    def __init__(self, audit_logger: Optional[AuditTrailLogger] = None):
        self.audit_logger = audit_logger or AuditTrailLogger()
        self._approvals: Dict[str, ApprovalRequest] = {}

    def request_approval(
        self,
        session_id: str,
        tool_name: str,
        input_params: Dict[str, Any],
        blast_radius_summary: str,
        compensating_action: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 1800
    ) -> ApprovalRequest:
        now = time.time()
        approval_id = f"APV-{uuid.uuid4().hex[:8].upper()}"
        req = ApprovalRequest(
            approval_id=approval_id,
            session_id=session_id,
            tool_name=tool_name,
            input_params=input_params,
            blast_radius_summary=blast_radius_summary,
            compensating_action=compensating_action,
            status=ApprovalStatus.PENDING,
            created_at=now,
            expires_at=now + timeout_seconds
        )
        self._approvals[approval_id] = req

        self.audit_logger.log_event(
            event_type="APPROVAL_REQUESTED",
            session_id=session_id,
            operator_id="agent-engine",
            details={
                "approval_id": approval_id,
                "tool_name": tool_name,
                "input_params": input_params,
                "blast_radius": blast_radius_summary
            }
        )
        return req

    def approve(self, approval_id: str, operator_id: str, rationale: str = "Authorized by on-call SRE") -> ApprovalRequest:
        req = self._approvals.get(approval_id)
        if not req:
            raise ValueError(f"Approval request '{approval_id}' not found.")
        if req.status != ApprovalStatus.PENDING:
            raise ValueError(f"Approval request '{approval_id}' is already {req.status.value}.")
        if time.time() > req.expires_at:
            req.status = ApprovalStatus.EXPIRED
            raise ValueError(f"Approval request '{approval_id}' has expired.")

        req.status = ApprovalStatus.APPROVED
        req.decision_by = operator_id
        req.decision_at = time.time()
        req.decision_rationale = rationale

        self.audit_logger.log_event(
            event_type="APPROVAL_GRANTED",
            session_id=req.session_id,
            operator_id=operator_id,
            details={
                "approval_id": approval_id,
                "tool_name": req.tool_name,
                "rationale": rationale
            }
        )
        return req

    def reject(self, approval_id: str, operator_id: str, rationale: str = "Rejected by on-call SRE") -> ApprovalRequest:
        req = self._approvals.get(approval_id)
        if not req:
            raise ValueError(f"Approval request '{approval_id}' not found.")
        if req.status != ApprovalStatus.PENDING:
            raise ValueError(f"Approval request '{approval_id}' is already {req.status.value}.")

        req.status = ApprovalStatus.REJECTED
        req.decision_by = operator_id
        req.decision_at = time.time()
        req.decision_rationale = rationale

        self.audit_logger.log_event(
            event_type="APPROVAL_DENIED",
            session_id=req.session_id,
            operator_id=operator_id,
            details={
                "approval_id": approval_id,
                "tool_name": req.tool_name,
                "rationale": rationale
            }
        )
        return req

    def get_approval(self, approval_id: str) -> Optional[ApprovalRequest]:
        return self._approvals.get(approval_id)

    def get_pending_approvals(self) -> List[ApprovalRequest]:
        now = time.time()
        # Mark expired ones
        for req in self._approvals.values():
            if req.status == ApprovalStatus.PENDING and now > req.expires_at:
                req.status = ApprovalStatus.EXPIRED
        return [req for req in self._approvals.values() if req.status == ApprovalStatus.PENDING]
