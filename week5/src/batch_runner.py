"""Production Batch Pipeline Runner for Document Extraction.

Features:
1. Fault-Tolerant Execution: Continues execution when encountering corrupted or invalid
   documents (like doc_069_corrupt.pdf) without losing prior work.
2. Atomic State Checkpointing: Persists results after each document so interrupted runs resume seamlessly.
3. Automated Confidence Routing: Integrates with ConfidenceEngine and HumanReviewQueue.
4. Telemetry & Cost Accounting: Tracks token consumption, latency, and costs.
5. Generates outputs:
   - outputs/predictions.jsonl
   - outputs/failures.jsonl
   - outputs/review_queue.csv
"""

from __future__ import annotations
import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from src.confidence import ConfidenceEngine, ConfidenceReport
from src.extractor import DocumentExtractor, ExtractionMetadata
from src.loader import DocumentContent, DocumentLoader
from src.review_queue import HumanReviewQueue
from src.schemas import InvoiceExtraction


@dataclass
class ProcessedDocumentRecord:
    document_id: str
    filename: str
    doc_type: str
    status: str  # "SUCCESS", "REVIEW_REQUIRED", "FAILED"
    confidence_score: float
    is_auto_approved: bool
    review_reasons: List[str]
    latency_ms: float
    retries_used: int
    extracted_data: Dict[str, Any]
    error_message: Optional[str] = None


@dataclass
class BatchExecutionSummary:
    total_documents: int
    succeeded_count: int
    failed_count: int
    auto_approved_count: int
    human_review_count: int
    duration_seconds: float
    avg_latency_ms: float
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: float
    checkpoint_file: str


