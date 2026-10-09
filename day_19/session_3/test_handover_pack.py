import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from handover_validator import HandoverPackValidator


class TestHandoverPack(unittest.TestCase):
    """Test suite for Handover Pack completeness and integrity."""

    def setUp(self):
        self.validator = HandoverPackValidator()

    def test_checklist_items_verification(self):
        """Verify all 8 checklist items exist and are 100% verified."""
        ok, total, verified = self.validator.validate_checklist_json()
        self.assertTrue(ok)
        self.assertEqual(total, 8)
        self.assertEqual(verified, 8)

    def test_markdown_required_sections(self):
        """Verify all 8 mandatory sections exist in HANDOVER_PACK.md."""
        ok, missing = self.validator.validate_markdown_sections()
        self.assertTrue(ok, f"Missing sections in HANDOVER_PACK.md: {missing}")
        self.assertEqual(len(missing), 0)

    def test_cost_model_math(self):
        """Verify mathematical correctness of cost calculations."""
        # Pilot: 1000 queries * $0.0028 + $15.00 = $17.80
        cost_pilot = self.validator.calculate_cost_model(1000, 0.0028, 15.0)
        self.assertAlmostEqual(cost_pilot, 17.80, places=2)

        # Enterprise: 100,000 queries * $0.0028 + $220.00 = $500.00
        cost_fleet = self.validator.calculate_cost_model(100000, 0.0028, 220.0)
        self.assertAlmostEqual(cost_fleet, 500.00, places=2)

    def test_full_validation_status(self):
        """Verify end-to-end report validates successfully."""
        report = self.validator.run_full_validation()
        self.assertTrue(report.is_valid)
        self.assertEqual(report.verified_items, 8)
        self.assertEqual(len(report.missing_sections), 0)

    def test_missing_path_resilience(self):
        """Verify validator handles missing directory gracefully."""
        bad_validator = HandoverPackValidator(base_dir="/tmp/non_existent_dir_xyz")
        report = bad_validator.run_full_validation()
        self.assertFalse(report.is_valid)


if __name__ == "__main__":
    unittest.main()
