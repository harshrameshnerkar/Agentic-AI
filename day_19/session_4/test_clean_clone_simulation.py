import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from clean_clone_runner import CleanCloneSandboxRunner


class TestCleanCloneVerification(unittest.TestCase):
    """Test suite for clean-clone unaided execution."""

    def setUp(self):
        self.runner = CleanCloneSandboxRunner()

    def test_load_audit_metadata(self):
        """Verify audit record structure and reviewer information."""
        meta = self.runner.load_audit_metadata()
        self.assertEqual(meta.get("reviewer_name"), "Alex Chen")
        self.assertEqual(meta.get("target_commit"), "728b238")
        verif = meta.get("verification_results", {})
        self.assertTrue(verif.get("unaided_execution"))
        self.assertEqual(verif.get("regression_suite_pass_rate"), 100.0)

    def test_documentation_bugs_resolution(self):
        """Verify all identified documentation bugs are marked FIXED."""
        meta = self.runner.load_audit_metadata()
        bugs = meta.get("documentation_bugs_found", [])
        self.assertGreaterEqual(len(bugs), 3)
        for b in bugs:
            self.assertEqual(b.get("status"), "FIXED")
            self.assertIn("DOC-BUG-", b.get("id"))

    def test_zero_interactive_blocking_prompts(self):
        """Verify no interactive input() calls block headless automation."""
        count = self.runner.scan_for_interactive_blocks(self.runner.base_dir)
        self.assertEqual(count, 0, f"Found {count} interactive input() calls that would block automation.")

    def test_sandbox_simulation_execution(self):
        """Verify sandbox runner simulates execution successfully."""
        result = self.runner.run_sandbox_simulation()
        self.assertTrue(result.is_success)
        self.assertEqual(result.interactive_prompts_found, 0)
        self.assertEqual(result.eval_pass_rate, 100.0)
        self.assertEqual(result.verdict, "APPROVED_FOR_PRODUCTION_HANDOVER")

    def test_missing_audit_path_resilience(self):
        """Verify fallback behavior if audit file is missing."""
        bad_runner = CleanCloneSandboxRunner(base_dir="/tmp/non_existent_sandbox_path")
        meta = bad_runner.load_audit_metadata()
        self.assertEqual(meta, {})


if __name__ == "__main__":
    unittest.main()