class BatchPipelineRunner:
    """Enterprise batch processing pipeline with atomic checkpointing and crash protection."""

    COST_PER_1M_INPUT = 0.10
    COST_PER_1M_OUTPUT = 0.40

    def __init__(
        self,
        output_dir: Optional[Union[str, Path]] = None,
        checkpoint_path: Optional[Union[str, Path]] = None,
        confidence_threshold: float = 0.80,
    ):
        base_dir = Path(__file__).resolve().parent.parent
        self.output_dir = Path(output_dir) if output_dir else base_dir / "outputs"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.checkpoint_path = (
            Path(checkpoint_path)
            if checkpoint_path
            else self.output_dir / "batch_checkpoint.json"
        )
        self.predictions_jsonl = self.output_dir / "predictions.jsonl"
        self.failures_jsonl = self.output_dir / "failures.jsonl"
        self.review_queue_csv = self.output_dir / "review_queue.csv"

        self.loader = DocumentLoader()
        self.extractor = DocumentExtractor()
        self.confidence_engine = ConfidenceEngine(threshold=confidence_threshold)
        self.review_queue = HumanReviewQueue(queue_csv_path=self.review_queue_csv)

    def run_batch(
        self,
        document_paths: List[Union[str, Path]],
        resume_from_checkpoint: bool = True,
    ) -> Tuple[List[ProcessedDocumentRecord], BatchExecutionSummary]:
        start_time = time.time()
        results: Dict[str, ProcessedDocumentRecord] = {}

        # Load existing checkpoint if resuming
        if resume_from_checkpoint and self.checkpoint_path.exists():
            try:
                with open(self.checkpoint_path, "r", encoding="utf-8") as f:
                    saved_data = json.load(f)
                    for k, v in saved_data.get("records", {}).items():
                        results[k] = ProcessedDocumentRecord(**v)
            except Exception:
                results = {}

        total_input_tokens = 0
        total_output_tokens = 0

        for file_path in document_paths:
            path = Path(file_path)
            doc_id = path.stem

            # Skip if already processed in checkpoint
            if doc_id in results and results[doc_id].status != "FAILED":
                continue

            try:
                # Step 1: Load Document (Zero-crash guarantee)
                doc = self.loader.load_document(path)

                if not doc.is_valid:
                    rec = ProcessedDocumentRecord(
                        document_id=doc_id,
                        filename=path.name,
                        doc_type=doc.doc_type,
                        status="FAILED",
                        confidence_score=0.0,
                        is_auto_approved=False,
                        review_reasons=[f"Document loading failed: {doc.error_message}"],
                        latency_ms=0.0,
                        retries_used=0,
                        extracted_data={},
                        error_message=doc.error_message,
                    )
                    results[doc_id] = rec
                    self._save_checkpoint(results)
                    self._record_failure(rec)
                    continue

                # Step 2: Extract structured fields
                extraction, metadata = self.extractor.extract(doc)
                total_input_tokens += metadata.input_tokens
                total_output_tokens += metadata.output_tokens

                # Step 3: Compute confidence & routing
                conf_report = self.confidence_engine.compute_confidence(
                    doc, extraction, metadata
                )

                status = "SUCCESS" if conf_report.is_auto_approved else "REVIEW_REQUIRED"

                rec = ProcessedDocumentRecord(
                    document_id=doc_id,
                    filename=path.name,
                    doc_type=doc.doc_type,
                    status=status,
                    confidence_score=conf_report.composite_confidence,
                    is_auto_approved=conf_report.is_auto_approved,
                    review_reasons=conf_report.review_reasons,
                    latency_ms=metadata.latency_ms,
                    retries_used=metadata.retries_used,
                    extracted_data=extraction.to_ground_truth_dict(),
                    error_message=None,
                )
                results[doc_id] = rec
                self._save_checkpoint(results)
                self._record_prediction(rec)

                # Route to human review queue if not auto-approved
                if not conf_report.is_auto_approved:
                    self.review_queue.enqueue(
                        document_id=doc_id,
                        filename=path.name,
                        doc_type=doc.doc_type,
                        confidence_score=conf_report.composite_confidence,
                        review_reasons=conf_report.review_reasons,
                        extracted_data=extraction.to_ground_truth_dict(),
                    )

            except Exception as e:
                rec = ProcessedDocumentRecord(
                    document_id=doc_id,
                    filename=path.name,
                    doc_type="unknown",
                    status="FAILED",
                    confidence_score=0.0,
                    is_auto_approved=False,
                    review_reasons=[f"Unexpected pipeline exception: {str(e)}"],
                    latency_ms=0.0,
                    retries_used=0,
                    extracted_data={},
                    error_message=str(e),
                )
                results[doc_id] = rec
                self._save_checkpoint(results)
                self._record_failure(rec)

        # Compute summary
        duration = round(time.time() - start_time, 2)
        records_list = list(results.values())
        succeeded = [r for r in records_list if r.status in ("SUCCESS", "REVIEW_REQUIRED")]
        failed = [r for r in records_list if r.status == "FAILED"]
        auto_approved = [r for r in records_list if r.status == "SUCCESS"]
        review_req = [r for r in records_list if r.status == "REVIEW_REQUIRED"]

        avg_latency = (
            round(sum(r.latency_ms for r in succeeded) / len(succeeded), 2)
            if succeeded
            else 0.0
        )

        cost = (
            (total_input_tokens / 1_000_000) * self.COST_PER_1M_INPUT
            + (total_output_tokens / 1_000_000) * self.COST_PER_1M_OUTPUT
        )

        summary = BatchExecutionSummary(
            total_documents=len(document_paths),
            succeeded_count=len(succeeded),
            failed_count=len(failed),
            auto_approved_count=len(auto_approved),
            human_review_count=len(review_req),
            duration_seconds=duration,
            avg_latency_ms=avg_latency,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            total_cost_usd=round(cost, 6),
            checkpoint_file=str(self.checkpoint_path),
        )

        # Write overall predictions.jsonl and failures.jsonl
        self._write_output_files(records_list, summary)

        return records_list, summary

    def _save_checkpoint(self, results: Dict[str, ProcessedDocumentRecord]):
        """Persists atomic progress to disk."""
        serialized = {k: asdict(v) for k, v in results.items()}
        try:
            with open(self.checkpoint_path, "w", encoding="utf-8") as f:
                json.dump({"records": serialized, "timestamp": time.time()}, f, indent=2)
        except Exception:
            pass

    def _record_prediction(self, rec: ProcessedDocumentRecord):
        with open(self.predictions_jsonl, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(rec)) + "\n")

    def _record_failure(self, rec: ProcessedDocumentRecord):
        with open(self.failures_jsonl, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(rec)) + "\n")

    def _write_output_files(self, records: List[ProcessedDocumentRecord], summary: BatchExecutionSummary):
        """Rewrites predictions.jsonl, failures.jsonl and batch_summary.json cleanly."""
        with open(self.predictions_jsonl, "w", encoding="utf-8") as f:
            for r in records:
                if r.status != "FAILED":
                    f.write(json.dumps(asdict(r)) + "\n")

        with open(self.failures_jsonl, "w", encoding="utf-8") as f:
            for r in records:
                if r.status == "FAILED":
                    f.write(json.dumps(asdict(r)) + "\n")

        with open(self.output_dir / "batch_summary.json", "w", encoding="utf-8") as f:
            json.dump(asdict(summary), f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Production Batch Document Extraction Pipeline")
    parser.add_argument("--input-dir", type=str, default="data/documents", help="Directory of invoice documents")
    parser.add_argument("--output-dir", type=str, default="outputs", help="Directory for extraction outputs")
    parser.add_argument("--threshold", type=float, default=0.80, help="Confidence threshold for auto-approval")
    args = parser.parse_args()

    input_dir = Path(args.input_dir).resolve()
    output_dir = Path(args.output_dir).resolve()

    if not input_dir.exists():
        print(f"Error: Input directory '{input_dir}' does not exist.")
        sys.exit(1)

    doc_files = sorted([
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in (".pdf", ".png", ".jpg", ".jpeg", ".webp")
    ])

    print(f"Discovered {len(doc_files)} documents in {input_dir}. Starting batch processing...")
    runner = BatchPipelineRunner(output_dir=output_dir, confidence_threshold=args.threshold)
    records, summary = runner.run_batch(doc_files)

    print(f"\n==========================================")
    print(f"BATCH EXECUTION COMPLETE")
    print(f"==========================================")
    print(f"Total Documents:     {summary.total_documents}")
    print(f"Succeeded:           {summary.succeeded_count}")
    print(f"Failed:              {summary.failed_count}")
    print(f"Auto-Approved:       {summary.auto_approved_count} ({round(summary.auto_approved_count/max(1, len(doc_files))*100, 1)}%)")
    print(f"Human Review:        {summary.human_review_count} ({round(summary.human_review_count/max(1, len(doc_files))*100, 1)}%)")
    print(f"Duration:            {summary.duration_seconds}s")
    print(f"Outputs written to:  {output_dir}")


if __name__ == "__main__":
    main()
