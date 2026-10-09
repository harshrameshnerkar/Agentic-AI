"""
Unit and Integration Tests for Day 18 Session 3: Code Review Fixes.
Verifies all 5 code review resolutions: single-use nonces, bounded regexes, enum tiers,
thread-safe audit log serialization, and dataclass type safety.
"""

import os
import sys
import time
import threading
import unittest

# Ensure current session directory is on path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from reviewed_delivery_engine import (
    BlastRadiusTier,
    TriageResult,
    HardenedPIISanitizer,
    HardenedBlastRadiusClassifier,
    HardenedHITLGateway,
    ThreadSafeAuditLogger,
    ReviewedDeliveryService
)


class TestCodeReviewFixes(unittest.TestCase):

    def setUp(self):
        self.test_log_path = os.path.join(CURRENT_DIR, "test_review_concurrency.log")
        if os.path.exists(self.test_log_path):
            os.remove(self.test_log_path)

    def tearDown(self):
        if os.path.exists(self.test_log_path):
            os.remove(self.test_log_path)

    def test_nonce_replay_attack_prevention(self):
        """Fix #1: Verifies single-use nonce blocks duplicate execution of valid signature."""
        action = "Rollback deployment"
        now = int(time.time())
        approver = "lead-sre@enterprise.com"
        sig = HardenedHITLGateway.generate_signature("INC-NONCE-1", action, approver, now)

        # 1st attempt: Must succeed
        ok1, msg1 = HardenedHITLGateway.verify_and_consume_approval(
            "INC-NONCE-1", action, approver, now, sig
        )
        self.assertTrue(ok1)
        self.assertIn("verified and consumed", msg1)

        # 2nd attempt: Must be blocked as replay attack
        ok2, msg2 = HardenedHITLGateway.verify_and_consume_approval(
            "INC-NONCE-1", action, approver, now, sig
        )
        self.assertFalse(ok2)
        self.assertIn("REPLAY_ATTACK_DETECTED", msg2)

    def test_bounded_pii_sanitizer_long_input(self):
        """Fix #2: Verifies input length guard prevents ReDoS on massive inputs."""
        massive_input = ("credit card 1234-5678-9012-3456 " * 4000)  # > 100 KB
        clean, count = HardenedPIISanitizer.sanitize(massive_input)
        self.assertGreater(count, 0)
        self.assertIn("[REDACTED_CREDIT_CARD]", clean)

    def test_blast_radius_enum_integrity(self):
        """Fix #3: Verifies Enum return types and frozenset constants."""
        tier3 = HardenedBlastRadiusClassifier.classify_action("rollback deployment")
        self.assertIsInstance(tier3, BlastRadiusTier)
        self.assertEqual(tier3, BlastRadiusTier.TIER_3_CONSEQUENTIAL)

        tier1 = HardenedBlastRadiusClassifier.classify_action("read documentation")
        self.assertEqual(tier1, BlastRadiusTier.TIER_1_READ_ONLY)

    def test_thread_safe_audit_logger_concurrency(self):
        """Fix #4: Verifies thread-safe lock prevents hash chain forks under concurrent writes."""
        logger = ThreadSafeAuditLogger(self.test_log_path)
        threads = []
        errors = []

        def worker(worker_id):
            try:
                for i in range(10):
                    logger.log_event(f"INC-THREAD-{worker_id}", "CONCURRENT_WRITE", {"seq": i})
            except Exception as e:
                errors.append(e)

        # Launch 8 concurrent threads (80 total events)
        for w in range(8):
            t = threading.Thread(target=worker, args=(w,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0)
        valid, count, msg = logger.verify_integrity()
        self.assertTrue(valid, f"Chain corrupted: {msg}")
        self.assertEqual(count, 80, f"Expected 80 events, found {count}")

    def test_typed_dataclass_serialization(self):
        """Fix #5: Verifies TriageResult dataclass attributes and to_dict serialization."""
        res = TriageResult(
            incident_id="INC-T",
            service_name="payment-svc",
            sanitized_query="clean alert",
            root_cause_diagnosis="DB failure",
            proposed_remediation="reboot pod",
            blast_radius_tier=BlastRadiusTier.TIER_3_CONSEQUENTIAL,
            execution_status="BLOCKED_HITL_REQUIRED",
            hitl_message="Awaiting approval",
            audit_hash="abc123hash"
        )
        d = res.to_dict()
        self.assertEqual(d["incident_id"], "INC-T")
        self.assertEqual(d["blast_radius_tier"], BlastRadiusTier.TIER_3_CONSEQUENTIAL.value)


if __name__ == "__main__":
    unittest.main()
