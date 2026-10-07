"""
Day 12 - Session 3: LoRA & QLoRA Architectural Engine
=====================================================
Implements:
  1. Low-Rank Adaptation (LoRA) Linear Layer (W = W_0 + (alpha / r) * B * A)
  2. Freezing Base Weight W_0 & Zero-Initialization of B (Identity at step 0)
  3. Hyperparameter Scaling Dynamics (Rank r, Alpha alpha, Scaling Factor alpha/r)
  4. Target Module Mapping (Attention-only vs All-Linear MLP projections)
  5. QLoRA 4-Bit NormalFloat4 (NF4) & Double Quantization (DQ) Memory Modeling
  6. Zero-Latency Weight Merging & Unmerging for Serving
"""

import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class LoRAConfig:
    """Hyperparameter specification for Low-Rank Adaptation (LoRA)."""
    r: int = 8                                  # Intrinsic rank dimension
    lora_alpha: int = 16                        # LoRA scaling factor (alpha)
    lora_dropout: float = 0.05                  # Dropout applied to low-rank input
    target_modules: List[str] = field(          # Transformer projection layers to adapt
        default_factory=lambda: ["q_proj", "v_proj", "k_proj", "o_proj"]
    )
    bias: str = "none"                          # "none" | "all" | "lora_only"
    use_qlora_4bit: bool = True                 # Whether base weights emulate 4-bit NF4
    task_type: str = "CAUSAL_LM"

    @property
    def scaling(self) -> float:
        """Computes delta scaling factor: alpha / r."""
        return self.lora_alpha / self.r if self.r > 0 else 1.0


class LoRALinear(nn.Module):
    """
    Core Low-Rank Adaptation (LoRA) Layer implementing:
        h = W_0 * x + (alpha / r) * B * A * x
    where:
      - W_0 in R^{out_features x in_features} is FROZEN (no gradient compute).
      - A in R^{r x in_features} is initialized with Gaussian / Kaiming distribution.
      - B in R^{out_features x r} is initialized to ZERO, ensuring Delta W = 0 at step 0.
    """

    def __init__(
        self,
        in_features: int,
        out_features: int,
        r: int = 8,
        lora_alpha: int = 16,
        lora_dropout: float = 0.05,
        bias: bool = False,
    ):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.r = r
        self.lora_alpha = lora_alpha
        self.scaling = lora_alpha / r if r > 0 else 1.0

        # 1. Base Weight W_0 (FROZEN)
        self.base_layer = nn.Linear(in_features, out_features, bias=bias)
        self.base_layer.weight.requires_grad = False
        if bias and self.base_layer.bias is not None:
            self.base_layer.bias.requires_grad = False

        # 2. LoRA Low-Rank Matrices: A and B
        if r > 0:
            self.lora_dropout = nn.Dropout(p=lora_dropout) if lora_dropout > 0.0 else nn.Identity()
            # Down-projection matrix A: R^{in_features} -> R^{r}
            self.lora_A = nn.Parameter(torch.empty(r, in_features))
            # Up-projection matrix B: R^{r} -> R^{out_features}
            self.lora_B = nn.Parameter(torch.zeros(out_features, r))

            # Initialize A with Kaiming uniform and B with strict zeros
            nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))
            nn.init.zeros_(self.lora_B)

        self.merged: bool = False

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward computation:
          If merged: h = W_merged * x
          If unmerged: h = W_0 * x + (alpha / r) * (x * A^T * B^T)
        """
        base_out = self.base_layer(x)
        if self.r == 0 or self.merged:
            return base_out

        # LoRA branch: x -> Dropout -> A -> B * scaling
        lora_in = self.lora_dropout(x)
        # Compute x @ A.T -> shape [..., r]
        lora_hidden = F.linear(lora_in, self.lora_A)
        # Compute hidden @ B.T -> shape [..., out_features]
        lora_out = F.linear(lora_hidden, self.lora_B)

        return base_out + self.scaling * lora_out

    def merge_weights(self) -> None:
        """Merges Delta W = (alpha / r) * B * A directly into W_0 for zero-latency serving."""
        if self.merged or self.r == 0:
            return
        delta_w = self.scaling * (self.lora_B @ self.lora_A)
        self.base_layer.weight.data += delta_w
        self.merged = True

    def unmerge_weights(self) -> None:
        """Reverses weight merge, returning W_0 to pristine base state."""
        if not self.merged or self.r == 0:
            return
        delta_w = self.scaling * (self.lora_B @ self.lora_A)
        self.base_layer.weight.data -= delta_w
        self.merged = False


class QLoRAMemoryModeler:
    """
    Models the theoretical and empirical memory savings of QLoRA:
      - 4-bit NormalFloat4 (NF4) quantization vs FP16
      - Double Quantization (DQ) savings
      - Paged Optimizers memory headroom
    """

    @staticmethod
    def calculate_memory_footprint(
        param_count_billions: float,
        rank: int = 16,
        target_all_linear: bool = True,
        batch_size: int = 4,
        seq_length: int = 2048,
    ) -> Dict[str, Any]:
        """Calculates precise memory consumption across FP32, FP16, INT8, and QLoRA 4-bit."""
        params_bytes = param_count_billions * 1e9

        # Base Model Weights (VRAM)
        fp32_base_gb = (params_bytes * 4) / (1024**3)
        fp16_base_gb = (params_bytes * 2) / (1024**3)
        int8_base_gb = (params_bytes * 1) / (1024**3)
        # QLoRA: 4 bits per param = 0.5 bytes + Double Quantization (saving ~0.37 bits/param)
        qlora_base_gb = (params_bytes * 0.55) / (1024**3)

        # LoRA Trainable Parameters Estimate
        # Target all linear: ~1.5% of total params at r=16; attention-only: ~0.4%
        trainable_ratio = 0.015 if target_all_linear else 0.004
        trainable_ratio *= (rank / 16.0)
        trainable_params = params_bytes * trainable_ratio
        adapter_fp16_mb = (trainable_params * 2) / (1024**2)

        # Optimizer States (AdamW: FP32 copy + 1st momentum + 2nd momentum = 16 bytes/param)
        full_ft_opt_gb = (params_bytes * 16) / (1024**3)
        # LoRA optimizer: only for trainable parameters (16 bytes/trainable param)
        lora_opt_gb = (trainable_params * 16) / (1024**3)

        # Gradients (FP16: 2 bytes/param)
        full_ft_grad_gb = (params_bytes * 2) / (1024**3)
        lora_grad_gb = (trainable_params * 2) / (1024**3)

        # Total Training VRAM Footprint
        full_fp16_total_gb = fp16_base_gb + full_ft_opt_gb + full_ft_grad_gb + 2.5
        qlora_total_gb = qlora_base_gb + (adapter_fp16_mb / 1024) + lora_opt_gb + lora_grad_gb + 1.5

        savings_pct = (1.0 - (qlora_total_gb / full_fp16_total_gb)) * 100.0

        return {
            "model_size_billions": param_count_billions,
            "rank": rank,
            "target_all_linear": target_all_linear,
            "trainable_parameters_m": trainable_params / 1e6,
            "trainable_percentage": trainable_ratio * 100.0,
            "full_fp16_vram_gb": round(full_fp16_total_gb, 2),
            "qlora_vram_gb": round(qlora_total_gb, 2),
            "vram_saved_gb": round(full_fp16_total_gb - qlora_total_gb, 2),
            "vram_savings_pct": round(savings_pct, 1),
            "fits_on_consumer_gpu_24gb": qlora_total_gb <= 24.0,
            "fits_on_consumer_gpu_16gb": qlora_total_gb <= 16.0,
        }
