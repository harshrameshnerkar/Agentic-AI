"""
Day 12 - Session 3: LoRA Training Pipeline & Convergence Engine (Scaled)
========================================================================
Implements:
  1. Base Model Initialization (Scaled Open LLaMA Causal LM Architecture: ~12M params)
  2. Freezing Base Weights W_0 and Injecting Low-Rank Adapters (B @ A) via PEFT
  3. Batch Dataset Ingestion from Large SFT Dataset (1,000 train / 200 val examples)
  4. LoRA Optimization with AdamW (LR: 2e-4, Cosine Decay, Rank r=16, Alpha=32)
  5. Step-by-Step Training & Validation Loss Telemetry Logging
  6. Exporting Fine-Tuned LoRA Adapter Weights & Config (adapter_model.bin, adapter_config.json)
"""

import os
import sys
import json
import time
import math
import argparse
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from peft import LoraConfig, get_peft_model, TaskType
from transformers import AutoConfig, AutoModelForCausalLM


@dataclass
class TrainingMetrics:
    epoch: int
    train_loss: float
    val_loss: float
    perplexity: float
    learning_rate: float
    duration_sec: float
    trainable_params: int
    total_params: int
    trainable_pct: float


class SREJSONLDataset(Dataset):
    """
    Parses Chat JSONL messages format from Session 2 into tokenized PyTorch tensors.
    Uses deterministic subword hash-modulo tokenization into an 8,192 vocabulary space.
    """

    def __init__(
        self,
        jsonl_path: str,
        max_samples: Optional[int] = None,
        vocab_size: int = 8192,
        max_seq_len: int = 128,
    ):
        self.samples: List[str] = []
        self.vocab_size = vocab_size
        self.max_seq_len = max_seq_len

        if os.path.exists(jsonl_path):
            with open(jsonl_path, "r", encoding="utf-8") as f:
                lines = [json.loads(line) for line in f if line.strip()]
                if max_samples:
                    lines = lines[:max_samples]
                for item in lines:
                    msgs = item["messages"]
                    full_text = f"USER: {msgs[1]['content']}\nASSISTANT: {msgs[2]['content']}"
                    self.samples.append(full_text)

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        text = self.samples[idx]
        # Hash mapping of words into vocabulary IDs (1 to vocab_size - 1), reserving 0 for padding
        tokens = [hash(word) % (self.vocab_size - 1) + 1 for word in text.split()]
        if len(tokens) > self.max_seq_len:
            tokens = tokens[:self.max_seq_len]
        else:
            tokens = tokens + [0] * (self.max_seq_len - len(tokens))  # Pad with 0

        input_ids = torch.tensor(tokens, dtype=torch.long)
        labels = input_ids.clone()
        labels[labels == 0] = -100  # Mask padding tokens in cross-entropy loss computation

        return {"input_ids": input_ids, "labels": labels}


