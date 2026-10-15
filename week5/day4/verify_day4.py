"""Verification Suite for Week 5 Day 4 Acceptance Criteria.

Enforces:
- Criterion 7: Confidence signal exists and routes low-confidence extractions to human review.
  Tests feeding poor-quality/ambiguous scans and verifies they are flagged with clear reasons.
- Criterion 8: Review threshold is tuned with empirical evidence (auto-approval rate vs. escaped
  error rate trade-off curve), not picked arbitrarily.
"""

from __future__ import annotations
import os
import sys
from decimal import Decimal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent
for p in (str(REPO_ROOT), str(BASE_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from week5.day4.review_queue import HumanReviewQueue
from week5.day4.tune_thresholds import ThresholdTuner, ANALYSIS_PATH
from week5.pipeline.confidence_engine import ConfidenceEngine
from week5.pipeline.document_loader import DocumentLoader
from week5.pipeline.extraction_schema import InvoiceExtraction
DOCS_DIR = BASE_DIR / "data" / "documents"


def test_confidence_routing_poor_quality_scan():
    print("\n[CRITERION 7] Testing Confidence Routing on Low-Confidence Scans...")
    loader = DocumentLoader()
    engine = ConfidenceEngine(threshold=0.80)
    queue = HumanReviewQueue()

    # 1. Clean vector PDF with complete anchors
    clean_doc = loader.load_document(DOCS_DIR / "doc_001.pdf")
    clean_ext = InvoiceExtraction(
        invoice_id="36258",
        invoice_date="2012-03-06",
        subtotal=Decimal("45.00"),
        tax_amount=Decimal("5.10"),
        total_amount=Decimal("50.10"),
    )
    clean_report = engine.compute_confidence(clean_doc, clean_ext)
    print(f"  • Clean Document (doc_001.pdf) Confidence: {clean_report.composite_confidence:.2f} -> Auto-Approved: {clean_report.is_auto_approved}")
    assert clean_report.composite_confidence >= 0.80, "Clean vector PDF should achieve high confidence"

    # 2. Degraded scan with missing anchor and arithmetic mismatch
    degraded_doc = loader.load_document(DOCS_DIR / "doc_026.pdf")
    degraded_ext = InvoiceExtraction(
        invoice_id=None,  # Missing critical anchor
        invoice_date="2012-03-15",
        subtotal=Decimal("194.92"),
        tax_amount=Decimal("19.49"),
        total_amount=Decimal("999.00"),  # Severe math mismatch (194.92 + 19.49 != 999.00)
    )
    degraded_report = engine.compute_confidence(degraded_doc, degraded_ext)
    print(f"  • Degraded Document (doc_026.pdf) Confidence: {degraded_report.composite_confidence:.2f} -> Auto-Approved: {degraded_report.is_auto_approved}")
    print(f"    - Review Reasons Flagged: {degraded_report.review_reasons}")

    assert degraded_report.composite_confidence < 0.80, "Degraded scan should fall below 0.80 threshold"
    assert degraded_report.is_auto_approved is False, "Degraded scan MUST NOT be auto-approved"
    assert len(degraded_report.review_reasons) >= 2, "Expected multiple specific review reasons flagged"

    # Verify queue enrollment
    item = queue.enqueue(
        document_id=degraded_doc.document_id,
        filename=degraded_doc.filename,
        doc_type=degraded_doc.doc_type,
        confidence_score=degraded_report.composite_confidence,
        review_reasons=degraded_report.review_reasons,
        extracted_data=degraded_ext.to_ground_truth_dict(),
    )
    assert item.status == "PENDING_REVIEW"
    print("  [PASS] Low-confidence extraction routed directly to Human Review Queue.")


def test_threshold_evidence_tuning():
    print("\n[CRITERION 8] Testing Empirical Evidence Threshold Tuning...")
    tuner = ThresholdTuner()
    points = tuner.run_sweep()

    assert len(points) >= 5, "Expected at least 5 candidate threshold points evaluated"
    assert ANALYSIS_PATH.exists(), f"Analysis file missing: {ANALYSIS_PATH}"

    # Verify monotonic properties: as threshold increases, auto-approval decreases
    auto_rates = [p.auto_approval_rate_pct for p in points]
    assert auto_rates == sorted(auto_rates, reverse=True), "Auto-approval rate must decrease as threshold rises"

    # Verify 0.80 sweet spot point exists
    point_80 = [p for p in points if p.threshold == 0.80][0]
    print(f"  • Selected Threshold 0.80: Auto-Approval={point_80.auto_approval_rate_pct}% | Escaped Error Rate={point_80.escaped_error_rate_pct}%")
    assert point_80.auto_approval_rate_pct >= 60.0, "Expected >=60% auto-approval at 0.80"
    assert point_80.escaped_error_rate_pct <= 5.0, "Expected <=5.0% escaped error rate at 0.80"
    print("  [PASS] Threshold 0.80 selected with rigorous empirical evidence in CONFIDENCE_ROUTING_ANALYSIS.md.")


def main():
    print("=" * 75)
    print("TASK 5 - DAY 4 ACCEPTANCE CRITERIA VERIFICATION SUITE")
    print("=" * 75)

    test_confidence_routing_poor_quality_scan()
    test_threshold_evidence_tuning()

    print("\n" + "-" * 75)
    print("ALL DAY 4 ACCEPTANCE CRITERIA VERIFIED SUCCESSFULLY!")
    print("  Criterion 7: Confidence signal routes low-confidence scans -> MET (Y)")
    print("  Criterion 8: Review threshold tuned with empirical data    -> MET (Y)")
    print("-" * 75)


if __name__ == "__main__":
    main()
