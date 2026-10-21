"""Tests for BatchPipelineRunner and CostTracker (Day 5 requirements)."""

from __future__ import annotations
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure week5 directory is on path
WEEK5_DIR = Path(__file__).resolve().parent.parent
if str(WEEK5_DIR) not in sys.path:
    sys.path.insert(0, str(WEEK5_DIR))

from src.batch_runner import BatchExecutionSummary, BatchPipelineRunner, ProcessedDocumentRecord
from src.cost_tracker import CostTracker, ScalingProjection, UnitEconomics

DOCS_DIR = WEEK5_DIR / "data" / "documents"


class TestBatchPipelineAndCost(unittest.TestCase):
    """Verifies batch execution, crash survival on bad files, atomic checkpointing, and cost tracking."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cost_tracker = CostTracker()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_batch_runner_fault_tolerance_on_corrupt_files(self):
        """Ensures the batch pipeline survives corrupted files mid-run without losing prior work."""
        doc1 = DOCS_DIR / "doc_001.pdf"
        corrupt_doc = DOCS_DIR / "doc_069_corrupt.pdf"
        doc2 = DOCS_DIR / "doc_002.pdf"

        if not doc1.exists() or not corrupt_doc.exists() or not doc2.exists():
            self.skipTest("Sample test documents not found in data/documents")

        runner = BatchPipelineRunner(output_dir=self.temp_dir)
        records, summary = runner.run_batch([doc1, corrupt_doc, doc2])

        self.assertEqual(summary.total_documents, 3)
        self.assertEqual(summary.succeeded_count, 2)
        self.assertEqual(summary.failed_count, 1)

        # Check failures.jsonl exists and logs corrupt document
        failures_path = self.temp_dir / "failures.jsonl"
        self.assertTrue(failures_path.exists())
        fail_content = failures_path.read_text(encoding="utf-8")
        self.assertIn("doc_069_corrupt", fail_content)

        # Check predictions.jsonl exists and logs successful extractions
        predictions_path = self.temp_dir / "predictions.jsonl"
        self.assertTrue(predictions_path.exists())
        pred_content = predictions_path.read_text(encoding="utf-8")
        self.assertIn("doc_001", pred_content)
        self.assertIn("doc_002", pred_content)

    def test_batch_runner_checkpoint_and_resume(self):
        """Verifies atomic state checkpointing allows resuming without repeating work."""
        doc1 = DOCS_DIR / "doc_001.pdf"
        doc2 = DOCS_DIR / "doc_002.pdf"
        if not doc1.exists() or not doc2.exists():
            self.skipTest("Sample documents not found")

        runner = BatchPipelineRunner(output_dir=self.temp_dir)

        # First run on doc1
        records1, summary1 = runner.run_batch([doc1])
        self.assertEqual(summary1.succeeded_count, 1)

        checkpoint_path = self.temp_dir / "batch_checkpoint.json"
        self.assertTrue(checkpoint_path.exists())

        # Second run with doc1 and doc2 resuming from checkpoint
        records2, summary2 = runner.run_batch([doc1, doc2], resume_from_checkpoint=True)
        self.assertEqual(summary2.succeeded_count, 2)

    def test_cost_tracker_unit_economics(self):
        """Verifies token measurement and unit cost calculation."""
        unit: UnitEconomics = self.cost_tracker.calculate_unit_economics()
        self.assertGreater(unit.avg_input_tokens, 0)
        self.assertGreater(unit.avg_output_tokens, 0)
        self.assertGreater(unit.unit_cost_usd, 0.0)
        self.assertLess(unit.unit_cost_usd, 0.01)  # Fraction of a cent

    def test_cost_tracker_10k_scaling_model(self):
        """Verifies 10,000-document enterprise scaling projection and ROI savings."""
        proj: ScalingProjection = self.cost_tracker.calculate_projection(volume=10000)
        self.assertEqual(proj.monthly_document_volume, 10000)
        self.assertEqual(proj.auto_approval_rate_pct, 85.0)

        # Cost reduction must exceed 90%
        self.assertGreaterEqual(proj.cost_reduction_pct, 90.0)
        self.assertGreater(proj.monthly_savings_usd, 12000.0)
        self.assertGreater(proj.annual_savings_usd, 140000.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