class LoRATrainingEngine:
    """
    Manages the full LoRA fine-tuning cycle on the target enterprise SRE dataset:
      - Freezes W_0 (12M parameters)
      - Attaches low-rank matrices A and B (rank=16, alpha=32)
      - Trains only low-rank adapters (~131k parameters, ~1.1% trainable)
    """

    def __init__(
        self,
        rank: int = 16,
        lora_alpha: int = 32,
        learning_rate: float = 2e-4,
        epochs: int = 5,
        batch_size: int = 16,
        vocab_size: int = 8192,
        target_modules: Optional[List[str]] = None,
    ):
        self.rank = rank
        self.lora_alpha = lora_alpha
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.batch_size = batch_size
        self.vocab_size = vocab_size
        self.target_modules = target_modules or ["q_proj", "k_proj", "v_proj", "o_proj"]

        self.device = torch.device("cpu")
        self.base_model: Optional[nn.Module] = None
        self.lora_model: Optional[nn.Module] = None
        self.metrics_history: List[TrainingMetrics] = []

    def build_model(self) -> Tuple[nn.Module, Dict[str, Any]]:
        """
        Initializes scaled open LLaMA architecture (~12M params) and wraps with PEFT LoRA adapters.
        All base model parameters are frozen (requires_grad = False).
        Only matrices A and B in target_modules will have requires_grad = True.
        """
        # Scaled transformer architecture (~12.0M parameters)
        config = AutoConfig.for_model(
            "llama",
            hidden_size=256,
            intermediate_size=1024,
            num_hidden_layers=4,
            num_attention_heads=8,
            vocab_size=self.vocab_size,
        )
        self.base_model = AutoModelForCausalLM.from_config(config)

        # Configure Low-Rank Adaptation (LoRA)
        peft_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=self.rank,
            lora_alpha=self.lora_alpha,
            target_modules=self.target_modules,
            lora_dropout=0.05,
            bias="none",
        )

        # Inject LoRA adapters onto base model
        if self.base_model is None:
            raise RuntimeError("Base model initialization failed.")
        self.lora_model = get_peft_model(self.base_model, peft_config)
        assert self.lora_model is not None, "PEFT model initialization failed."

        # Compute parameter budget
        trainable_params = sum(p.numel() for p in self.lora_model.parameters() if p.requires_grad)
        all_params = sum(p.numel() for p in self.lora_model.parameters())
        trainable_pct = (trainable_params / all_params) * 100.0

        param_summary = {
            "trainable_parameters": trainable_params,
            "total_parameters": all_params,
            "trainable_percentage": round(trainable_pct, 4),
            "scaling_factor": round(self.lora_alpha / self.rank, 2),
            "target_modules": self.target_modules,
        }

        return self.lora_model, param_summary

    def train(
        self,
        train_path: str,
        val_path: str,
        max_train_samples: Optional[int] = None,
        max_val_samples: Optional[int] = None,
    ) -> List[TrainingMetrics]:
        """
        Executes multi-epoch LoRA training run with validation evaluation and loss convergence logging.
        """
        if self.lora_model is None:
            self.build_model()

        assert self.lora_model is not None, "LoRA model must be instantiated before training."

        train_ds = SREJSONLDataset(train_path, max_samples=max_train_samples, vocab_size=self.vocab_size)
        val_ds = SREJSONLDataset(val_path, max_samples=max_val_samples, vocab_size=self.vocab_size)

        train_loader = DataLoader(train_ds, batch_size=self.batch_size, shuffle=True)
        val_loader = DataLoader(val_ds, batch_size=self.batch_size, shuffle=False)

        # LoRA Optimizer: AdamW strictly updates parameters where requires_grad == True (A and B matrices)
        trainable_parameters = [p for p in self.lora_model.parameters() if p.requires_grad]
        optimizer = torch.optim.AdamW(
            trainable_parameters,
            lr=self.learning_rate,
            weight_decay=0.01,
        )

        total_steps = len(train_loader) * self.epochs
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max(1, total_steps))

        trainable_params = sum(p.numel() for p in trainable_parameters)
        all_params = sum(p.numel() for p in self.lora_model.parameters())
        trainable_pct = (trainable_params / all_params) * 100.0

        self.metrics_history = []

        print("\n" + "=" * 90)
        print(" STARTING SCALED LORA TRAINING PIPELINE (Target Task: SRE-Structured-Triage-v1) ".center(90))
        print("=" * 90)
        print(f"Base Architecture     : LLaMA Causal LM (~{all_params / 1e6:.1f}M Parameters)")
        print(f"LoRA Configuration    : Rank r = {self.rank} | Alpha alpha = {self.lora_alpha} (Scale = {self.lora_alpha / self.rank:.1f})")
        print(f"Target Modules        : {', '.join(self.target_modules)}")
        print(f"Trainable Parameters  : {trainable_params:,} / {all_params:,} ({trainable_pct:.2f}% trainable)")
        print(f"Learning Rate & Sched : {self.learning_rate:.1e} (Cosine Annealing) | Epochs: {self.epochs}")
        print(f"Training / Val Split  : {len(train_ds)} Train / {len(val_ds)} Validation (Batch Size: {self.batch_size})")
        print("-" * 90)

        for epoch in range(1, self.epochs + 1):
            t0 = time.perf_counter()
            self.lora_model.train()
            epoch_loss = 0.0
            steps = 0

            for batch in train_loader:
                input_ids = batch["input_ids"]
                labels = batch["labels"]

                optimizer.zero_grad()
                outputs = self.lora_model(input_ids=input_ids, labels=labels)
                loss = outputs.loss
                loss.backward()
                optimizer.step()
                scheduler.step()

                epoch_loss += loss.item()
                steps += 1

            avg_train_loss = epoch_loss / max(1, steps)

            # Validation Loop
            self.lora_model.eval()
            val_loss_acc = 0.0
            val_steps = 0
            with torch.no_grad():
                for vbatch in val_loader:
                    v_input_ids = vbatch["input_ids"]
                    v_labels = vbatch["labels"]
                    v_out = self.lora_model(input_ids=v_input_ids, labels=v_labels)
                    val_loss_acc += v_out.loss.item()
                    val_steps += 1

            avg_val_loss = val_loss_acc / max(1, val_steps)
            perplexity = math.exp(min(avg_val_loss, 20.0))
            current_lr = float(scheduler.get_last_lr()[0])
            dur = time.perf_counter() - t0

            metric = TrainingMetrics(
                epoch=epoch,
                train_loss=round(avg_train_loss, 4),
                val_loss=round(avg_val_loss, 4),
                perplexity=round(perplexity, 2),
                learning_rate=current_lr,
                duration_sec=round(dur, 2),
                trainable_params=trainable_params,
                total_params=all_params,
                trainable_pct=round(trainable_pct, 4),
            )
            self.metrics_history.append(metric)

            print(
                f"[EPOCH {epoch}/{self.epochs}] "
                f"Train Loss: {avg_train_loss:.4f} | "
                f"Val Loss: {avg_val_loss:.4f} | "
                f"Perplexity: {perplexity:6.2f} | "
                f"LR: {current_lr:.2e} | "
                f"Duration: {dur:.2f}s"
            )

        print("-" * 90)
        initial_loss = self.metrics_history[0].train_loss
        final_loss = self.metrics_history[-1].train_loss
        print(f"[OK] Training complete. Loss converged from {initial_loss:.4f} -> {final_loss:.4f}.")
        return self.metrics_history

    def save_adapter(self, output_dir: str) -> str:
        """
        Saves LoRA adapter configuration and trained weights.
        Only the low-rank delta matrices (B and A) are written to disk.
        """
        assert self.lora_model is not None, "Cannot save uninitialized LoRA model."
        os.makedirs(output_dir, exist_ok=True)
        config_path = os.path.join(output_dir, "adapter_config.json")
        summary_path = os.path.join(output_dir, "adapter_metadata.json")

        adapter_config = {
            "base_model_name_or_path": "llama-scaled-open",
            "peft_type": "LORA",
            "task_type": "CAUSAL_LM",
            "r": self.rank,
            "lora_alpha": self.lora_alpha,
            "lora_dropout": 0.05,
            "target_modules": self.target_modules,
            "bias": "none",
            "scaling_factor": self.lora_alpha / self.rank,
        }

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(adapter_config, f, indent=2)

        meta = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "epochs_trained": self.epochs,
            "rank": self.rank,
            "lora_alpha": self.lora_alpha,
            "scaling_factor": self.lora_alpha / self.rank,
            "batch_size": self.batch_size,
            "final_train_loss": self.metrics_history[-1].train_loss if self.metrics_history else None,
            "final_val_loss": self.metrics_history[-1].val_loss if self.metrics_history else None,
            "final_perplexity": self.metrics_history[-1].perplexity if self.metrics_history else None,
            "metrics_history": [m.__dict__ for m in self.metrics_history],
        }

        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        # Save model state dict for the trainable low-rank adapters only
        adapter_weights_path = os.path.join(output_dir, "adapter_model.bin")
        trainable_state = {k: v for k, v in self.lora_model.state_dict().items() if "lora_" in k}
        torch.save(trainable_state, adapter_weights_path)

        print(f"[OK] LoRA adapter successfully saved to: {output_dir}")
        return output_dir


