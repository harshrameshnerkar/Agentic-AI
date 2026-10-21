"""Human-in-the-Loop Review Queue Manager for Document Extraction.

Features:
- Maintains pending review items flagged by ConfidenceEngine with explicit reasons.
- Records human operator overrides, approvals, rejections, and audit notes.
- Persists queue state to outputs/review_queue.csv and data/review_queue.json.
"""

from __future__ import annotations
import csv
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


@dataclass
class ReviewQueueItem:
    document_id: str
    filename: str
    doc_type: str
    confidence_score: float
    review_reasons: List[str]
    extracted_data: Dict[str, Any]
    status: str = "PENDING_REVIEW"  # PENDING_REVIEW, APPROVED, REJECTED, OVERRIDDEN
    human_notes: Optional[str] = None
    reviewed_at: Optional[float] = None
    overridden_fields: Dict[str, Any] = field(default_factory=dict)


class HumanReviewQueue:
    """Manages the lifecycle of documents requiring human-in-the-loop inspection."""

    def __init__(
        self,
        queue_json_path: Optional[Union[str, Path]] = None,
        queue_csv_path: Optional[Union[str, Path]] = None,
    ):
        base_dir = Path(__file__).resolve().parent.parent
        self.queue_json = Path(queue_json_path) if queue_json_path else base_dir / "data" / "review_queue.json"
        self.queue_csv = Path(queue_csv_path) if queue_csv_path else base_dir / "outputs" / "review_queue.csv"
        self.items: Dict[str, ReviewQueueItem] = self._load_queue()

    def _load_queue(self) -> Dict[str, ReviewQueueItem]:
        if self.queue_json.exists():
            try:
                with open(self.queue_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return {k: ReviewQueueItem(**v) for k, v in data.items()}
            except Exception:
                pass

        # Fallback to CSV if JSON not found
        if self.queue_csv.exists():
            try:
                items: Dict[str, ReviewQueueItem] = {}
                with open(self.queue_csv, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        doc_id = row.get("document_id")
                        if not doc_id:
                            continue
                        reasons = [r.strip() for r in (row.get("review_reasons") or "").split(";") if r.strip()]
                        overrides_str = row.get("overridden_fields")
                        overrides = json.loads(overrides_str) if overrides_str else {}
                        reviewed_at_str = row.get("reviewed_at")
                        reviewed_at = float(reviewed_at_str) if reviewed_at_str else None
                        conf_str = row.get("confidence_score")
                        conf = float(conf_str) if conf_str else 0.50

                        items[doc_id] = ReviewQueueItem(
                            document_id=doc_id,
                            filename=row.get("filename") or f"{doc_id}.pdf",
                            doc_type=row.get("doc_type") or "unknown",
                            confidence_score=conf,
                            review_reasons=reasons,
                            extracted_data={},
                            status=row.get("status") or "PENDING_REVIEW",
                            human_notes=row.get("human_notes") or None,
                            reviewed_at=reviewed_at,
                            overridden_fields=overrides,
                        )
                return items
            except Exception:
                return {}
        return {}

    def _save_queue(self):
        # Save JSON
        self.queue_json.parent.mkdir(parents=True, exist_ok=True)
        with open(self.queue_json, "w", encoding="utf-8") as f:
            serialized = {k: asdict(v) for k, v in self.items.items()}
            json.dump(serialized, f, indent=2)

        # Save CSV
        self.export_csv(self.queue_csv)

    def export_csv(self, csv_path: Optional[Union[str, Path]] = None):
        """Exports review queue to outputs/review_queue.csv."""
        target_path = Path(csv_path) if csv_path else self.queue_csv
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "document_id",
                "filename",
                "doc_type",
                "confidence_score",
                "status",
                "review_reasons",
                "human_notes",
                "reviewed_at",
                "overridden_fields",
            ])
            for item in self.items.values():
                writer.writerow([
                    item.document_id,
                    item.filename,
                    item.doc_type,
                    item.confidence_score,
                    item.status,
                    "; ".join(item.review_reasons),
                    item.human_notes or "",
                    item.reviewed_at or "",
                    json.dumps(item.overridden_fields) if item.overridden_fields else "",
                ])

    def enqueue(
        self,
        document_id: str,
        filename: str,
        doc_type: str,
        confidence_score: float,
        review_reasons: List[str],
        extracted_data: Dict[str, Any],
    ) -> ReviewQueueItem:
        item = ReviewQueueItem(
            document_id=document_id,
            filename=filename,
            doc_type=doc_type,
            confidence_score=confidence_score,
            review_reasons=review_reasons,
            extracted_data=extracted_data,
        )
        self.items[document_id] = item
        self._save_queue()
        return item

    def get_pending_items(self) -> List[ReviewQueueItem]:
        return [item for item in self.items.values() if item.status == "PENDING_REVIEW"]

    def resolve_item(
        self,
        document_id: str,
        action: str,  # "APPROVED", "REJECTED", "OVERRIDDEN"
        notes: str = "",
        overrides: Optional[Dict[str, Any]] = None,
        filename: Optional[str] = None,
        doc_type: Optional[str] = None,
        confidence_score: Optional[float] = None,
        extracted_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[ReviewQueueItem]:
        if document_id not in self.items:
            self.items[document_id] = ReviewQueueItem(
                document_id=document_id,
                filename=filename or f"{document_id}.pdf",
                doc_type=doc_type or "unknown",
                confidence_score=confidence_score or 0.85,
                review_reasons=["Operator manual verification"],
                extracted_data=extracted_data or {},
            )
        item = self.items[document_id]
        item.status = action
        item.human_notes = notes
        item.reviewed_at = time.time()
        if overrides:
            item.overridden_fields = overrides
            item.extracted_data.update(overrides)
        self._save_queue()
        return item

    def get_summary(self) -> Dict[str, int]:
        counts = {"TOTAL": len(self.items), "PENDING_REVIEW": 0, "APPROVED": 0, "REJECTED": 0, "OVERRIDDEN": 0}
        for item in self.items.values():
            counts[item.status] = counts.get(item.status, 0) + 1
        return counts
