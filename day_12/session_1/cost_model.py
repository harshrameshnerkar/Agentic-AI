"""
Day 12 - Session 1: Total Cost of Ownership (TCO) & Economic Calculator
======================================================================
Models the full lifecycle financial cost of:
  1. Option A: In-Context RAG + Prompt Caching (Current OpsSentinel AI)
  2. Option B: Cloud-Managed Fine-Tuned Model (OpenAI / Vertex AI)
  3. Option C: Dedicated Self-Hosted Fine-Tuned SLM (AWS EC2 g5.2xlarge A10G)

Calculates:
  - Upfront capital expenditure (Dataset curation, labeling, compute, MLOps setup)
  - Monthly operational expenses (Token costs, fixed GPU node hosting)
  - Cumulative 12-month TCO
  - Volume breakeven thresholds
"""

import os
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class UpfrontCostBreakdown(BaseModel):
    dataset_curation_sre_hours: float = 50.0
    sre_hourly_rate: float = 125.0
    synthetic_data_api_cost: float = 1500.0
    expert_qa_review_hours: float = 20.0
    qa_hourly_rate: float = 75.0
    training_compute_gpu_hours: float = 48.0
    gpu_hourly_rate_a100: float = 4.10  # 8x A100 node rate / instance hour equivalent
    eval_harness_mlops_hours: float = 25.0
    mlops_hourly_rate: float = 125.0
    integration_testing_hours: float = 12.0
    software_hourly_rate: float = 125.0

    @property
    def total_curation_cost(self) -> float:
        return self.dataset_curation_sre_hours * self.sre_hourly_rate

    @property
    def total_qa_cost(self) -> float:
        return self.expert_qa_review_hours * self.qa_hourly_rate

    @property
    def total_compute_cost(self) -> float:
        return self.training_compute_gpu_hours * self.gpu_hourly_rate_a100

    @property
    def total_eval_harness_cost(self) -> float:
        return self.eval_harness_mlops_hours * self.mlops_hourly_rate

    @property
    def total_integration_cost(self) -> float:
        return self.integration_testing_hours * self.software_hourly_rate

    @property
    def total_upfront_cost(self) -> float:
        return (
            self.total_curation_cost
            + self.synthetic_data_api_cost
            + self.total_qa_cost
            + self.total_compute_cost
            + self.total_eval_harness_cost
            + self.total_integration_cost
        )


