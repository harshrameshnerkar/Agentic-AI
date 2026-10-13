"""
Day 13 - Session 04: Human-in-the-Loop & Audit Trails
Demonstrates:
1. Operator review station & approval queue for high blast-radius actions.
2. Cryptographic HMAC audit trail logging.
3. Compensating rollback actions on failure.
"""

from __future__ import annotations
from approval_queue import HumanApprovalQueue, ApprovalStatus
from audit_trail import AuditTrailStore
from test_hitl_workflow import test_hitl_end_to_end


def demo_approval_station():
    print("\n--- 1. Operator Approval Station ---")
    queue = HumanApprovalQueue()
    req = queue.submit_request(
        session_id="SESS-01",
        tenant_id="ACME_FINTECH",
        action_type="RESTART_SERVICE",
        proposed_tool="restart_service",
        tool_parameters={"service": "payment-api"},
        blast_radius="HIGH",
        agent_confidence=0.94,
        explanation_for_human="Memory leak detected in payment-api.",
        evidence_citations=["Error rate: 4.2%"],
    )
    print(f"Submitted approval request: {req.request_id} for '{req.action_type}'")

    # Operator approves
    queue.resolve_request(req.request_id, ApprovalStatus.APPROVED, reviewer="SRE Lead")
    resolved = queue.get_request(req.request_id)
    print(f"Request {req.request_id} resolved as: {resolved.status.value}")
    assert resolved.status == ApprovalStatus.APPROVED


def main():
    print("Day 13 Session 04: HITL Governance & Audit Trails\n")
    demo_approval_station()

    print("\n--- 2. Running End-to-End HITL Workflow Test ---")
    test_hitl_end_to_end()
    print("Pass: HITL workflow, approval gates, and rollback tests completed.")


if __name__ == "__main__":
    main()
