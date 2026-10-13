"""
Day 18 - Session 03: Code Review & Replay Defense
Demonstrates security hardening from code review:
1. Replay attack prevention via single-use nonces.
2. Hardened HMAC authorization verification.
"""

from __future__ import annotations
import os
import time
from reviewed_delivery_engine import ReviewedDeliveryService, HardenedHITLGateway


def main():
    print("Day 18 Session 03: Code Review & Replay Attack Defense\n")
    audit_file = os.path.join(os.path.dirname(__file__), "review_audit.jsonl")
    if os.path.exists(audit_file):
        os.remove(audit_file)

    service = ReviewedDeliveryService(audit_file)
    action = "Rollback deployment and increase memory limits"
    now = int(time.time())
    sig = HardenedHITLGateway.generate_signature("INC-301", action, "sre-lead@company.com", now)

    # 1. First execution: Authorized
    res1 = service.process_incident(
        incident_id="INC-301",
        service_name="auth-service",
        raw_alert_query="auth-service pod OOM crash",
        hmac_signature=sig,
        approved_by="sre-lead@company.com",
        timestamp=now
    )
    print(f"1st Attempt (Authorized): {res1['execution_status']}")
    assert res1["execution_status"] == "EXECUTED_AUTHORIZED"

    # 2. Second execution with identical signature (replay attempt): Blocked!
    res2 = service.process_incident(
        incident_id="INC-301",
        service_name="auth-service",
        raw_alert_query="auth-service pod OOM crash",
        hmac_signature=sig,
        approved_by="sre-lead@company.com",
        timestamp=now
    )
    print(f"2nd Attempt (Replay Attack): {res2['execution_status']}")
    assert res2["execution_status"] == "REJECTED_REPLAY_ATTACK"

    print("\nReplay attack defense verified: Single-use nonce rejected duplicate signature.")


if __name__ == "__main__":
    main()
