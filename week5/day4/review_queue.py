"""Human-in-the-Loop Review Queue Manager for Week 5 Document Extraction.

Manages documents flagged by ConfidenceEngine:
- Maintains pending review items with explicit failure reasons.
- Records human operator overrides and audit timestamps.
- Persists queue state to disk (review_queue.json).
"""

from __future__ import annotations
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
QUEUE_PATH = BASE_DIR / "data" / "review_queue.json"


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

    def __init__(self, queue_file: Optional[Path] = None):
        self.queue_file = queue_file or QUEUE_PATH
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        self.items: Dict[str, ReviewQueueItem] = self._load_queue()

    def _load_queue(self) -> Dict[str, ReviewQueueItem]:
        if self.queue_file.exists():
            try:
                with open(self.queue_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return {k: ReviewQueueItem(**v) for k, v in data.items()}
            except Exception:
                return {}
        return {}

    def _save_queue(self):
        with open(self.queue_file, "w", encoding="utf-8") as f:
            serialized = {k: asdict(v) for k, v in self.items.items()}
            json.dump(serialized, f, indent=2)

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
    ) -> Optional[ReviewQueueItem]:
        if document_id not in self.items:
            return None
        item = self.items[document_id]
        item.status = action
        item.human_notes = notes
        item.reviewed_at = time.time()
        if overrides:
            item.overridden_fields = overrides
            item.extracted_data.update(overrides)
        self._save_queue()
        return item
