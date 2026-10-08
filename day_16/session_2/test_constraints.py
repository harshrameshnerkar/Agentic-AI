"""Day 16 - Session 2: Unit & Integration Test Suite for Constraints & HITL Gate."""

import os
import time
import unittest

try:
    from .constraints_validator import (
        SignedOffMetrics,
        SecretMasker,
        BlacklistEnforcer,
        BlastRadiusClassifier,
        CryptographicHITLGateway,
        ComplianceEvaluator,
    )
except ImportError:
    from constraints_validator import (
        SignedOffMetrics,
        SecretMasker,
        BlacklistEnforcer,
        BlastRadiusClassifier,
        CryptographicHITLGateway,
        ComplianceEvaluator,
    )


class TestDay16Session2ConstraintsSuite(unittest.TestCase):
    """Test suite for signed-off metrics, secret scrubbing, blacklist, and HITL gate."""

    def setUp(self):
        self.metrics = SignedOffMetrics()
        self.gateway = CryptographicHITLGateway(secret_key="test-secret-key-123")
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

    def test_signed_off_metrics_thresholds(self):
        """Verifies the 6 exact signed-off numeric target metrics."""
        self.assertEqual(self.metrics.diagnostic_accuracy_min, 0.95)
        self.assertEqual(self.metrics.p95_latency_max_sec, 90.0)
        self.assertEqual(self.metrics.p50_latency_max_sec, 45.0)
        self.assertEqual(self.metrics.cost_ceiling_max_usd, 0.15)
        self.assertEqual(self.metrics.unattended_destructive_writes_max, 0)
        self.assertEqual(self.metrics.secret_mask_rate_min, 1.0)
        self.assertEqual(self.metrics.mttr_reduction_min, 0.80)

    def test_secret_masker(self):
        """Verifies robust redaction of credentials, API tokens, and PII."""
        sample_log = (
            "User admin with password='SuperSecretPassword123' encountered error. "
            "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9. "
            "OpenAI token: sk-1234567890abcdef1234567890. "
            "Contact user at dev-ops@company.internal or card 4111-2222-3333-4444."
        )

        masked, secret_cnt, pii_cnt = SecretMasker.mask_text(sample_log)
        self.assertGreaterEqual(secret_cnt, 2)
        self.assertGreaterEqual(pii_cnt, 2)
        self.assertNotIn("SuperSecretPassword123", masked)
        self.assertNotIn("sk-1234567890abcdef1234567890", masked)
        self.assertNotIn("4111-2222-3333-4444", masked)
        self.assertIn("[REDACTED_SECRET]", masked)
        self.assertIn("[REDACTED_PII]", masked)

    def test_blacklist_enforcer(self):
        """Verifies rejection of all 5 'Never Automate' red lines and acceptance of safe commands."""
        # Red lines that must be rejected
        bad_commands = [
            "DROP TABLE users_production;",
            "TRUNCATE TABLE billing_ledger;",
            "kubectl delete pvc redis-data-pvc",
            "aws iam delete-user --user-name admin",
            "git push origin main --force",
            "kill_switch disable",
        ]

        for cmd in bad_commands:
            allowed, reason = BlacklistEnforcer.inspect_command(cmd)
            self.assertFalse(allowed, f"Should have blocked command: {cmd}")
            self.assertIsNotNone(reason)

        # Safe commands that must be allowed
        safe_commands = [
            "kubectl get pods -n prod-core",
            "curl -s http://localhost:8000/metrics",
            "SELECT count(*) FROM latency_traces WHERE status=500;",
            "git log -n 5 --oneline",
        ]

        for cmd in safe_commands:
            allowed, reason = BlacklistEnforcer.inspect_command(cmd)
            self.assertTrue(allowed, f"Should have allowed safe command: {cmd}")
            self.assertIsNone(reason)

    def test_blast_radius_classification(self):
        """Verifies 3-tier classification of operations."""
        self.assertEqual(
            BlastRadiusClassifier.classify("query_metrics"), "TIER_1_READ_ONLY"
        )
        self.assertEqual(
            BlastRadiusClassifier.classify("fetch_logs"), "TIER_1_READ_ONLY"
        )
        self.assertEqual(
            BlastRadiusClassifier.classify("drain_read_replica"),
            "TIER_2_LOW_RISK_REBALANCE",
        )
        self.assertEqual(
            BlastRadiusClassifier.classify("restart_pod"),
            "TIER_3_DESTRUCTIVE_WRITE",
        )
        self.assertEqual(
            BlastRadiusClassifier.classify("rollback_deployment"),
            "TIER_3_DESTRUCTIVE_WRITE",
        )
        # Unknown tool must default to Tier 3
        self.assertEqual(
            BlastRadiusClassifier.classify("unknown_custom_tool"),
            "TIER_3_DESTRUCTIVE_WRITE",
        )

    def test_cryptographic_hitl_lifecycle(self):
        """Verifies HMAC token generation, verification, expiration, and tampering detection."""
        incident_id = "INC-101"
        action = "restart_pod"
        params = {"pod": "payment-api-0"}

        # 1. Generate token
        req = self.gateway.generate_approval_request(
            incident_id, action, params, ttl_minutes=15
        )
        token = req["approval_token"]
        expires_at = req["expires_at"]
        self.assertEqual(req["status"], "AWAITING_APPROVAL")

        # 2. Approve with valid token
        ok, msg = self.gateway.verify_and_approve(
            incident_id, action, params, expires_at, token, "lead.sre@corp.com"
        )
        self.assertTrue(ok)
        self.assertEqual(msg, "APPROVED_SUCCESSFULLY")
        self.assertEqual(len(self.gateway.audit_log), 1)

        # 3. Reject tampered token
        tampered_token = token[:-4] + "ffff"
        ok, msg = self.gateway.verify_and_approve(
            incident_id, action, params, expires_at, tampered_token, "lead.sre@corp.com"
        )
        self.assertFalse(ok)
        self.assertIn("INVALID_SIGNATURE", msg)

        # 4. Reject expired token
        past_time = int(time.time()) - 100
        ok, msg = self.gateway.verify_and_approve(
            incident_id, action, params, past_time, token, "lead.sre@corp.com"
        )
        self.assertFalse(ok)
        self.assertIn("TOKEN_EXPIRED", msg)

    def test_compliance_evaluator(self):
        """Verifies compliance certification logic under pass and fail scenarios."""
        evaluator = ComplianceEvaluator()

        # Passing runs
        passing_runs = [
            {
                "is_correct": True,
                "latency_sec": 40.0,
                "cost_usd": 0.08,
                "tier3_unapproved": False,
                "unmasked_secrets_count": 0,
                "human_mttr_min": 85.0,
                "agent_mttr_min": 2.0,
            }
        ] * 20

        cert_pass = evaluator.evaluate_batch(passing_runs)
        self.assertEqual(cert_pass["overall_status"], "COMPLIANT_PASSED")

        # Failing runs (accuracy too low)
        failing_runs = [
            {
                "is_correct": False,
                "latency_sec": 40.0,
                "cost_usd": 0.08,
                "tier3_unapproved": False,
                "unmasked_secrets_count": 0,
                "human_mttr_min": 85.0,
                "agent_mttr_min": 2.0,
            }
        ] * 20

        cert_fail = evaluator.evaluate_batch(failing_runs)
        self.assertEqual(cert_fail["overall_status"], "NON_COMPLIANT_FAILED")

    def test_markdown_artifacts(self):
        """Verifies presence and depth of Signed-Off Metrics and HITL Agreement documents."""
        metrics_doc = os.path.join(self.base_dir, "SIGNED_OFF_SUCCESS_METRICS.md")
        hitl_doc = os.path.join(self.base_dir, "HITL_BOUNDARY_AGREEMENT.md")

        for doc in [metrics_doc, hitl_doc]:
            self.assertTrue(os.path.isfile(doc), f"Missing document: {doc}")
            with open(doc, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertGreater(len(content), 1000)

        # Verify key contents in metrics document
        with open(metrics_doc, "r", encoding="utf-8") as f:
            m_text = f.read()
            self.assertIn("Diagnostic Accuracy", m_text)
            self.assertIn("p95 Triage Latency", m_text)
            self.assertIn("Cost Per Triage Run", m_text)
            self.assertIn("FORMAL STAKEHOLDER SIGN-OFF", m_text)

        # Verify key contents in HITL agreement
        with open(hitl_doc, "r", encoding="utf-8") as f:
            h_text = f.read()
            self.assertIn("3-Tier Blast-Radius", h_text)
            self.assertIn("NEVER AUTOMATE", h_text)
            self.assertIn("HMAC-SHA256", h_text)
            self.assertIn("Emergency Kill Switch", h_text)


if __name__ == "__main__":
    unittest.main()
