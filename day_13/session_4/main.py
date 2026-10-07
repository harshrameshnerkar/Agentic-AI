"""
Day 13 - Session 4: Master CLI & Operator Review Station
========================================================
Implements:
  1. Human-in-the-Loop Verification Test Suite
  2. Operator Review Station (Interactive approval queue management)
  3. Cryptographic Audit Trail Inspector (Viewing and verifying tamper-evident logs)
"""

import os
import sys
import argparse
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
    from day_13.session_4.test_hitl_workflow import test_hitl_end_to_end
except ImportError:
    from audit_trail import AuditTrailStore
    from approval_queue import HumanApprovalQueue, ApprovalStatus
    from compensating_actions import CompensatingActionRegistry
    from hitl_agent import HumanInTheLoopAgent
    from test_hitl_workflow import test_hitl_end_to_end


def print_header(title: str) -> None:
    print("\n" + "=" * 95)
    print(f" {title.center(93)} ")
    print("=" * 95)


def demo_review_station() -> None:
    print_header("OPERATOR REVIEW STATION & APPROVAL QUEUE")
    approval_queue = HumanApprovalQueue()

    # Pre-populate 2 pending requests
    req1 = approval_queue.submit_request(
        session_id="SESS-INC-901",
        tenant_id="ACME_FINTECH",
        action_type="RESTART_SERVICE",
        proposed_tool="restart_service",
        tool_parameters={"service": "payment-api"},
        blast_radius="HIGH",
        agent_confidence=0.94,
        explanation_for_human="Postgres connection pool saturation causing 504 timeouts. Rolling restart required.",
        evidence_citations=["Telemetry error rate: 4.2%", "pgbouncer queue: >120"],
    )

    req2 = approval_queue.submit_request(
        session_id="SESS-INC-902",
        tenant_id="GLOBEX_LOGISTICS",
        action_type="ROLLBACK_DEPLOYMENT",
        proposed_tool="rollback_deployment",
        tool_parameters={"service": "telematics-hub", "target_version": "v1.8.0"},
        blast_radius="CRITICAL",
        agent_confidence=0.88,
        explanation_for_human="Canary v1.8.1 causing memory leak and OOMKilled pods across cluster.",
        evidence_citations=["Memory usage: 98%", "OOMKilled events: 14 in 5 mins"],
    )

    pending = approval_queue.get_pending_requests()
    print(f"Active Pending Requests awaiting Human Review ({len(pending)}):")
    print("-" * 95)
    for r in pending:
        print(f"Request ID   : {r.request_id}")
        print(f"Tenant       : {r.tenant_id} | Session: {r.session_id}")
        print(f"Action       : {r.action_type} (Tool: {r.proposed_tool})")
        print(f"Blast Radius : {r.blast_radius} | Confidence: {r.agent_confidence:.2f}")
        print(f"Explanation  : {r.explanation_for_human}")
        print(f"Evidence     : {'; '.join(r.evidence_citations)}")
        print("-" * 95)

    print("\nSimulating Operator Action on Request 1: APPROVE")
    ok, msg, approved = approval_queue.approve(req1.request_id, reviewer_id="oncall-lead@acme.internal")
    status_str = approved.status.value if approved else "UNKNOWN"
    print(f"  Result: {msg} (Status: {status_str})")

    print("\nSimulating Operator Action on Request 2: REJECT (Hold for maintenance window)")
    ok2, msg2, rejected = approval_queue.reject(req2.request_id, reviewer_id="sre-director@globex.internal", reason="Hold until 02:00 UTC maintenance window.")
    status_str2 = rejected.status.value if rejected else "UNKNOWN"
    reason_str = rejected.rejection_reason if rejected else ""
    print(f"  Result: {msg2} (Status: {status_str2}, Reason: {reason_str})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 13 Session 4: Human-in-the-Loop Design")
    parser.add_argument("--test-hitl", action="store_true", help="Run end-to-end HITL & audit trail test")
    parser.add_argument("--review-station", action="store_true", help="Launch operator review station demo")

    args = parser.parse_args()

    if args.test_hitl:
        test_hitl_end_to_end()
    elif args.review_station:
        demo_review_station()
    else:
        # Default run both
        test_hitl_end_to_end()
        demo_review_station()


if __name__ == "__main__":
    main()
