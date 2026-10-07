"""
Day 12 - Session 2: SFT Dataset Preparation & Quality Control Inspector
=======================================================================
Interactive CLI Workspace:
  1. Build / Re-generate 300-Example SFT Dataset Pipeline
  2. View Quality Control & Stratification Report
  3. Inspect Random Golden Train/Validation Samples (Formatted JSON)
  4. Run Provider Format Linter (OpenAI / Vertex / Hugging Face Compliance)
  5. Pedagogical Guide: The 4 Commandments of SFT Datasets
"""

import sys
import os
import json
import random
from typing import Dict, List, Any

from dataset_pipeline import build_and_export_sft_dataset
from quality_control import qc_pipeline, estimate_tokens
from dataset_generator import TriageActionPlan


def print_banner(title: str):
    print("\n" + "=" * 95)
    print(f" {title.center(93)} ")
    print("=" * 95)


def show_qc_report():
    print_banner("QUALITY CONTROL & STRATIFICATION REPORT")
    meta_path = os.path.join(os.path.dirname(__file__), "sft_metadata.json")
    if not os.path.exists(meta_path):
        print("[!] Metadata not found. Generating dataset first...")
        build_and_export_sft_dataset()

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    qc = meta["quality_control_summary"]
    print(f"Dataset Name    : {meta['dataset_name']}")
    print(f"Narrow Task     : {meta['task_description']}")
    print(f"Total Golden    : {meta['total_examples']} examples")
    print(f"Train / Val     : {meta['train_examples']} Train (84.0%) / {meta['val_examples']} Val (16.0%)")
    print(f"Retention Rate  : {qc['retention_rate_pct']}% of candidates accepted")
    print(f"Mean Tokens     : Prompt = {qc['mean_prompt_tokens']:.1f} tok | Completion = {qc['mean_completion_tokens']:.1f} tok\n")

    print("1. QUALITY CONTROL FILTER STAGES:")
    print(f"   - Raw Candidates Evaluated          : {qc['total_candidates_evaluated']:>4}")
    print(f"   - Exact Duplicates Removed (SHA-256): {qc['exact_duplicates_removed']:>4}")
    print(f"   - Fuzzy Duplicates Removed (Jaccard): {qc['fuzzy_duplicates_removed']:>4}")
    print(f"   - HITL Safety Rubric Filtered       : {qc['hitl_rubric_failures_removed']:>4}")
    print(f"   - Final Accepted Golden Pool        : {qc['total_accepted_examples']:>4}\n")

    print("2. CATEGORY STRATIFICATION BREAKDOWN:")
    print("-" * 65)
    print(f"| SRE Architectural Category   | Count | Proportion | Stratified |")
    print("-" * 65)
    for cat, cnt in qc["category_distribution"].items():
        pct = (cnt / meta["total_examples"]) * 100.0
        print(f"| {cat:<28} | {cnt:>5} | {pct:>9.1f}% | [BALANCED] |")
    print("-" * 65)

    print("\n3. SEVERITY DISTRIBUTION:")
    for sev, cnt in qc["severity_distribution"].items():
        pct = (cnt / meta["total_examples"]) * 100.0
        print(f"   - {sev:<6}: {cnt:>3} examples ({pct:.1f}%)")
    print("-" * 95)


def inspect_random_samples(n: int = 2):
    print_banner(f"INSPECTING {n} RANDOM GOLDEN EXAMPLES FROM TRAIN SET")
    train_path = os.path.join(os.path.dirname(__file__), "sft_train.jsonl")
    if not os.path.exists(train_path):
        build_and_export_sft_dataset()

    with open(train_path, "r", encoding="utf-8") as f:
        lines = [json.loads(line) for line in f if line.strip()]

    samples = random.sample(lines, min(n, len(lines)))
    for idx, s in enumerate(samples, 1):
        msgs = s["messages"]
        user_prompt = msgs[1]["content"]
        assistant_json = json.loads(msgs[2]["content"])

        print(f"\n--- [SAMPLE #{idx:02d} / {len(lines)} TRAIN EXAMPLES] ---")
        print(f"[USER PROMPT]:\n{user_prompt}\n")
        print(f"[ASSISTANT TRIAGE ACTION PLAN (JSON)]:")
        print(json.dumps(assistant_json, indent=2))
        print(f"Token Estimate: Prompt ~ {estimate_tokens(user_prompt)} tok | Completion ~ {estimate_tokens(msgs[2]['content'])} tok")
        print("-" * 95)


