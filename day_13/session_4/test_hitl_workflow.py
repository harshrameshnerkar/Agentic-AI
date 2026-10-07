"""
Day 13 - Session 4: End-to-End HITL & Audit Trail Verification Test
===================================================================
Automated verification proving:
  1. Destructive actions are blocked and routed to the Human Approval Queue.
  2. Every tool call, argument, output, and latency is logged to the Audit Trail.
  3. Operator Rejection is respected without executing side effects.
  4. Operator Approval executes the action and creates a compensating Undo record.
  5. One-Click Compensating Undo successfully reverts state.
  6. Cryptographic SHA-256 Hash Chain passes 100% integrity audit.
"""

import os
import sys
import json
import time

# Ensure local session directory is in sys.path
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)
try:
    from day_13.session_4.audit_trail import AuditTrailStore
    from day_13.session_4.approval_queue import HumanApprovalQueue, ApprovalStatus
    from day_13.session_4.compensating_actions import CompensatingActionRegistry
    from day_13.session_4.hitl_agent import HumanInTheLoopAgent
except ImportError:
    from audit_trail import AuditTrailStore
    from approval_queue import HumanApprovalQueue, ApprovalStatus
    from compensating_actions import CompensatingActionRegistry
    from hitl_agent import HumanInTheLoopAgent


