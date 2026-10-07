"""
Day 13 - Session 4: Human Review & Approval Queue
=================================================
Implements:
  1. Review queue for destructive actions (restarts, rollbacks, schema changes)
  2. Granular approval states: PENDING -> APPROVED | REJECTED | EXPIRED
  3. Context-rich human inspection payload (Why the agent wants to act + evidence citations)
  4. Automatic review expiration timeout (preventing stale approvals)
  5. Operator review accountability (logging reviewer_id and decision timestamp)
"""

import time
import uuid
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


@dataclass
class ApprovalRequest:
    request_id: str
    session_id: str
    tenant_id: str
    action_type: str            # e.g. "RESTART_SERVICE" | "ROLLBACK_DEPLOYMENT" | "DRAIN_CONNECTIONS"
    proposed_tool: str
    tool_parameters: Dict[str, Any]
    blast_radius: str           # "MEDIUM" | "HIGH" | "CRITICAL"
    agent_confidence: float     # e.g. 0.92
    explanation_for_human: str  # Transparent justification
    evidence_citations: List[str]
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: float = field(default_factory=time.time)
    timeout_sec: float = 300.0   # Default 5-minute review window
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[float] = None
    rejection_reason: Optional[str] = None

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.timeout_sec and self.status == ApprovalStatus.PENDING


class HumanApprovalQueue:
    """
    Centralized Human Review Queue for Privileged Destructive Actions.
    Halts autonomous execution until an authorized SRE engineer signs off.
    """

    def __init__(self, default_timeout_sec: float = 300.0):
        self.default_timeout_sec = default_timeout_sec
        self.requests: Dict[str, ApprovalRequest] = {}

    def submit_request(
        self,
        session_id: str,
        tenant_id: str,
        action_type: str,
        proposed_tool: str,
        tool_parameters: Dict[str, Any],
        blast_radius: str,
        agent_confidence: float,
        explanation_for_human: str,
        evidence_citations: List[str],
        timeout_sec: Optional[float] = None,
    ) -> ApprovalRequest:
        """Enqueues a destructive action for human review."""
        req_id = f"APR-{uuid.uuid4().hex[:8].upper()}"
        req = ApprovalRequest(
            request_id=req_id,
            session_id=session_id,
            tenant_id=tenant_id,
            action_type=action_type,
            proposed_tool=proposed_tool,
            tool_parameters=tool_parameters,
            blast_radius=blast_radius,
            agent_confidence=agent_confidence,
            explanation_for_human=explanation_for_human,
            evidence_citations=evidence_citations,
            timeout_sec=timeout_sec or self.default_timeout_sec,
        )
        self.requests[req_id] = req
        return req

    def get_pending_requests(self) -> List[ApprovalRequest]:
        """Returns active requests pending human review (filtering out expired)."""
        now = time.time()
        active = []
        for r in self.requests.values():
            if r.status == ApprovalStatus.PENDING:
                if (now - r.created_at) > r.timeout_sec:
                    r.status = ApprovalStatus.EXPIRED
                else:
                    active.append(r)
        return active

    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        return self.requests.get(request_id)

    def approve(self, request_id: str, reviewer_id: str) -> Tuple[bool, str, Optional[ApprovalRequest]]:
        """Grants human authorization to execute the proposed tool."""
        req = self.get_request(request_id)
        if not req:
            return False, f"Request '{request_id}' not found.", None

        if req.is_expired:
            req.status = ApprovalStatus.EXPIRED
            return False, "Approval request expired before review.", req

        if req.status != ApprovalStatus.PENDING:
            return False, f"Cannot approve request with status '{req.status.value}'.", req

        req.status = ApprovalStatus.APPROVED
        req.reviewed_by = reviewer_id
        req.reviewed_at = time.time()
        return True, "Authorization granted by reviewer.", req

    def reject(self, request_id: str, reviewer_id: str, reason: str) -> Tuple[bool, str, Optional[ApprovalRequest]]:
        """Denies human authorization. Agent will abort destructive path and fall back."""
        req = self.get_request(request_id)
        if not req:
            return False, f"Request '{request_id}' not found.", None

        if req.status != ApprovalStatus.PENDING:
            return False, f"Cannot reject request with status '{req.status.value}'.", req

        req.status = ApprovalStatus.REJECTED
        req.reviewed_by = reviewer_id
        req.reviewed_at = time.time()
        req.rejection_reason = reason
        return True, "Request rejected by reviewer.", req
