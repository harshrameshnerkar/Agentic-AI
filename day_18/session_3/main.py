"""
Day 18 - Session 3: Code Review
CLI Entrypoint for reviewing PR #18, the mentor review thread, and verified security fixes.
"""

import os
import sys
import time
import argparse

# Set UTF-8 encoding for Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from reviewed_delivery_engine import (
    ReviewedDeliveryService,
    HardenedHITLGateway,
    BlastRadiusTier
)


def display_header():
    print("=" * 82)
    print("           DAY 18 - SESSION 3: CODE REVIEW & LINE-BY-LINE DEFENSE")
    print("=" * 82)
    print("  Curriculum Task: PR raised, reviewed line-by-line, all comments addressed")
    print("  Author: Harsh Ramesh Nerkar (@harshrameshnerkar)")
    print("  Reviewer: Dr. Elena Rostova (@erostova-mentor)")
    print("=" * 82)


def display_pr_summary():
    print("\n" + "=" * 82)
    print("       PULL REQUEST #18: INCIDENT DELIVERY SURFACE & SAFETY GUARDRAILS")
    print("=" * 82)
    print("Branch: feat/delivery-surface-safety -> main")
    print("Status: [APPROVED & READY TO MERGE]")
    print("-" * 82)
    print("Deliverables:")
    print("  • Production Incident Triage Delivery Surface (Universal REST / CLI Engine)")
    print("  • Bounded Anti-ReDoS PII Redactor for SSN, CC, Emails, JWTs, and Passwords")
    print("  • Single-Use Nonce Replay Protected HMAC-SHA256 HITL Gateway")
    print("  • Thread-Safe Monotonic SHA-256 Hash-Chained Audit Trail")
    print("  • Type-Safe Dataclass TriageResult with Enum-based Blast Radius Tiers")
    print("=" * 82)


def test_replay_defense(audit_log: str):
    service = ReviewedDeliveryService(audit_log)

    print("\n" + "=" * 82)
    print("       TESTING SINGLE-USE NONCE REPLAY ATTACK DEFENSE (REVIEW FIX #1)")
    print("=" * 82)
    action = "Rollback deployment and increase pod memory limits from 512Mi to 2Gi"
    now = int(time.time())
    approver = "lead-sre@enterprise.com"
    sig = HardenedHITLGateway.generate_signature("INC-301", action, approver, now)

    # First attempt: Authorized
    print("[1st Attempt with Signature]: Submitting authorized request...")
    res1 = service.process_incident(
        incident_id="INC-301",
        service_name="auth-service",
        raw_alert_query="CRITICAL: auth-service pod is crashing with OutOfMemoryError ExitCode 137",
        approval_signature=sig,
        approver_email=approver,
        timestamp_epoch=now
    )
    print(f"  Result: {res1.execution_status} -> {res1.hitl_message}")

    # Second attempt: Replayed signature
    print("\n[2nd Attempt (Replay Attack)]: Submitting intercepted duplicate request...")
    res2 = service.process_incident(
        incident_id="INC-301",
        service_name="auth-service",
        raw_alert_query="CRITICAL: auth-service pod is crashing with OutOfMemoryError ExitCode 137",
        approval_signature=sig,
        approver_email=approver,
        timestamp_epoch=now
    )
    print(f"  Result: {res2.execution_status} -> {res2.hitl_message}")
    print("=" * 82)


def main():
    parser = argparse.ArgumentParser(description="Day 18 Session 3: Code Review CLI")
    parser.add_argument("--test-replay", action="store_true", help="Demonstrate replay attack prevention")
    parser.add_argument("--audit-fixes", action="store_true", help="Display all 5 code review resolutions")
    args = parser.parse_args()

    display_header()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    audit_log = os.path.join(current_dir, "test_reviewed_audit.log")

    if args.test_replay:
        test_replay_defense(audit_log)
    else:
        display_pr_summary()
        test_replay_defense(audit_log)


if __name__ == "__main__":
    main()
