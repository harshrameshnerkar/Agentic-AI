"""Day 5: Production Batch Pipeline CLI.

Batch-processes all documents in a directory:
- Writes structured CSV and JSON outputs.
- Logs per-document latency, token usage, and confidence status.
- Survives corrupt files (e.g., doc_069_corrupt.pdf) without losing prior work.
"""

from __future__ import annotations
import argparse
import csv
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent
for p in (str(REPO_ROOT), str(BASE_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from week5.pipeline.batch_runner import BatchPipelineRunner
DEFAULT_INPUT_DIR = BASE_DIR / "data" / "documents"
DEFAULT_OUTPUT_DIR = BASE_DIR / "data" / "batch_output"


def run_batch_pipeline(
    input_dir: Path,
    output_dir: Path,
    confidence_threshold: float = 0.80,
    resume: bool = True,
):
    print("=" * 75)
    print("TASK 5 - DAY 5: PRODUCTION BATCH INVOICE PIPELINE")
    print("=" * 75)

    input_dir = Path(input_dir).resolve()
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Collect all invoice files
    doc_files = sorted([
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in (".pdf", ".png", ".jpg", ".jpeg")
    ])

    print(f"\n[DISCOVERY] Discovered {len(doc_files)} documents in '{input_dir.name}/'")
    print(f"[CONFIG] Confidence Threshold: {confidence_threshold} | Resume Checkpoint: {resume}")

    checkpoint_file = output_dir / "batch_checkpoint.json"
    runner = BatchPipelineRunner(
        checkpoint_path=checkpoint_file,
        confidence_threshold=confidence_threshold,
    )

    records, summary = runner.run_batch(doc_files, resume_from_checkpoint=resume)

    # Write batch_extractions.json
    json_path = output_dir / "batch_extractions.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump([r.__dict__ for r in records], f, indent=2)

    # Write batch_extractions.csv
    csv_path = output_dir / "batch_extractions.csv"
    csv_headers = [
        "document_id",
        "filename",
        "doc_type",
        "status",
        "confidence_score",
        "latency_ms",
        "invoice_id",
        "invoice_date",
        "due_date",
        "vendor_name",
        "vendor_tax_id",
        "customer_name",
        "currency",
        "subtotal",
        "tax_amount",
        "total_amount",
        "payment_terms",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_headers)
        writer.writeheader()
        for r in records:
            row = {
                "document_id": r.document_id,
                "filename": r.filename,
                "doc_type": r.doc_type,
                "status": r.status,
                "confidence_score": r.confidence_score,
                "latency_ms": r.latency_ms,
            }
            row.update(r.extracted_data)
            writer.writerow(row)

    # Write batch_summary.json
    summary_path = output_dir / "batch_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary.__dict__, f, indent=2)

    print("\n" + "=" * 75)
    print("BATCH PROCESSING COMPLETED SUCCESSFULLY")
    print(f"  • Total Documents:   {summary.total_documents}")
    print(f"  • Succeeded:         {summary.succeeded_count} (Auto-Approved: {summary.auto_approved_count}, Review: {summary.human_review_count})")
    print(f"  • Failed/Corrupt:    {summary.failed_count} (Trapped gracefully without crashing)")
    print(f"  • Total Duration:    {summary.duration_seconds}s (Average Latency: {summary.avg_latency_ms}ms)")
    print(f"  • Total Tokens:      {summary.total_input_tokens + summary.total_output_tokens:,} tokens")
    print(f"  • Batch Run Cost:    ${summary.total_cost_usd:.4f} USD")
    print(f"\nArtifacts Written:")
    print(f"  - Structured JSON:   {json_path}")
    print(f"  - Tabular CSV:       {csv_path}")
    print(f"  - Run Summary:       {summary_path}")
    print("=" * 75)

    return summary


def main():
    parser = argparse.ArgumentParser(description="Run production invoice extraction batch pipeline.")
    parser.add_argument("--input-dir", type=str, default=str(DEFAULT_INPUT_DIR))
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--threshold", type=float, default=0.80)
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()

    run_batch_pipeline(
        input_dir=Path(args.input_dir),
        output_dir=Path(args.output_dir),
        confidence_threshold=args.threshold,
        resume=not args.no_resume,
    )


if __name__ == "__main__":
    main()
