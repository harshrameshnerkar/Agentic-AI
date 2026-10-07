"""
Day 12 - Session 2: SFT Dataset Pipeline & Stratified Splitter
=============================================================
Orchestrates:
  1. Generation of diverse raw candidates
  2. Multi-stage QC filtering & deduplication down to exactly 300 golden samples
  3. Stratified Train / Validation split (250 train / 50 val) without data leakage
  4. Export to industry-standard JSONL format (OpenAI, Vertex AI, HuggingFace TRL)
  5. Dataset metadata and provenance recording
"""

import os
import json
import random
from typing import Dict, List, Any, Tuple, Optional
from dataset_generator import generate_sft_dataset_candidates, SFTExample
from quality_control import qc_pipeline, QCReport


def stratified_train_val_split(
    examples: List[SFTExample],
    val_ratio: float = 0.1667,  # 50 out of 300 = 16.67%
    seed: int = 42
) -> Tuple[List[SFTExample], List[SFTExample]]:
    """
    Performs category-stratified train/validation splitting.
    Ensures identical proportion of all 5 SRE categories across sets with no data leakage.
    """
    random.seed(seed)

    # Group by category
    by_category: Dict[str, List[SFTExample]] = {}
    for ex in examples:
        by_category.setdefault(ex.category, []).append(ex)

    train_set: List[SFTExample] = []
    val_set: List[SFTExample] = []

    for cat, cat_examples in by_category.items():
        # Shuffle deterministically
        shuffled = list(cat_examples)
        random.shuffle(shuffled)

        n_val = max(1, int(len(shuffled) * val_ratio))
        val_slice = shuffled[:n_val]
        train_slice = shuffled[n_val:]

        val_set.extend(val_slice)
        train_set.extend(train_slice)

    # Final shuffle within splits
    random.shuffle(train_set)
    random.shuffle(val_set)

    return train_set, val_set


def build_and_export_sft_dataset(
    output_dir: Optional[str] = None,
    target_count: int = 300
) -> Dict[str, Any]:
    """Builds, validates, splits, and exports the 300-example SFT dataset."""
    if output_dir is None:
        output_dir = os.path.dirname(__file__)

    print(f"\n[SFT PIPELINE] 1. Generating raw SFT candidates with diversity seeds...")
    raw_candidates = generate_sft_dataset_candidates(count=450)
    print(f"               Generated {len(raw_candidates)} synthetic candidates across 5 categories.")

    print(f"[SFT PIPELINE] 2. Executing multi-stage Quality Control & Deduplication pipeline...")
    accepted_examples, qc_report = qc_pipeline.process_and_filter(raw_candidates, target_count=target_count)
    print(f"               Filtered down to exactly {len(accepted_examples)} golden examples.")
    print(f"               - Exact duplicates pruned : {qc_report.exact_duplicates_removed}")
    print(f"               - Fuzzy duplicates pruned : {qc_report.fuzzy_duplicates_removed}")
    print(f"               - Schema/HITL fails pruned: {qc_report.schema_failures_removed + qc_report.hitl_rubric_failures_removed}")

    print(f"[SFT PIPELINE] 3. Performing stratified Train/Validation split...")
    train_set, val_set = stratified_train_val_split(accepted_examples, val_ratio=0.1667)
    print(f"               - Train set size : {len(train_set)} examples (83.3%)")
    print(f"               - Val set size   : {len(val_set)} examples (16.7%)")

    # Export paths
    train_path = os.path.join(output_dir, "sft_train.jsonl")
    val_path = os.path.join(output_dir, "sft_val.jsonl")
    full_path = os.path.join(output_dir, "sft_full_300.jsonl")
    meta_path = os.path.join(output_dir, "sft_metadata.json")
    qc_summary_path = os.path.join(output_dir, "QC_REPORT_SUMMARY.md")

    print(f"[SFT PIPELINE] 4. Exporting provider-standard Chat JSONL files...")

    # Write train JSONL
    with open(train_path, "w", encoding="utf-8") as f:
        for ex in train_set:
            f.write(json.dumps({"messages": ex.messages}, ensure_ascii=False) + "\n")

    # Write val JSONL
    with open(val_path, "w", encoding="utf-8") as f:
        for ex in val_set:
            f.write(json.dumps({"messages": ex.messages}, ensure_ascii=False) + "\n")

    # Write full JSONL
    with open(full_path, "w", encoding="utf-8") as f:
        for ex in accepted_examples:
            f.write(json.dumps({"id": ex.example_id, "category": ex.category, "messages": ex.messages}, ensure_ascii=False) + "\n")

    # Write metadata
    metadata_content = {
        "dataset_name": "SRE-Structured-Triage-v1",
        "task_description": "Automated SRE Alert-to-Remediation Triage & Structured Action Plan Formulation",
        "total_examples": len(accepted_examples),
        "train_examples": len(train_set),
        "val_examples": len(val_set),
        "target_format": "chat_messages_jsonl",
        "provider_compatibility": ["OpenAI", "Google Vertex AI", "Anthropic", "HuggingFace TRL", "AWS Bedrock"],
        "quality_control_summary": qc_report.model_dump(),
        "files": {
            "train": os.path.basename(train_path),
            "val": os.path.basename(val_path),
            "full": os.path.basename(full_path),
        }
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata_content, f, indent=2)

    # Write QC Report Summary Markdown
    with open(qc_summary_path, "w", encoding="utf-8") as f:
        f.write("# SRE-Structured-Triage-v1: Quality Control & Validation Summary\n\n")
        f.write(f"- **Total Candidate Examples Evaluated**: {qc_report.total_candidates_evaluated}\n")
        f.write(f"- **Final Accepted Golden Examples**: **{qc_report.total_accepted_examples}**\n")
        f.write(f"- **Train Set**: {len(train_set)} examples (83.3%)\n")
        f.write(f"- **Validation Set**: {len(val_set)} examples (16.7%)\n")
        f.write(f"- **Exact Duplicates Removed**: {qc_report.exact_duplicates_removed}\n")
        f.write(f"- **Fuzzy Semantic Duplicates Removed (Jaccard > 0.75)**: {qc_report.fuzzy_duplicates_removed}\n")
        f.write(f"- **Mean Prompt Tokens**: {qc_report.mean_prompt_tokens:.1f} tokens\n")
        f.write(f"- **Mean Completion Tokens**: {qc_report.mean_completion_tokens:.1f} tokens\n\n")
        f.write("### Category Stratification\n\n")
        f.write("| Category | Total Count | Train Count | Val Count |\n| :--- | :---: | :---: | :---: |\n")
        for cat, count in qc_report.category_distribution.items():
            tr_cnt = sum(1 for e in train_set if e.category == cat)
            vl_cnt = sum(1 for e in val_set if e.category == cat)
            f.write(f"| {cat} | {count} | {tr_cnt} | {vl_cnt} |\n")

    print(f"[OK] Master SFT dataset ready:")
    print(f"     Train JSONL : {train_path}")
    print(f"     Val JSONL   : {val_path}")
    print(f"     Metadata    : {meta_path}")

    return {
        "train_count": len(train_set),
        "val_count": len(val_set),
        "total_count": len(accepted_examples),
        "qc_report": qc_report,
        "train_file": train_path,
        "val_file": val_path,
    }


if __name__ == "__main__":
    build_and_export_sft_dataset()