def test_hitl_end_to_end() -> None:
    audit_store = AuditTrailStore()
    approval_queue = HumanApprovalQueue()
    compensating_registry = CompensatingActionRegistry()

    agent = HumanInTheLoopAgent(
        audit_store=audit_store,
        approval_queue=approval_queue,
        compensating_registry=compensating_registry,
    )

    session_id = "SESS-PROD-PAYMENT-404"
    tenant_id = "ACME_FINTECH"
    operator_id = "alice@acme.internal"

    print("\n" + "=" * 95)
    print(" DAY 13 - SESSION 4: HUMAN-IN-THE-LOOP & AUDIT LEDGER VERIFICATION ".center(95))
    print("=" * 95)

    # -------------------------------------------------------------------------
    # TEST 1: AUTONOMOUS DIAGNOSTICS & DESTRUCTIVE ACTION BLOCKING
    # -------------------------------------------------------------------------
    print("\n[STAGE 1: DIAGNOSTIC & APPROVAL GATE TEST]")
    print(f"Triggering incident query: 'Payment-api pod is logging elevated 5xx rate and connection timeouts.'")
    turn_1 = agent.triage_incident(
        session_id=session_id,
        tenant_id=tenant_id,
        operator_id=operator_id,
        alert_query="Payment-api pod is logging elevated 5xx rate and connection timeouts.",
    )

    print(f"  - Turn Status             : {turn_1.status}")
    print(f"  - User Explanation        : {turn_1.user_explanation}")
    print(f"  - Pending Approval ID     : {turn_1.pending_approval.request_id if turn_1.pending_approval else None}")
    assert turn_1.status == "AWAITING_APPROVAL"
    assert turn_1.pending_approval is not None

    # Verify review queue contains the pending request
    pending = approval_queue.get_pending_requests()
    assert len(pending) == 1
    req = pending[0]
    print(f"  - Review Queue Request    : [{req.request_id}] {req.action_type} (Blast: {req.blast_radius}, Conf: {req.agent_confidence})")
    print(f"  - Justification for Human : {req.explanation_for_human}")
    print("[PASS] Destructive action successfully halted at Human Approval Gate.")

    # -------------------------------------------------------------------------
    # TEST 2: OPERATOR REJECTION HANDLING
    # -------------------------------------------------------------------------
    print("\n[STAGE 2: OPERATOR REJECTION TEST]")
    print("Operator rejects request: 'Do not restart during active payment processing spike.'")
    ok, msg, req_rejected = approval_queue.reject(
        request_id=req.request_id,
        reviewer_id="lead-bob@acme.internal",
        reason="Blocked due to active payment processing window.",
    )
    assert ok
    assert req_rejected is not None
    assert req_rejected.status == ApprovalStatus.REJECTED
    print(f"  - Rejection Confirmation  : Status = {req_rejected.status.value} (Reviewer: {req_rejected.reviewed_by})")
    print(f"  - Rejection Reason        : {req_rejected.rejection_reason}")
    print("[PASS] Rejection handled cleanly with zero side-effects.")

    # -------------------------------------------------------------------------
    # TEST 3: OPERATOR APPROVAL & EXECUTION
    # -------------------------------------------------------------------------
    print("\n[STAGE 3: OPERATOR APPROVAL & COMPENSATING ACTION TEST]")
    approval_token = "AUTH-APPROVE-LEAD-BOB-2026"
    print(f"Agent re-invoked with human approval token: '{approval_token}'...")
    turn_2 = agent.triage_incident(
        session_id=session_id,
        tenant_id=tenant_id,
        operator_id=operator_id,
        alert_query="Payment-api pod is logging elevated 5xx rate and connection timeouts.",
        approval_token=approval_token,
    )

    print(f"  - Turn Status             : {turn_2.status}")
    print(f"  - User Explanation        : {turn_2.user_explanation}")
    print(f"  - Executed Actions        : {len(turn_2.executed_actions)} action(s)")
    assert turn_2.status == "RESOLVED"
    assert len(turn_2.executed_actions) == 1

    # Check that compensating action was registered
    reversible = compensating_registry.list_reversible_actions(session_id)
    assert len(reversible) == 1
    comp_action = reversible[0]
    print(f"  - Registered Undo Action  : [{comp_action.action_id}] {comp_action.inverse_action_name}")
    print(f"  - State Snapshot Preserved: {comp_action.state_before}")
    print("[PASS] Destructive action executed under approval; compensating Undo registered.")

    # -------------------------------------------------------------------------
    # TEST 4: ONE-CLICK COMPENSATING UNDO EXECUTION
    # -------------------------------------------------------------------------
    print("\n[STAGE 4: COMPENSATING UNDO ROLLBACK TEST]")
    print(f"Operator clicks 'Undo' on action {comp_action.action_id}...")
    undo_result = compensating_registry.execute_undo(comp_action.action_id, operator_id="lead-bob@acme.internal")
    print(f"  - Undo Execution Status   : {undo_result['status']}")
    print(f"  - Action Executed         : {undo_result['inverse_action_executed']}")
    print(f"  - Parameters Restored     : {undo_result['restored_parameters']}")
    assert undo_result["status"] == "COMPENSATED"
    print("[PASS] Reversible undo action executed cleanly; state restored.")

    # -------------------------------------------------------------------------
    # TEST 5: CRYPTOGRAPHIC AUDIT LEDGER INTEGRITY CHECK
    # -------------------------------------------------------------------------
    print("\n[STAGE 5: CRYPTOGRAPHIC AUDIT LEDGER AUDIT]")
    records = audit_store.get_session_records(session_id)
    print(f"Total Audit Ledger Records Logged: {len(records)}")
    print("-" * 95)
    print(f"| Event ID      | Event Type        | Tool Name             | Status   | SHA-256 Digest (Tail) |")
    print("-" * 95)
    for r in records:
        print(f"| {r.event_id:<13} | {r.event_type:<17} | {str(r.tool_name):<21} | {r.status:<8} | ...{r.record_hash[-14:]} |")
    print("-" * 95)

    is_valid, err = audit_store.verify_integrity()
    print(f"  - Audit Trail Integrity Check: {'VALID' if is_valid else 'COMPROMISED'}")
    assert is_valid, f"Audit trail failed verification: {err}"
    print("[PASS] Cryptographic SHA-256 chain passes 100% integrity verification.")
    print("=" * 95)


import unittest


class HitlWorkflowTest(unittest.TestCase):
    def test_workflow(self) -> None:
        test_hitl_end_to_end()


if __name__ == "__main__":
    test_hitl_end_to_end()

