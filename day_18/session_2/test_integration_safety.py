"""
Unit and Integration Tests for Day 18 Session 2: Integration & Safety.
Verifies PII masking, HMAC approval gateway, delivery surface execution, and audit trail integrity.
"""

import os
import sys
import time
import unittest

# Ensure current session directory is on path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from safety_guardrails import PIISanitizer, BlastRadiusClassifier, CryptographicHITLGateway
from audit_logger import CryptographicAuditLogger
from delivery_surface import ProductionTriageDeliveryService


class TestIntegrationSafety(unittest.TestCase):

    def setUp(self):
        self.test_audit_path = os.path.join(CURRENT_DIR, "test_audit_trail.log")
        if os.path.exists(self.test_audit_path):
            os.remove(self.test_audit_path)
        self.service = ProductionTriageDeliveryService(self.test_audit_path)

    def tearDown(self):
        if os.path.exists(self.test_audit_path):
            os.remove(self.test_audit_path)

    def test_pii_sanitization_patterns(self):
        """Verifies that all 5 PII categories are redacted without corrupting text."""
        raw_text = (
            "Admin user dev@enterprise.com with SSN 000-11-2222 and card 1111-2222-3333-4444 "
            "leaked password='SuperSecretPassword123' and token eyJhbGciOiJIUzI1NiJ9.test.abc"
        )
        clean, count = PIISanitizer.sanitize(raw_text)

        self.assertGreaterEqual(count, 5)
        self.assertNotIn("000-11-2222", clean)
        self.assertNotIn("1111-2222-3333-4444", clean)
        self.assertNotIn("dev@enterprise.com", clean)
        self.assertNotIn("SuperSecretPassword123", clean)
        self.assertNotIn("eyJhbGciOiJIUzI1NiJ9", clean)

        self.assertIn("[REDACTED_SSN]", clean)
        self.assertIn("[REDACTED_CREDIT_CARD]", clean)
        self.assertIn("[REDACTED_EMAIL]", clean)
        self.assertIn("[REDACTED_SECRET]", clean)
        self.assertIn("[REDACTED_JWT_TOKEN]", clean)

    def test_hitl_gateway_blocks_unauthorized_tier3(self):
        """Verifies that Tier 3 consequential actions are blocked without HMAC signature."""
        res = self.service.process_incident(
            incident_id="INC-TEST-01",
            service_name="auth-service",
            raw_alert_query="CRITICAL: auth-service pod is crashing with OutOfMemoryError ExitCode 137"
        )
        self.assertEqual(res["execution_status"], "BLOCKED_HITL_REQUIRED")
        self.assertIn("Tier 3", res["blast_radius_tier"])

    def test_hitl_gateway_allows_valid_hmac(self):
        """Verifies that Tier 3 action executes when verified HMAC signature is provided."""
        action = "Rollback deployment and increase pod memory limits from 512Mi to 2Gi"
        now = int(time.time())
        approver = "lead-sre@enterprise.com"
        valid_sig = CryptographicHITLGateway.generate_approval_signature(
            "INC-TEST-02", action, approver, now
        )

        res = self.service.process_incident(
            incident_id="INC-TEST-02",
            service_name="auth-service",
            raw_alert_query="CRITICAL: auth-service pod is crashing with OutOfMemoryError ExitCode 137",
            approval_signature=valid_sig,
            approver_email=approver,
            timestamp_epoch=now
        )
        self.assertEqual(res["execution_status"], "EXECUTED_WITH_APPROVAL")
        self.assertIn("Authorized by lead-sre@enterprise.com", res["hitl_message"])

    def test_hitl_gateway_rejects_expired_or_invalid_signature(self):
        """Verifies that expired timestamps or tampered signatures are rejected."""
        action = "Rollback deployment and increase pod memory limits from 512Mi to 2Gi"
        expired_time = int(time.time()) - 400  # 400s in the past (clock skew limit is 300s)
        approver = "lead-sre@enterprise.com"
        sig = CryptographicHITLGateway.generate_approval_signature(
            "INC-TEST-03", action, approver, expired_time
        )

        res = self.service.process_incident(
            incident_id="INC-TEST-03",
            service_name="auth-service",
            raw_alert_query="CRITICAL: auth-service pod is crashing with OutOfMemoryError ExitCode 137",
            approval_signature=sig,
            approver_email=approver,
            timestamp_epoch=expired_time
        )
        self.assertEqual(res["execution_status"], "BLOCKED_INVALID_SIGNATURE")

    def test_audit_logger_chain_integrity(self):
        """Verifies that audit logger maintains unbroken SHA-256 hash chaining."""
        logger = CryptographicAuditLogger(self.test_audit_path)
        logger.log_event("INC-A", "EVENT_1", {"msg": "First test event"})
        logger.log_event("INC-B", "EVENT_2", {"msg": "Second test event"})
        logger.log_event("INC-C", "EVENT_3", {"msg": "Third test event"})

        valid, count, msg = logger.verify_chain_integrity()
        self.assertTrue(valid)
        self.assertEqual(count, 3)


if __name__ == "__main__":
    unittest.main()