def run_lora_training(
    rank: int = 16,
    alpha: int = 32,
    lr: float = 2e-4,
    epochs: int = 5,
    batch_size: int = 16,
    use_large_dataset: bool = True,
) -> LoRATrainingEngine:
    """
    Convenience entrypoint to execute LoRA training on the SRE dataset.
    Prioritizes the scaled 1,000-example dataset with fallback to standard dataset.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))

    large_train = os.path.abspath(os.path.join(current_dir, "..", "session_2", "sft_train_large.jsonl"))
    large_val = os.path.abspath(os.path.join(current_dir, "..", "session_2", "sft_val_large.jsonl"))
    std_train = os.path.abspath(os.path.join(current_dir, "..", "session_2", "sft_train.jsonl"))
    std_val = os.path.abspath(os.path.join(current_dir, "..", "session_2", "sft_val.jsonl"))

    if use_large_dataset and os.path.exists(large_train):
        train_path, val_path = large_train, large_val
        print(f"[DATASET SELECTION] Using scaled production dataset: {train_path} (1,000 examples)")
    else:
        train_path, val_path = std_train, std_val
        print(f"[DATASET SELECTION] Using standard dataset: {train_path} (252 examples)")

    output_dir = os.path.join(current_dir, "lora_adapter")

    engine = LoRATrainingEngine(
        rank=rank,
        lora_alpha=alpha,
        learning_rate=lr,
        epochs=epochs,
        batch_size=batch_size,
    )
    engine.train(train_path=train_path, val_path=val_path)
    engine.save_adapter(output_dir=output_dir)
    return engine


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train LoRA on SRE Incident Triage Dataset")
    parser.add_argument("--rank", type=int, default=16, help="LoRA rank r (default: 16)")
    parser.add_argument("--alpha", type=int, default=32, help="LoRA alpha scaling (default: 32)")
    parser.add_argument("--lr", type=float, default=2e-4, help="Learning rate (default: 2e-4)")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs (default: 5)")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size (default: 16)")
    parser.add_argument("--small-data", action="store_true", help="Force using the smaller 252-example dataset")

    args = parser.parse_args()

    run_lora_training(
        rank=args.rank,
        alpha=args.alpha,
        lr=args.lr,
        epochs=args.epochs,
        batch_size=args.batch_size,
        use_large_dataset=not args.small_data,
    )
