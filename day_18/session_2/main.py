"""
Day 18 - Session 02: Integration & Safety Delivery Surface
Demonstrates end-to-end integration safety:
1. PII redaction of sensitive credentials and user data.
2. Cryptographic HMAC authorization gates.
3. Tamper-evident SHA-256 audit logging.
"""

from __future__ import annotations
import os
from delivery_surface import ProductionTriageDeliveryService
from safety_guardrails import CryptographicHITLGateway, PIISanitizer
from audit_logger import CryptographicAuditLogger


def main():
    print("Day 18 Session 02: Delivery Surface Safety Controls\n")

    # 1. PII Redaction
    dirty_input = "User test@company.com (SSN: 123-45-6789, token: sk_live_998877) reported incident."
    clean_text, count = PIISanitizer.sanitize(dirty_input)
    print(f"PII Redactions: Applied {count} redactions.")
    print(f"Sanitized: {clean_text}")
    assert count >= 2

    # 2. HITL Flow
    audit_file = os.path.join(os.path.dirname(__file__), "test_audit.jsonl")
    if os.path.exists(audit_file):
        os.remove(audit_file)

    service = ProductionTriageDeliveryService(audit_file)
    res_unauth = service.process_incident(
        incident_id="INC-201",
        service_name="auth-service",
        raw_alert_query="auth-service pod OOMKilled"
    )
    print(f"Unauthorized Tier-3 Action: Status = {res_unauth['execution_status']}")
    assert res_unauth["execution_status"] == "REJECTED_UNAUTHORIZED"

    # Authorized with HMAC
    token = CryptographicHITLGateway.generate_approval_token(
        "INC-201", res_unauth["recommended_action"], "sre-lead@company.com"
    )
    res_auth = service.process_incident(
        incident_id="INC-201",
        service_name="auth-service",
        raw_alert_query="auth-service pod OOMKilled",
        hmac_signature=token,
        approved_by="sre-lead@company.com"
    )
    print(f"Authorized Action: Status = {res_auth['execution_status']}")
    assert res_auth["execution_status"] == "EXECUTED_AUTHORIZED"

    print("\nDelivery surface and security controls verified.")


if __name__ == "__main__":
    main()
