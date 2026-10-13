"""
Day 12 - Session 02: SFT Dataset Preparation & Quality Control
Builds a curated, deduplicated, format-validated instruction dataset
for supervised fine-tuning (SFT) with stratified train/validation splits.
"""

from __future__ import annotations
import os
import json
from dataset_pipeline import build_and_export_sft_dataset


def main():
    print("Day 12 Session 02: SFT Dataset Pipeline & Quality Control\n")

    meta_path = os.path.join(os.path.dirname(__file__), "sft_metadata.json")
    if not os.path.exists(meta_path):
        print("Generating and exporting golden SFT dataset...")
        build_and_export_sft_dataset()

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    qc = meta["quality_control_summary"]
    print(f"Dataset:        {meta['dataset_name']}")
    print(f"Total Examples: {meta['total_examples']} (Train: {meta['train_examples']}, Val: {meta['val_examples']})")
    print(f"Retention Rate: {qc['retention_rate_pct']}% (Filtered duplicates and low-quality samples)")
    print(f"Mean Tokens:    Prompt = {qc['mean_prompt_tokens']:.1f} | Completion = {qc['mean_completion_tokens']:.1f}")

    print("\nCategory Distribution:")
    for cat, cnt in qc["category_distribution"].items():
        print(f"  • {cat}: {cnt} examples")

    print("\nDataset ready and verified for supervised fine-tuning.")


if __name__ == "__main__":
    main()
