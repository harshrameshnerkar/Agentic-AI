import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from freeze_auditor import FeatureFreezeAuditor


class TestFeatureFreezeAuditor(unittest.TestCase):
    """Test suite for feature freeze policy enforcement."""

    def setUp(self):
        self.auditor = FeatureFreezeAuditor()

    def test_load_policy_metadata(self):
        """Verify baseline freeze metadata loaded correctly."""
        self.assertEqual(self.auditor.policy.release_tag, "v1.0.0-rc1")
        self.assertEqual(self.auditor.policy.baseline_commit, "728b238")
        self.assertEqual(self.auditor.policy.policy_status, "ACTIVE_FREEZE")
        self.assertTrue(self.auditor.policy.zero_new_features)
        self.assertGreaterEqual(len(self.auditor.policy.approved_backlog), 4)

    def test_reject_feature_commits(self):
        """Verify that feature addition commits are rejected during freeze."""
        disallowed_samples = [
            "feat: add slack interactive notification bot",
            "feature: implement auto-scaling remediation tool",
            "add-api: expose new GraphQL query endpoint",
            "fix: add feature to scrape cloudwatch",
            "random commit without valid prefix"
        ]
        for msg in disallowed_samples:
            allowed, reason = self.auditor.is_commit_allowed(msg)
            self.assertFalse(allowed, f"Expected '{msg}' to be rejected, but got allowed. Reason: {reason}")
            self.assertIn("REJECTED", reason)

    def test_allow_hardening_and_doc_commits(self):
        """Verify that fix, docs, test, and hardening commits are approved."""
        allowed_samples = [
            "fix: bound regex quantifier to prevent ReDoS attack",
            "docs: update clean-clone setup guide in README",
            "test: add 6-vector adversarial chaos test cases",
            "harden: wrap audit logger append in reentrant lock",
            "refactor: clean up unused variable in triage router",
            "chore: bump regression test dataset version"
        ]
        for msg in allowed_samples:
            allowed, reason = self.auditor.is_commit_allowed(msg)
            self.assertTrue(allowed, f"Expected '{msg}' to be allowed, but got rejected. Reason: {reason}")
            self.assertIn("ALLOWED", reason)

    def test_task_category_validation(self):
        """Verify task categories are filtered according to freeze scope."""
        self.assertTrue(self.auditor.is_task_allowed("FIX")[0])
        self.assertTrue(self.auditor.is_task_allowed("DOCS")[0])
        self.assertTrue(self.auditor.is_task_allowed("TEST")[0])
        self.assertTrue(self.auditor.is_task_allowed("HARDENING")[0])

        self.assertFalse(self.auditor.is_task_allowed("NEW_FEATURE")[0])
        self.assertFalse(self.auditor.is_task_allowed("UI_EXPANSION")[0])
        self.assertFalse(self.auditor.is_task_allowed("INTEGRATION_ADDITION")[0])

    def test_policy_fingerprint_integrity(self):
        """Verify deterministic SHA-256 fingerprint generation."""
        fp = self.auditor.compute_policy_fingerprint()
        self.assertEqual(len(fp), 64)
        state = self.auditor.audit_system_state()
        self.assertEqual(state["policy_sha256"], fp)


if __name__ == "__main__":
    unittest.main()
