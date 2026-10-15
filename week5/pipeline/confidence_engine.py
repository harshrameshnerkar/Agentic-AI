"""Confidence Engine & Human Review Router for Week 5 Document Extraction.

Computes a calibrated 0.0 to 1.0 confidence score per extraction based on:
1. Critical Anchor Presence (invoice_id, invoice_date, total_amount).
2. Financial Arithmetic Coherence (subtotal + tax_amount == total_amount).
3. Document Source Fidelity (vector text vs scanned vs image).
4. Validation Stability (retries used in Pydantic loop).

Routes documents below an evidence-based threshold to the Human Review Queue.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from week5.pipeline.document_loader import DocumentContent
from week5.pipeline.extraction_schema import InvoiceExtraction
from week5.pipeline.extractor import ExtractionMetadata


@dataclass
class ConfidenceReport:
    document_id: str
    composite_confidence: float
    is_auto_approved: bool
    review_reasons: List[str] = field(default_factory=list)
    anchor_score: float = 0.0
    math_coherence_score: float = 0.0
    fidelity_score: float = 0.0
    stability_score: float = 0.0


class ConfidenceEngine:
    """Calculates multi-factor confidence scores and routes low-confidence extractions."""

    DEFAULT_THRESHOLD = 0.80

    def __init__(self, threshold: float = DEFAULT_THRESHOLD):
        self.threshold = threshold

    def compute_confidence(
        self,
        doc: DocumentContent,
        extraction: InvoiceExtraction,
        metadata: Optional[ExtractionMetadata] = None,
        custom_threshold: Optional[float] = None,
    ) -> ConfidenceReport:
        threshold = custom_threshold if custom_threshold is not None else self.threshold
        reasons: List[str] = []

        if not doc.is_valid:
            return ConfidenceReport(
                document_id=doc.document_id,
                composite_confidence=0.0,
                is_auto_approved=False,
                review_reasons=[f"Document loading failed: {doc.error_message}"],
            )

        # 1. Critical Anchor Presence (Max: 0.35)
        anchor_score = 0.0
        if extraction.invoice_id:
            anchor_score += 0.15
        else:
            reasons.append("Missing critical anchor: invoice_id is null")

        if extraction.total_amount is not None:
            anchor_score += 0.15
        else:
            reasons.append("Missing critical anchor: total_amount is null")

        if extraction.invoice_date:
            anchor_score += 0.05
        else:
            reasons.append("Missing anchor: invoice_date is null")

        # 2. Financial Arithmetic Coherence (Max: 0.30)
        math_score = 0.0
        sub = extraction.subtotal
        tax = extraction.tax_amount or Decimal("0.00")
        tot = extraction.total_amount
        has_severe_math_error = False

        if sub is not None and tot is not None:
            expected_total = sub + tax
            diff = abs(expected_total - tot)
            if diff <= Decimal("0.05"):
                math_score = 0.30
            elif diff <= Decimal("5.00") or (tot > 0 and (diff / tot) <= Decimal("0.10")):
                # Minor variance (e.g. shipping/freight or discount)
                math_score = 0.25
            else:
                math_score = 0.05
                has_severe_math_error = True
                reasons.append(f"Severe arithmetic mismatch: {sub} + {tax} != {tot}")
        elif tot is not None:
            math_score = 0.20
        else:
            reasons.append("Unable to verify arithmetic coherence (missing amounts)")

        # 3. Source Fidelity (Max: 0.20)
        fidelity_score = 0.0
        if doc.doc_type == "pdf_text":
            fidelity_score = 0.20
        elif doc.doc_type == "pdf_scanned":
            fidelity_score = 0.15
        elif doc.doc_type in ("image_png", "image_jpg"):
            fidelity_score = 0.12
        else:
            fidelity_score = 0.05

        # 4. Extraction Stability (Max: 0.15)
        stability_score = 0.0
        retries = metadata.retries_used if metadata else 0
        if retries == 0:
            stability_score = 0.15
        elif retries == 1:
            stability_score = 0.08
            reasons.append("Required 1 schema validation retry")
        else:
            stability_score = 0.02
            reasons.append(f"Required {retries} schema validation retries")

        composite = round(anchor_score + math_score + fidelity_score + stability_score, 3)
        composite = min(1.0, max(0.0, composite))

        # Auto-approval: must reach threshold AND have critical anchors without severe math mismatch
        has_critical_anchors = bool(extraction.invoice_id and extraction.total_amount is not None)
        is_auto_approved = (composite >= threshold) and has_critical_anchors and not has_severe_math_error

        return ConfidenceReport(
            document_id=doc.document_id,
            composite_confidence=composite,
            is_auto_approved=is_auto_approved,
            review_reasons=reasons,
            anchor_score=round(anchor_score, 3),
            math_coherence_score=round(math_score, 3),
            fidelity_score=round(fidelity_score, 3),
            stability_score=round(stability_score, 3),
        )
