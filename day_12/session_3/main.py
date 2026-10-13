"""
Day 12 - Session 03: LoRA in Practice
Demonstrates Low-Rank Adaptation (LoRA) parameter-efficient fine-tuning
and evaluates against catastrophic forgetting using dual benchmarks.
"""

from __future__ import annotations
import os
import json
from train_lora import run_lora_training
from eval_benchmarks import DualBenchmarkEvaluator, print_dual_benchmark_report


def main():
    print("Day 12 Session 03: LoRA Training & Dual-Benchmark Evaluation\n")

    # 1. Run LoRA training pipeline
    print("Running LoRA training loop (freezing base model W_0, training adapter A & B)...")
    train_res = run_lora_training(epochs=3, rank=8, alpha=16)
    print(f"LoRA Training Complete: Final Loss = {train_res['final_loss']:.4f} across {train_res['total_steps']} steps.")

    # 2. Dual-Benchmark Evaluation
    print("\nRunning Dual-Benchmark Evaluation (Domain Task vs General Benchmark)...")
    evaluator = DualBenchmarkEvaluator()
    report = evaluator.run_evaluation(weights_path=train_res.get("checkpoint_path"))
    print_dual_benchmark_report(report)

    assert report["catastrophic_forgetting_detected"] is False, "Catastrophic forgetting detected!"
    print("\nVerification Passed: LoRA achieved high domain accuracy without catastrophic forgetting.")


if __name__ == "__main__":
    main()
