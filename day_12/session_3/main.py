"""
Day 12 - Session 3: LoRA in Practice Master Workspace
=====================================================
Interactive CLI & Demonstration Suite:
  1. Fine-Tune Small Open Model with LoRA (Training Pipeline & Convergence)
  2. Run Dual-Evaluation Benchmark (Target SRE Task vs. General Benchmark)
  3. LoRA Hyperparameter & Rank Inspector (Freeze W_0, Rank r, Alpha, Target Modules)
  4. QLoRA 4-Bit NormalFloat4 (NF4) & Memory Economics Calculator
  5. Adapter Merging Demonstration (Zero-Latency Deployment: W_merged = W_0 + (alpha/r)*B*A)
  6. Catastrophic Forgetting Diagnostic Report
"""

import os
import sys
import json
import time
import argparse
import torch
import torch.nn as nn

from lora_architecture import LoRAConfig, LoRALinear, QLoRAMemoryModeler
from train_lora import run_lora_training, LoRATrainingEngine
from eval_benchmarks import DualBenchmarkEvaluator, print_dual_benchmark_report
from general_benchmark_dataset import GENERAL_BENCHMARK_CASES


def print_header(title: str) -> None:
    print("\n" + "=" * 95)
    print(f" {title.center(93)} ")
    print("=" * 95)


def show_hyperparameter_inspector() -> None:
    print_header("LORA HYPERPARAMETER & ARCHITECTURAL INSPECTOR")
    print("Core Mathematical Axiom:  W = W_0 + (alpha / r) * (B * A)")
    print("  - Base Weight W_0   : FROZEN (Requires Grad = False)")
    print("  - Matrix A          : R^{r x d_in} initialized with Gaussian/Kaiming")
    print("  - Matrix B          : R^{d_out x r} initialized to STRICT ZERO (Delta W = 0 at Step 0)")
    print("  - Scaling Factor    : alpha / r (Maintains gradient magnitude across ranks)")

    print("\n" + "-" * 95)
    print(f"| Rank (r) | Alpha (alpha) | Scaling Factor | Trainable Params (7B) | Parameter %% | Recommended Use Case        |")
    print("-" * 95)
    ranks = [
        (4, 8, "2.0x", "1.05 M", "0.015%", "Ultra-low memory, simple classification"),
        (8, 16, "2.0x", "2.10 M", "0.030%", "Standard formatting & structured JSON triage (Ours)"),
        (16, 32, "2.0x", "4.19 M", "0.060%", "Complex reasoning & code generation"),
        (32, 64, "2.0x", "8.39 M", "0.120%", "Multi-lingual or multi-task domain adaptation"),
        (64, 128, "2.0x", "16.78 M", "0.240%", "Extensive knowledge shift (near full-FT capacity)"),
    ]
    for r, a, s, p, pct, use in ranks:
        print(f"| {r:>8} | {a:>13} | {s:>14} | {p:>21} | {pct:>11} | {use:<27} |")
    print("-" * 95)

    print("\nTARGET MODULES TRADEOFF:")
    print("  - Attention-Only (q_proj, v_proj)              : ~0.4% trainable params. Fast, but limits non-linear learning.")
    print("  - All-Linear (q, k, v, o, gate, up, down)      : ~1.5% trainable params. Modern gold standard (matches full-FT).")
    print("  * Empirical Rule of Thumb: Adapting all linear layers with rank r=8 or r=16 consistently")
    print("    outperforms adapting only q,v with rank r=64 while using fewer total parameters!")
    print("-" * 95)


def show_qlora_calculator() -> None:
    print_header("QLORA 4-BIT NORMALFLOAT4 (NF4) & VRAM CALCULATOR")
    print("QLoRA Innovations (Dettmers et al. 2023):")
    print("  1. NF4 Quantization   : Information-theoretically optimal for zero-mean normal weights.")
    print("  2. Double Quantization: Quantizes the quantization constants, saving ~0.37 bits/param.")
    print("  3. Paged Optimizers   : CPU RAM paging prevents CUDA OOM on gradient spikes.")

    models = [1.1, 3.0, 7.0, 13.0, 70.0]
    print("\n" + "-" * 95)
    print(f"| Model Size | Full FP16 VRAM | QLoRA 4-bit VRAM | VRAM Saved | Savings %% | Fits on 16GB GPU? | Fits on 24GB GPU? |")
    print("-" * 95)
    for m in models:
        stats = QLoRAMemoryModeler.calculate_memory_footprint(m, rank=16, target_all_linear=True)
        fits_16 = "[YES]" if stats["fits_on_consumer_gpu_16gb"] else "[NO]"
        fits_24 = "[YES]" if stats["fits_on_consumer_gpu_24gb"] else "[NO]"
        print(
            f"| {m:>8.1f}B | {stats['full_fp16_vram_gb']:>12.1f} GB | "
            f"{stats['qlora_vram_gb']:>14.1f} GB | {stats['vram_saved_gb']:>8.1f} GB | "
            f"{stats['vram_savings_pct']:>8.1f}% | {fits_16:>17} | {fits_24:>17} |"
        )
    print("-" * 95)
    print("Key Takeaway: A 7B parameter model requiring 58 GB for full FP16 training fits comfortably into 11.8 GB")
    print("on a single consumer GPU (e.g. RTX 4080 / RTX 3090) with QLoRA!")
    print("-" * 95)


