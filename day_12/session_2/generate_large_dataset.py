"""
Day 12 - Session 2 Extension: Large-Scale SFT Dataset Generator (1,200 Examples)
==============================================================================
Generates a scaled 1,200-example dataset for robust production-scale LoRA fine-tuning:
  - 1,000 Training Examples (sft_train_large.jsonl)
  - 200 Validation Examples (sft_val_large.jsonl)
Across all 5 enterprise SRE categories and 40 incident archetypes.
"""

import os
import json
import random
from typing import List
from dataset_generator import generate_sft_dataset_candidates, SFTExample


def generate_and_export_large_sft_dataset(
    output_dir: str,
    train_count: int = 1000,
    val_count: int = 200,
    seed: int = 42,
) -> None:
    total_count = train_count + val_count
    random.seed(seed)
    print(f"[LARGE DATASET PIPELINE] Generating {total_count} diverse SRE candidates...")

    candidates: List[SFTExample] = generate_sft_dataset_candidates(count=total_count)
    random.shuffle(candidates)

    train_examples = candidates[:train_count]
    val_examples = candidates[train_count:train_count + val_count]

    train_path = os.path.join(output_dir, "sft_train_large.jsonl")
    val_path = os.path.join(output_dir, "sft_val_large.jsonl")

    with open(train_path, "w", encoding="utf-8") as f:
        for ex in train_examples:
            f.write(json.dumps({"messages": ex.messages}, ensure_ascii=False) + "\n")

    with open(val_path, "w", encoding="utf-8") as f:
        for ex in val_examples:
            f.write(json.dumps({"messages": ex.messages}, ensure_ascii=False) + "\n")

    print(f"[OK] Generated {len(train_examples)} training samples -> {train_path}")
    print(f"[OK] Generated {len(val_examples)} validation samples -> {val_path}")


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    generate_and_export_large_sft_dataset(current_dir, train_count=1000, val_count=200)