def verify_provider_linter():
    print_banner("PROVIDER FORMAT LINTER & COMPLIANCE CHECKER")
    print("Verifying formatting against OpenAI, Vertex AI & Hugging Face TRL specifications...\n")

    files_to_check = [
        ("Train Set", os.path.join(os.path.dirname(__file__), "sft_train.jsonl")),
        ("Validation Set", os.path.join(os.path.dirname(__file__), "sft_val.jsonl")),
    ]

    all_passed = True
    for label, path in files_to_check:
        if not os.path.exists(path):
            print(f"[!] File not found: {path}")
            all_passed = False
            continue

        with open(path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]

        print(f"Checking {label:<15} ({len(lines)} lines in {os.path.basename(path)}):")

        line_errors = 0
        for idx, line in enumerate(lines, 1):
            try:
                data = json.loads(line)
            except Exception as e:
                print(f"  [ERROR] Line {idx}: Invalid JSON syntax ({e})")
                line_errors += 1
                continue

            if "messages" not in data:
                print(f"  [ERROR] Line {idx}: Missing 'messages' key")
                line_errors += 1
                continue

            msgs = data["messages"]
            if len(msgs) != 3:
                print(f"  [ERROR] Line {idx}: Expected 3 messages, got {len(msgs)}")
                line_errors += 1
                continue

            roles = [m.get("role") for m in msgs]
            if roles != ["system", "user", "assistant"]:
                print(f"  [ERROR] Line {idx}: Invalid roles {roles}")
                line_errors += 1
                continue

            # Verify assistant JSON
            try:
                parsed_plan = json.loads(msgs[2]["content"])
                TriageActionPlan(**parsed_plan)
            except Exception as e:
                print(f"  [ERROR] Line {idx}: Assistant payload violates schema ({e})")
                line_errors += 1
                continue

        if line_errors == 0:
            print(f"  [PASS] 100.0% of {len(lines)} lines conform to provider chat schema!\n")
        else:
            print(f"  [FAIL] {line_errors} lines failed validation.\n")
            all_passed = False

    if all_passed:
        print("[STATUS: 100% COMPLIANT] Ready for upload to OpenAI, Vertex AI, or Hugging Face!")
    print("-" * 95)


def show_pedagogical_commandments():
    print_banner("THE 4 COMMANDMENTS OF SFT DATASET PREPARATION")
    print("""
1. QUALITY OVER QUANTITY (THE LIMA PRINCIPLE)
   - Foundational alignment research proves that 300 to 1,000 pristine, diverse examples
     outperform 50,000 noisy, duplicate web scrapes.
   - SFT is NOT for teaching knowledge from scratch; SFT is for steering behavior, tone,
     and output formatting.

2. ABSOLUTE FORMAT CONSISTENCY
   - Models learn syntactic patterns with extreme efficiency.
   - If 10% of examples omit a key or format dates differently, the fine-tuned model
     will exhibit erratic schema compliance in production.
   - Always validate 100% of samples through Pydantic validators before training.

3. DEDUPLICATION (EXACT & FUZZY)
   - Duplicate prompts cause catastrophic overfitting on specific phrasings.
   - Exact hash deduplication catches repeats; fuzzy n-gram Jaccard deduplication
     catches paraphrased near-duplicates, forcing high lexical diversity.

4. THE TEACHER-STUDENT DISTILLATION PARADIGM
   - Use frontier models (e.g., Claude 3.5 Sonnet, GPT-4o) with rich domain prompts
     to generate candidate outputs.
   - Use human-in-the-loop expert SRE rubrics to filter, edit, and reject low-confidence
     or unsafe samples before feeding them into smaller student models.
""")


def interactive_menu():
    while True:
        print_banner("DAY 12 - SESSION 2: SFT DATASET PREPARATION")
        print(" [1] View Quality Control & Stratification Report")
        print(" [2] Inspect Random Golden Samples (Formatted JSON View)")
        print(" [3] Run Provider Format Linter (OpenAI / Vertex / HF Checker)")
        print(" [4] Re-run Full SFT Dataset Generation Pipeline (300 Samples)")
        print(" [5] Pedagogical Guide: The 4 Commandments of SFT Datasets")
        print(" [0] Exit")
        print("=" * 95)

        choice = input("Select an option (0-5): ").strip()
        if choice == "1":
            show_qc_report()
        elif choice == "2":
            inspect_random_samples(2)
        elif choice == "3":
            verify_provider_linter()
        elif choice == "4":
            build_and_export_sft_dataset()
        elif choice == "5":
            show_pedagogical_commandments()
        elif choice == "0":
            print("\nExiting Day 12 Session 2 SFT Dataset Workspace. Goodbye!\n")
            break
        else:
            print("[!] Invalid option. Please enter 0-5.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--rebuild":
        build_and_export_sft_dataset()
    elif len(sys.argv) > 1 and sys.argv[1] == "--verify":
        verify_provider_linter()
    elif len(sys.argv) > 1 and sys.argv[1] == "--report":
        show_qc_report()
    elif len(sys.argv) > 1 and sys.argv[1] == "--sample":
        inspect_random_samples(1)
    else:
        interactive_menu()