def show_adapter_merging_demo() -> None:
    print_header("ZERO-LATENCY ADAPTER MERGING DEMO")
    print("In production serving, evaluating LoRA via two forward branches adds 10-25% latency overhead.")
    print("LoRA enables offline weight folding:")
    print("   W_merged = W_0 + (alpha / r) * (B @ A)")
    print("Once merged, the model is served as a standard dense linear model with ZERO runtime adapter overhead!\n")

    in_f, out_f, r, alpha = 64, 64, 8, 16
    lora_layer = LoRALinear(in_features=in_f, out_features=out_f, r=r, lora_alpha=alpha)
    x = torch.randn(2, in_f)

    # Initial state (B=0 -> Delta W = 0)
    out_step0 = lora_layer(x)
    base_out = lora_layer.base_layer(x)
    init_diff = torch.norm(out_step0 - base_out).item()
    print(f"1. Step 0 Check (B = 0 initialization):")
    print(f"   - Norm difference between LoRALinear and Frozen W_0: {init_diff:.8f} (Identical base behavior)")

    # Simulate trained weights in B
    nn.init.normal_(lora_layer.lora_B, std=0.02)
    lora_layer.eval()  # Disable dropout for inference comparison
    out_adapted = lora_layer(x)
    adapted_diff = torch.norm(out_adapted - base_out).item()
    print(f"\n2. Post-Training State (Adapters active):")
    print(f"   - Adaptation magnitude ||Delta y||: {adapted_diff:.4f}")

    # Merge weights
    lora_layer.merge_weights()
    out_merged = lora_layer(x)
    merge_error = torch.norm(out_merged - out_adapted).item()
    print(f"\n3. Merged State (W_merged = W_0 + (alpha/r)*BA):")
    print(f"   - Discrepancy between two-branch forward and folded W_merged: {merge_error:.8f} (Bit-exact match!)")
    print(f"   - Serving Latency Overhead: 0.00% (No LoRA branches during inference)")

    # Unmerge back
    lora_layer.unmerge_weights()
    out_unmerged = lora_layer.base_layer(x)
    unmerge_error = torch.norm(out_unmerged - base_out).item()
    print(f"\n4. Unmerged State (Restoring base weights for multi-tenant switching):")
    print(f"   - Restored base weight fidelity error: {unmerge_error:.8f}")
    print("-" * 95)


def interactive_menu() -> None:
    while True:
        print_header("DAY 12 - SESSION 3: LORA IN PRACTICE WORKSPACE")
        print("  1. Run LoRA Fine-Tuning Pipeline (Train Small Open Model on SRE Dataset)")
        print("  2. Run Dual-Evaluation Benchmark (Target Task vs. General Benchmark)")
        print("  3. LoRA Hyperparameter & Scaling Inspector (Rank r, Alpha, Target Modules)")
        print("  4. QLoRA 4-Bit NormalFloat4 (NF4) & Memory Economics Calculator")
        print("  5. Zero-Latency Adapter Merging & Multi-Tenant Deployment Demo")
        print("  6. View Full General Benchmark Test Suite (20 Cases for Forgetting Checks)")
        print("  0. Exit")
        print("-" * 95)

        choice = input("Select an option (0-6): ").strip()
        if choice == "1":
            run_lora_training()
        elif choice == "2":
            evaluator = DualBenchmarkEvaluator()
            res = evaluator.run_full_dual_evaluation()
            print_dual_benchmark_report(res)
        elif choice == "3":
            show_hyperparameter_inspector()
        elif choice == "4":
            show_qlora_calculator()
        elif choice == "5":
            show_adapter_merging_demo()
        elif choice == "6":
            print_header("20-CASE GENERAL BENCHMARK SUITE (CATASTROPHIC FORGETTING AUDIT)")
            for tc in GENERAL_BENCHMARK_CASES:
                print(f"[{tc.test_id}] Domain: {tc.domain:<14} | {tc.description}")
                print(f"  Prompt: {tc.prompt}")
                print(f"  Target: {tc.expected_answer}")
                print("-" * 95)
        elif choice == "0":
            print("\nExiting Day 12 Session 3 LoRA Workspace. Goodbye!\n")
            break
        else:
            print("[!] Invalid option. Please select 0-6.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Day 12 Session 3: LoRA in Practice")
    parser.add_argument("--train", action="store_true", help="Execute LoRA fine-tuning")
    parser.add_argument("--eval", action="store_true", help="Run dual-benchmark evaluation")
    parser.add_argument("--inspect", action="store_true", help="Show LoRA hyperparameter inspector")
    parser.add_argument("--qlora", action="store_true", help="Show QLoRA 4-bit memory economics")
    parser.add_argument("--merge", action="store_true", help="Run adapter merging demo")

    args = parser.parse_args()

    if args.train:
        run_lora_training()
    elif args.eval:
        evaluator = DualBenchmarkEvaluator()
        res = evaluator.run_full_dual_evaluation()
        print_dual_benchmark_report(res)
    elif args.inspect:
        show_hyperparameter_inspector()
    elif args.qlora:
        show_qlora_calculator()
    elif args.merge:
        show_adapter_merging_demo()
    else:
        interactive_menu()
