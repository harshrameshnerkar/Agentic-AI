"""Independent unit and empirical tests for ConfidenceEngine (Day 4 requirements)."""

from __future__ import annotations
import sys
import unittest
from decimal import Decimal
from pathlib import Path

# Ensure week5 directory is on path
WEEK5_DIR = Path(__file__).resolve().parent.parent
if str(WEEK5_DIR) not in sys.path:
    sys.path.insert(0, str(WEEK5_DIR))

from src.confidence import ConfidenceEngine, ConfidenceReport, ThresholdTuningRow
from src.extractor import ExtractionMetadata
from src.loader import DocumentContent
from src.schemas import CurrencyEnum, InvoiceExtraction, PaymentTermsEnum


class TestConfidenceEngine(unittest.TestCase):
    """Verifies multi-factor scoring, anchor gating, arithmetic penalties, and threshold tuning."""

    def setUp(self):
        self.engine = ConfidenceEngine(threshold=0.80)

    def test_ideal_document_high_confidence(self):
        doc = DocumentContent(
            document_id="doc_perfect",
            filename="doc_perfect.pdf",
            file_path=Path("doc_perfect.pdf"),
            doc_type="pdf_text",
            text="Clean invoice font stream text",
            is_valid=True,
        )
        ext = InvoiceExtraction(
            invoice_id="INV-2024-001",
            invoice_date="2024-03-01",
            subtotal="500.00",
            tax_amount="50.00",
            total_amount="550.00",
            currency="USD",
            payment_terms="NET_30",
        )
        meta = ExtractionMetadata(
            document_id="doc_perfect",
            model="gemini-3.1-flash-lite",
            latency_ms=15.0,
            retries_used=0,
            validation_passed=True,
            input_tokens=400,
            output_tokens=120,
            from_cache=True,
            raw_response="{}",
        )

        report: ConfidenceReport = self.engine.compute_confidence(doc, ext, meta)

        self.assertAlmostEqual(report.anchor_score, 0.35, places=2)
        self.assertAlmostEqual(report.math_coherence_score, 0.30, places=2)
        self.assertAlmostEqual(report.fidelity_score, 0.20, places=2)
        self.assertAlmostEqual(report.stability_score, 0.15, places=2)
        self.assertEqual(report.composite_confidence, 1.0)
        self.assertTrue(report.is_auto_approved)
        self.assertEqual(len(report.review_reasons), 0)

    def test_missing_critical_anchors_blocks_auto_approval(self):
        doc = DocumentContent(
            document_id="doc_no_id",
            filename="doc_no_id.pdf",
            file_path=Path("doc_no_id.pdf"),
            doc_type="pdf_text",
            text="Some invoice text",
            is_valid=True,
        )
        # Missing invoice_id
        ext = InvoiceExtraction(
            invoice_id=None,
            invoice_date="2024-03-01",
            total_amount="100.00",
        )
        report = self.engine.compute_confidence(doc, ext)
        self.assertFalse(report.is_auto_approved)
        self.assertTrue(any("invoice_id is null" in r for r in report.review_reasons))

    def test_severe_math_mismatch_penalty(self):
        doc = DocumentContent(
            document_id="doc_math_fail",
            filename="doc_math_fail.pdf",
            file_path=Path("doc_math_fail.pdf"),
            doc_type="pdf_text",
            text="Invoice text",
            is_valid=True,
        )
        # 100 + 10 != 500
        ext = InvoiceExtraction(
            invoice_id="INV-99",
            invoice_date="2024-01-01",
            subtotal="100.00",
            tax_amount="10.00",
            total_amount="500.00",
        )
        report = self.engine.compute_confidence(doc, ext)
        self.assertFalse(report.is_auto_approved)
        self.assertEqual(report.math_coherence_score, 0.05)
        self.assertTrue(any("Severe arithmetic mismatch" in r for r in report.review_reasons))

    def test_fidelity_weight_scanned_vs_image(self):
        ext = InvoiceExtraction(invoice_id="INV-1", invoice_date="2024-01-01", total_amount="10.0")
        doc_scanned = DocumentContent("d1", "d1.pdf", Path("d1.pdf"), "pdf_scanned", "", is_valid=True)
        doc_img = DocumentContent("d2", "d2.png", Path("d2.png"), "image_png", "", is_valid=True)

        rep_scanned = self.engine.compute_confidence(doc_scanned, ext)
        rep_img = self.engine.compute_confidence(doc_img, ext)

        self.assertEqual(rep_scanned.fidelity_score, 0.15)
        self.assertEqual(rep_img.fidelity_score, 0.12)

    def test_retry_stability_penalty(self):
        doc = DocumentContent("d1", "d1.pdf", Path("d1.pdf"), "pdf_text", "txt", is_valid=True)
        ext = InvoiceExtraction(invoice_id="INV-1", invoice_date="2024-01-01", total_amount="10.0")

        meta0 = ExtractionMetadata("d1", "m", 1.0, 0, True, 10, 10, False, "")
        meta1 = ExtractionMetadata("d1", "m", 1.0, 1, True, 10, 10, False, "")
        meta2 = ExtractionMetadata("d1", "m", 1.0, 2, True, 10, 10, False, "")

        self.assertEqual(self.engine.compute_confidence(doc, ext, meta0).stability_score, 0.15)
        self.assertEqual(self.engine.compute_confidence(doc, ext, meta1).stability_score, 0.08)
        self.assertEqual(self.engine.compute_confidence(doc, ext, meta2).stability_score, 0.02)

    def test_corrupt_document_zero_confidence(self):
        doc = DocumentContent("d_corrupt", "c.pdf", Path("c.pdf"), "corrupt", "", is_valid=False, error_message="Corrupted header")
        ext = InvoiceExtraction()
        report = self.engine.compute_confidence(doc, ext)
        self.assertEqual(report.composite_confidence, 0.0)
        self.assertFalse(report.is_auto_approved)
        self.assertTrue(any("loading failed" in r for r in report.review_reasons))

    def test_threshold_tuning_sweep(self):
        # Create a small sample corpus: 8 valid, 2 invalid
        docs = []
        extractions = []
        for i in range(8):
            docs.append(DocumentContent(f"d_{i}", f"d_{i}.pdf", Path(f"d_{i}.pdf"), "pdf_text", "txt", is_valid=True))
            extractions.append(InvoiceExtraction(invoice_id=f"INV-{i}", invoice_date="2024-01-01", subtotal="10.0", tax_amount="1.0", total_amount="11.0"))
        # 2 bad docs
        for i in range(8, 10):
            docs.append(DocumentContent(f"d_{i}", f"d_{i}.pdf", Path(f"d_{i}.pdf"), "pdf_text", "txt", is_valid=True))
            extractions.append(InvoiceExtraction(invoice_id=None, total_amount="500.0"))

        rows = self.engine.tune_threshold_tradeoffs(docs, extractions)
        self.assertEqual(len(rows), 8)

        # Threshold 0.80 should be marked optimal
        row_80 = next(r for r in rows if r.threshold == 0.80)
        self.assertEqual(row_80.status, "OPTIMAL")
        self.assertEqual(row_80.escaped_errors, 0)
        self.assertEqual(row_80.auto_approved_count, 8)
        self.assertEqual(row_80.auto_approval_rate_pct, 80.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
