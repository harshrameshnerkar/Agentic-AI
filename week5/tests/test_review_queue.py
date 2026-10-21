"""Independent unit and integration tests for HumanReviewQueue (Day 4 requirements)."""

from __future__ import annotations
import csv
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

from src.review_queue import HumanReviewQueue, ReviewQueueItem


class TestReviewQueue(unittest.TestCase):
    """Verifies queue lifecycle, human actions (Approve, Reject, Override), and CSV persistence."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.json_path = self.temp_dir / "review_queue.json"
        self.csv_path = self.temp_dir / "review_queue.csv"
        self.queue = HumanReviewQueue(
            queue_json_path=self.json_path,
            queue_csv_path=self.csv_path,
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_enqueue_item(self):
        item = self.queue.enqueue(
            document_id="doc_flagged_01",
            filename="doc_flagged_01.pdf",
            doc_type="pdf_scanned",
            confidence_score=0.62,
            review_reasons=["Missing anchor: invoice_id is null"],
            extracted_data={"subtotal": 120.0, "total_amount": 120.0},
        )
        self.assertEqual(item.document_id, "doc_flagged_01")
        self.assertEqual(item.status, "PENDING_REVIEW")
        self.assertEqual(item.confidence_score, 0.62)

        # Verify JSON persisted
        self.assertTrue(self.json_path.exists())
        with open(self.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertIn("doc_flagged_01", data)

        # Verify CSV exported
        self.assertTrue(self.csv_path.exists())
        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            self.assertEqual(len(reader), 1)
            self.assertEqual(reader[0]["document_id"], "doc_flagged_01")
            self.assertEqual(reader[0]["status"], "PENDING_REVIEW")

    def test_get_pending_items(self):
        self.queue.enqueue("d1", "d1.pdf", "pdf_text", 0.70, ["Reason A"], {})
        self.queue.enqueue("d2", "d2.pdf", "pdf_scanned", 0.65, ["Reason B"], {})
        pending = self.queue.get_pending_items()
        self.assertEqual(len(pending), 2)

    def test_approve_item(self):
        self.queue.enqueue("d1", "d1.pdf", "pdf_text", 0.75, ["Check terms"], {"payment_terms": "UNKNOWN"})
        resolved = self.queue.resolve_item("d1", action="APPROVED", notes="Terms confirmed as Net 30 from email")

        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.status, "APPROVED")
        self.assertEqual(resolved.human_notes, "Terms confirmed as Net 30 from email")
        self.assertIsNotNone(resolved.reviewed_at)

        # Status in queue and pending list updated
        pending = self.queue.get_pending_items()
        self.assertEqual(len(pending), 0)

    def test_reject_item(self):
        self.queue.enqueue("d2", "d2.pdf", "pdf_text", 0.40, ["Unreadable scan"], {})
        resolved = self.queue.resolve_item("d2", action="REJECTED", notes="Illegible receipt, requested re-scan")

        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.status, "REJECTED")

    def test_override_fields_audit(self):
        self.queue.enqueue(
            document_id="d3",
            filename="d3.pdf",
            doc_type="pdf_text",
            confidence_score=0.68,
            review_reasons=["invoice_id is null"],
            extracted_data={"invoice_id": None, "total_amount": 950.0},
        )
        resolved = self.queue.resolve_item(
            document_id="d3",
            action="OVERRIDDEN",
            notes="Extracted invoice_id from footer",
            overrides={"invoice_id": "INV-FOOTER-1234"},
        )
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.status, "OVERRIDDEN")
        self.assertEqual(resolved.extracted_data["invoice_id"], "INV-FOOTER-1234")
        self.assertEqual(resolved.overridden_fields, {"invoice_id": "INV-FOOTER-1234"})

        # Reload queue from disk and verify persistence
        reloaded = HumanReviewQueue(queue_json_path=self.json_path, queue_csv_path=self.csv_path)
        item = reloaded.items["d3"]
        self.assertEqual(item.status, "OVERRIDDEN")
        self.assertEqual(item.extracted_data["invoice_id"], "INV-FOOTER-1234")

    def test_summary_metrics(self):
        self.queue.enqueue("d1", "d1.pdf", "pdf_text", 0.70, ["Reason"], {})
        self.queue.enqueue("d2", "d2.pdf", "pdf_text", 0.70, ["Reason"], {})
        self.queue.resolve_item("d1", action="APPROVED")

        summary = self.queue.get_summary()
        self.assertEqual(summary["TOTAL"], 2)
        self.assertEqual(summary["APPROVED"], 1)
        self.assertEqual(summary["PENDING_REVIEW"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
