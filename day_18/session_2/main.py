"""
Day 18 - Session 2: Integration & Safety
CLI Entrypoint for testing delivery surface, PII redaction, HMAC approval, and audit verification.
"""

import os
import sys
import json
import time
import argparse

# Set UTF-8 encoding for Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from delivery_surface import ProductionTriageDeliveryService
from safety_guardrails import CryptographicHITLGateway, PIISanitizer
from audit_logger import CryptographicAuditLogger


def display_header():
    print("=" * 82)
    print("       DAY 18 - SESSION 2: INTEGRATION & SAFETY DELIVERY SURFACE")
    print("=" * 82)
    print("  Curriculum Task: System runs end-to-end with guardrails & audit logging active")
    print("  Components: Delivery Surface + PII Redaction + HMAC HITL + SHA-256 Audit Trail")
    print("=" * 82)


def test_pii_redaction():
    print("\n" + "=" * 82)
    print("             TESTING PII REDACTION GUARDRAIL")
    print("=" * 82)
    dirty_input = (
        "CRITICAL: User john.doe@enterprise.com (SSN: 123-45-6789, CC: 4532-1234-5678-9012) "
        "reported payment crash with api_key='sk_live_9988776655443322' and JWT eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xyz.123"
    )
    clean_text, count = PIISanitizer.sanitize(dirty_input)
    print(f"Raw Input Alert:\n  {dirty_input}\n")
    print(f"Sanitized Output ({count} redactions applied):\n  {clean_text}")
    print("=" * 82)


def test_hitl_flows(audit_log: str):
    service = ProductionTriageDeliveryService(audit_log)

    print("\n" + "=" * 82)
    print("   TESTING TIER 3 HITL GATEWAY: UNAUTHORIZED vs. CRYPTOGRAPHICALLY AUTHORIZED")
    print("=" * 82)

    # 1. Without signature (should block)
    print("\n[SCENARIO 1: ATTEMPTING EXECUTION WITHOUT HMAC SIGNATURE]")
    res1 = service.process_incident(
        incident_id="INC-201",
        service_name="auth-service",
        raw_alert_query="CRITICAL: auth-service pod is crashing with OutOfMemoryError ExitCode 137"
    )
    print(f"  • Blast Radius     : {res1['blast_radius_tier']}")
    print(f"  • Execution Status : {res1['execution_status']}")
    print(f"  • Gateway Message  : {res1['hitl_message']}")

    # 2. With valid HMAC signature (should authorize)
    print("\n[SCENARIO 2: AUTHORIZING EXECUTION VIA CRYPTOGRAPHIC HMAC SIGNATURE]")
    now = int(time.time())
    approver = "lead-sre@enterprise.com"
    valid_sig = CryptographicHITLGateway.generate_approval_signature(
        "INC-202", res1["proposed_remediation"], approver, now
    )

    res2 = service.process_incident(
        incident_id="INC-202",
        service_name="auth-service",
        raw_alert_query="CRITICAL: auth-service pod is crashing with OutOfMemoryError ExitCode 137",
        approval_signature=valid_sig,
        approver_email=approver,
        timestamp_epoch=now
    )
    print(f"  • Approver         : {approver}")
    print(f"  • HMAC Signature   : {valid_sig[:24]}...")
    print(f"  • Execution Status : {res2['execution_status']}")
    print(f"  • Gateway Message  : {res2['hitl_message']}")
    print("=" * 82)


def verify_audit_log(audit_log: str):
    logger = CryptographicAuditLogger(audit_log)
    valid, count, msg = logger.verify_chain_integrity()
    print("\n" + "=" * 82)
    print("              CRYPTOGRAPHIC AUDIT LOG INTEGRITY VERIFICATION")
    print("=" * 82)
    print(f"Log File: {audit_log}")
    print(f"Status  : {'[✓] INTEGRITY VERIFIED' if valid else '[✗] INTEGRITY COMPROMISED'}")
    print(f"Details : {msg}")
    print("=" * 82)


def main():
    parser = argparse.ArgumentParser(description="Day 18 Session 2: Integration & Safety CLI")
    parser.add_argument("--test-pii", action="store_true", help="Demonstrate PII redaction")
    parser.add_argument("--test-hitl", action="store_true", help="Demonstrate HITL approval gate")
    parser.add_argument("--verify-audit", action="store_true", help="Verify cryptographic audit trail")
    args = parser.parse_args()

    display_header()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    audit_log = os.path.join(current_dir, "audit_trail.log")

    if args.test_pii:
        test_pii_redaction()
    elif args.test_hitl:
        test_hitl_flows(audit_log)
    elif args.verify_audit:
        verify_audit_log(audit_log)
    else:
        test_pii_redaction()
        test_hitl_flows(audit_log)
        verify_audit_log(audit_log)


if __name__ == "__main__":
    main()
