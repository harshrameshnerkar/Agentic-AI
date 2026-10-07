"""
Day 13 - Session 4: Human-in-the-Loop SRE Agent Engine
======================================================
Implements:
  1. Automated Read-Only Diagnostic Execution (Telemetry & Logs)
  2. Approval Gates on Destructive Actions (Blocks restarts/rollbacks until approval)
  3. Confidence-Based Escalation (Escalates ambiguous incidents to human operators)
  4. Full Audit Trail Integration (Logs every tool call, decision, and outcome)
  5. Transparent User Telemetry (Explaining 'What was observed' and 'Why action is needed')
"""

import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
try:
    from day_13.session_4.audit_trail import AuditTrailStore, AuditRecord
    from day_13.session_4.approval_queue import HumanApprovalQueue, ApprovalRequest, ApprovalStatus
    from day_13.session_4.compensating_actions import CompensatingActionRegistry, CompensatingActionRecord
except ImportError:
    from audit_trail import AuditTrailStore, AuditRecord
    from approval_queue import HumanApprovalQueue, ApprovalRequest, ApprovalStatus
    from compensating_actions import CompensatingActionRegistry, CompensatingActionRecord


@dataclass
class AgentTurnOutput:
    session_id: str
    tenant_id: str
    operator_id: str
    status: str                 # "RESOLVED" | "AWAITING_APPROVAL" | "ESCALATED_LOW_CONFIDENCE" | "REJECTED_BY_OPERATOR"
    user_explanation: str
    diagnostic_evidence: List[Dict[str, Any]]
    pending_approval: Optional[ApprovalRequest] = None
    executed_actions: List[Dict[str, Any]] = field(default_factory=list)
    reversible_actions: List[CompensatingActionRecord] = field(default_factory=list)
    audit_records_generated: int = 0