class CostModelEngine:
    def __init__(self):
        # Pricing from Cost Tracker Tab & AWS EC2 pricing
        self.rag_input_cost_per_m = 0.150       # $0.15 / 1M input tokens (Gemini 1.5 Flash / GPT-4o-mini)
        self.rag_output_cost_per_m = 0.600      # $0.60 / 1M output tokens
        self.rag_cache_discount = 0.75          # 75% discount on cached prompt prefix
        self.rag_cache_hit_rate = 0.85          # 85% cache hit on static system prompt
        self.rag_avg_context_tokens = 407.9     # Proven Day 11 Session 4 average
        self.rag_avg_output_tokens = 35.0

        # Managed Fine-Tuned Pricing (2x to 3x base model inference price)
        self.ft_input_cost_per_m = 0.300        # $0.30 / 1M input tokens
        self.ft_output_cost_per_m = 1.200       # $1.20 / 1M output tokens
        self.ft_avg_context_tokens = 250.0      # Slightly smaller prompt (no few-shots needed)
        self.ft_avg_output_tokens = 35.0

        # Self-Hosted SLM Pricing (AWS EC2 g5.2xlarge: 1x NVIDIA A10G 24GB VRAM)
        # On-demand: $1.212/hr. 1-year reserved: $0.755/hr. 730 hours/month = $551.15 - $884.76
        self.self_hosted_gpu_monthly = 734.00   # Blended reserved + storage + egress
        self.gpu_max_monthly_capacity = 350000  # Max requests 1x A10G can serve comfortably

        self.upfront = UpfrontCostBreakdown()

    def compute_rag_monthly_cost(self, monthly_volume: int) -> float:
        """Computes serverless RAG monthly cost factoring in prompt caching."""
        # Split prompt tokens: 126 static tokens (eligible for cache) + 282 dynamic tokens
        static_tokens = 126.0
        dynamic_tokens = self.rag_avg_context_tokens - static_tokens

        # Cached static cost
        cached_rate = self.rag_input_cost_per_m * (1.0 - self.rag_cache_discount)
        blended_static_rate = (self.rag_cache_hit_rate * cached_rate) + ((1.0 - self.rag_cache_hit_rate) * self.rag_input_cost_per_m)
        input_cost = monthly_volume * ((static_tokens * blended_static_rate + dynamic_tokens * self.rag_input_cost_per_m) / 1_000_000)

        output_cost = monthly_volume * (self.rag_avg_output_tokens / 1_000_000) * self.rag_output_cost_per_m
        return round(input_cost + output_cost, 4)

    def compute_managed_ft_monthly_cost(self, monthly_volume: int) -> float:
        """Computes cloud-managed fine-tuned model monthly inference fees."""
        input_cost = monthly_volume * (self.ft_avg_context_tokens / 1_000_000) * self.ft_input_cost_per_m
        output_cost = monthly_volume * (self.ft_avg_output_tokens / 1_000_000) * self.ft_output_cost_per_m
        return round(input_cost + output_cost, 4)

    def compute_self_hosted_monthly_cost(self, monthly_volume: int) -> float:
        """Computes dedicated self-hosted GPU infrastructure cost (scaling GPUs with volume)."""
        num_gpus = max(1, (monthly_volume + self.gpu_max_monthly_capacity - 1) // self.gpu_max_monthly_capacity)
        return round(num_gpus * self.self_hosted_gpu_monthly, 2)

    def generate_tco_comparison(self, volumes: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """Generates full comparative scorecard across volume milestones."""
        if volumes is None:
            volumes = [10000, 50000, 250000, 1000000, 5000000]

        results = []
        for vol in volumes:
            rag_mo = self.compute_rag_monthly_cost(vol)
            ft_mo = self.compute_managed_ft_monthly_cost(vol)
            gpu_mo = self.compute_self_hosted_monthly_cost(vol)

            upfront_ft = self.upfront.total_upfront_cost

            rag_12m = rag_mo * 12
            ft_12m = upfront_ft + (ft_mo * 12)
            gpu_12m = upfront_ft + (gpu_mo * 12)

            results.append({
                "monthly_volume": vol,
                "rag_monthly_cost": rag_mo,
                "managed_ft_monthly_cost": ft_mo,
                "self_hosted_monthly_cost": gpu_mo,
                "rag_12m_tco": round(rag_12m, 2),
                "managed_ft_12m_tco": round(ft_12m, 2),
                "self_hosted_12m_tco": round(gpu_12m, 2),
                "savings_rag_vs_managed_12m": round(ft_12m - rag_12m, 2),
                "savings_rag_vs_self_hosted_12m": round(gpu_12m - rag_12m, 2),
            })
        return results

    def calculate_breakeven_volume(self) -> Dict[str, Any]:
        """
        Calculates at what monthly volume self-hosting becomes cheaper than serverless RAG
        (pure monthly operational expense basis, ignoring upfront training costs).
        """
        # rag_cost(vol) = vol * unit_rag_cost
        # gpu_cost(1 gpu) = 734.00
        # Breakeven: vol * unit_rag_cost >= 734.00
        test_vol = 100000
        unit_rag_cost = self.compute_rag_monthly_cost(test_vol) / test_vol
        breakeven_vol = self.self_hosted_gpu_monthly / unit_rag_cost

        # With upfront cost factored into 1 year:
        # (12 * vol * unit_rag_cost) >= Upfront + (12 * 734)
        annual_upfront = self.upfront.total_upfront_cost
        # In fact, since unit_rag_cost is smaller than self-hosted monthly cost per unit capacity,
        # self-hosting never breaks even below single-GPU capacity!
        return {
            "unit_rag_cost_per_query": round(unit_rag_cost, 7),
            "pure_monthly_opex_breakeven_volume": int(breakeven_vol),
            "single_gpu_capacity_limit": self.gpu_max_monthly_capacity,
            "can_breakeven_on_single_gpu": breakeven_vol < self.gpu_max_monthly_capacity,
            "conclusion": (
                f"Serverless RAG costs ${unit_rag_cost:.6f} per query. A dedicated A10G GPU costs ${self.self_hosted_gpu_monthly}/mo. "
                f"You would need over {int(breakeven_vol):,} queries/month just to match monthly hosting fees, "
                f"which exceeds the throughput of a single GPU ({self.gpu_max_monthly_capacity:,} ops). "
                f"Therefore, self-hosting is NEVER cheaper than RAG under current pricing."
            ),
        }


# Singleton instance
cost_model = CostModelEngine()