class HumanInTheLoopAgent:
    """
    SRE Copilot with strict Human-in-the-Loop Safeguards.
    Ensures autonomous diagnostics while gating high-blast-radius remediations behind human sign-off.
    """

    def __init__(
        self,
        audit_store: Optional[AuditTrailStore] = None,
        approval_queue: Optional[HumanApprovalQueue] = None,
        compensating_registry: Optional[CompensatingActionRegistry] = None,
        confidence_threshold: float = 0.80,
    ):
        self.audit_store = audit_store or AuditTrailStore()
        self.approval_queue = approval_queue or HumanApprovalQueue()
        self.compensating_registry = compensating_registry or CompensatingActionRegistry()
        self.confidence_threshold = confidence_threshold

    def triage_incident(
        self,
        session_id: str,
        tenant_id: str,
        operator_id: str,
        alert_query: str,
        approval_token: Optional[str] = None,
    ) -> AgentTurnOutput:
        """
        Executes incident triage turn:
          1. Runs safe read-only diagnostics (telemetry & log inspection).
          2. Calculates confidence score.
          3. Checks if destructive action is required:
               - If requires approval and no token: Pauses & enqueues to review queue.
               - If approved with token: Executes action and registers compensating undo.
        """
        initial_records_count = len(self.audit_store.get_all_records())
        q_lower = alert_query.lower()

        # Step 1: Execute Safe Diagnostic Tool 1 (Telemetry DB)
        t0 = time.perf_counter()
        self.audit_store.log_tool_call(
            session_id=session_id,
            tenant_id=tenant_id,
            operator_id=operator_id,
            tool_name="query_telemetry_db",
            arguments={"service": "payment-api", "metric": "error_rate"},
            blast_radius="READ_ONLY",
        )
        # Mock telemetry result
        diag_telemetry = {"service": "payment-api", "status": "Degraded", "error_rate": "4.2%", "active_connections": 492}
        lat1 = (time.perf_counter() - t0) * 1000.0
        self.audit_store.log_tool_outcome(
            session_id=session_id,
            tenant_id=tenant_id,
            operator_id=operator_id,
            tool_name="query_telemetry_db",
            output=diag_telemetry,
            status="SUCCESS",
            latency_ms=round(lat1, 2),
            blast_radius="READ_ONLY",
        )

        # Step 2: Execute Safe Diagnostic Tool 2 (Log Inspection)
        t0 = time.perf_counter()
        self.audit_store.log_tool_call(
            session_id=session_id,
            tenant_id=tenant_id,
            operator_id=operator_id,
            tool_name="read_system_logs",
            arguments={"path": "/var/log/payment-api.log", "max_lines": 5},
            blast_radius="READ_ONLY",
        )
        diag_logs = {"path": "/var/log/payment-api.log", "findings": "Connection pool timeout 30000ms"}
        lat2 = (time.perf_counter() - t0) * 1000.0
        self.audit_store.log_tool_outcome(
            session_id=session_id,
            tenant_id=tenant_id,
            operator_id=operator_id,
            tool_name="read_system_logs",
            output=diag_logs,
            status="SUCCESS",
            latency_ms=round(lat2, 2),
            blast_radius="READ_ONLY",
        )

        # Step 3: Confidence-Based Escalation Check
        is_ambiguous = any(w in q_lower for w in ["split-brain", "zero-day", "unknown", "cascade"])
        confidence = 0.65 if is_ambiguous else 0.94

        if confidence < self.confidence_threshold:
            self.audit_store.log_event(
                session_id=session_id,
                tenant_id=tenant_id,
                operator_id=operator_id,
                event_type="APPROVAL_GATE",
                tool_name=None,
                payload={"confidence": confidence, "threshold": self.confidence_threshold, "reason": "High complexity / ambiguity"},
                blast_radius="HIGH",
                status="BLOCKED",
            )
            return AgentTurnOutput(
                session_id=session_id,
                tenant_id=tenant_id,
                operator_id=operator_id,
                status="ESCALATED_LOW_CONFIDENCE",
                user_explanation=(
                    f"Agent confidence ({confidence:.2f}) is below threshold ({self.confidence_threshold:.2f}). "
                    "Multi-service cascade detected. Automatically escalated to Senior SRE for manual review."
                ),
                diagnostic_evidence=[diag_telemetry, diag_logs],
                audit_records_generated=len(self.audit_store.get_all_records()) - initial_records_count,
            )

        # Step 4: Destructive Action Gate (Restart Pod / Rebalance Pool)
        action_type = "RESTART_POD"
        proposed_tool = "restart_service"
        proposed_args = {"service": "payment-api", "cluster": "k8s-prod-us-east"}
        blast_radius = "HIGH"

        # Check if human approval token is already granted
        if not approval_token or not approval_token.startswith("AUTH-"):
            # Enqueue to Human Review Queue
            approval_req = self.approval_queue.submit_request(
                session_id=session_id,
                tenant_id=tenant_id,
                action_type=action_type,
                proposed_tool=proposed_tool,
                tool_parameters=proposed_args,
                blast_radius=blast_radius,
                agent_confidence=confidence,
                explanation_for_human=(
                    "Diagnostic evidence confirms payment-api connection starvation (492/500 connections). "
                    "A rolling container restart is required to drain leaked connections."
                ),
                evidence_citations=[
                    "Telemetry: 492 active connections (saturation threshold 95%)",
                    "Logs: Connection pool timeout 30000ms",
                ],
            )

            # Log blocked approval gate to audit trail
            self.audit_store.log_event(
                session_id=session_id,
                tenant_id=tenant_id,
                operator_id=operator_id,
                event_type="APPROVAL_GATE",
                tool_name=proposed_tool,
                payload={"request_id": approval_req.request_id, "action_type": action_type},
                blast_radius=blast_radius,
                status="PENDING",
            )

            return AgentTurnOutput(
                session_id=session_id,
                tenant_id=tenant_id,
                operator_id=operator_id,
                status="AWAITING_APPROVAL",
                user_explanation=(
                    f"Agent formulated remediation plan: {action_type}. "
                    f"Due to {blast_radius} blast radius, action is paused awaiting operator sign-off in review queue."
                ),
                diagnostic_evidence=[diag_telemetry, diag_logs],
                pending_approval=approval_req,
                audit_records_generated=len(self.audit_store.get_all_records()) - initial_records_count,
            )

        # Step 5: Approved Execution (Execute Tool + Register Compensating Undo Action)
        t0 = time.perf_counter()
        self.audit_store.log_tool_call(
            session_id=session_id,
            tenant_id=tenant_id,
            operator_id=operator_id,
            tool_name=proposed_tool,
            arguments={**proposed_args, "approval_token": approval_token},
            blast_radius=blast_radius,
        )

        exec_res = {"status": "SUCCESS", "message": "Service payment-api restarted successfully."}
        lat3 = (time.perf_counter() - t0) * 1000.0

        self.audit_store.log_tool_outcome(
            session_id=session_id,
            tenant_id=tenant_id,
            operator_id=operator_id,
            tool_name=proposed_tool,
            output=exec_res,
            status="SUCCESS",
            latency_ms=round(lat3, 2),
            blast_radius=blast_radius,
        )

        # Register Compensating Action (Reversible Undo)
        comp_action = self.compensating_registry.register_action(
            session_id=session_id,
            tenant_id=tenant_id,
            mutating_tool=proposed_tool,
            forward_parameters=proposed_args,
            inverse_action_name="rollback_pod_restart_or_scale",
            inverse_parameters={"service": "payment-api", "revert_replicas": 4},
            state_before={"replicas": 4, "version": "v2.4.1"},
        )

        return AgentTurnOutput(
            session_id=session_id,
            tenant_id=tenant_id,
            operator_id=operator_id,
            status="RESOLVED",
            user_explanation=(
                f"Remediation action {action_type} executed under approval token {approval_token}. "
                "Service health restored. Reversible compensating action registered."
            ),
            diagnostic_evidence=[diag_telemetry, diag_logs],
            executed_actions=[exec_res],
            reversible_actions=[comp_action],
            audit_records_generated=len(self.audit_store.get_all_records()) - initial_records_count,
        )
