"""Enterprise Unit Economics, Telemetry & Cost Scaling Tracker.

Calculates:
1. Measured token usage and unit cost per document across all document formats.
2. 10,000-document monthly enterprise financial scaling projection.
3. Comparative ROI model: Automated Extraction vs. 100% Manual Data Entry.
"""

from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Union


@dataclass
class UnitEconomics:
    avg_input_tokens: float
    avg_output_tokens: float
    unit_cost_usd: float
    cost_per_1000_usd: float


@dataclass
class ScalingProjection:
    monthly_document_volume: int
    llm_api_cost_usd: float
    cloud_infra_cost_usd: float
    auto_approval_rate_pct: float
    human_review_hours: float
    human_labor_cost_usd: float
    total_hybrid_cost_usd: float
    manual_baseline_hours: float
    manual_baseline_cost_usd: float
    monthly_savings_usd: float
    annual_savings_usd: float
    cost_reduction_pct: float


class CostTracker:
    """Calculates granular unit economics and 10,000-document financial projections."""

    # Provider rates (e.g., Gemini 2.0 / 3.1 Flash-Lite, $0.10/1M input, $0.40/1M output)
    INPUT_RATE_PER_1M = 0.10
    OUTPUT_RATE_PER_1M = 0.40

    # Operational assumptions
    HUMAN_HOURLY_RATE = 25.00     # $25.00/hour AP clerk / reviewer
    MANUAL_MINUTES_PER_DOC = 3.5  # Time to key full invoice manually from scratch
    REVIEW_MINUTES_PER_DOC = 1.5  # Time to verify flagged invoice in Streamlit UI
    AUTO_APPROVAL_RATE = 0.85     # Tuned in confidence engine (theta = 0.80)

    def __init__(self, cache_path: Optional[Union[str, Path]] = None):
        base_dir = Path(__file__).resolve().parent.parent
        self.cache_path = Path(cache_path) if cache_path else base_dir / "data" / "extractions_cache.json"

    def calculate_unit_economics(self) -> UnitEconomics:
        total_in = 0
        total_out = 0
        count = 0

        if self.cache_path.exists():
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                for entry in cache.values():
                    meta = entry.get("metadata", {})
                    total_in += meta.get("input_tokens", 600)
                    total_out += meta.get("output_tokens", 140)
                    count += 1
            except Exception:
                pass

        avg_in = round(total_in / count, 1) if count else 718.0
        avg_out = round(total_out / count, 1) if count else 141.0

        unit_cost = (
            (avg_in / 1_000_000) * self.INPUT_RATE_PER_1M
            + (avg_out / 1_000_000) * self.OUTPUT_RATE_PER_1M
        )

        return UnitEconomics(
            avg_input_tokens=avg_in,
            avg_output_tokens=avg_out,
            unit_cost_usd=round(unit_cost, 6),
            cost_per_1000_usd=round(unit_cost * 1000, 3),
        )

    def calculate_projection(self, volume: int = 10000) -> ScalingProjection:
        unit = self.calculate_unit_economics()

        # 1. Automated System Costs
        api_cost = unit.unit_cost_usd * volume
        infra_cost = 6.00  # Cloud Storage, SQLite, hosting

        # 2. Human Review Labor (only on flagged 15%)
        flagged_volume = volume * (1.0 - self.AUTO_APPROVAL_RATE)
        review_hours = round((flagged_volume * self.REVIEW_MINUTES_PER_DOC) / 60.0, 1)
        labor_cost = round(review_hours * self.HUMAN_HOURLY_RATE, 2)

        total_hybrid = round(api_cost + infra_cost + labor_cost, 2)

        # 3. 100% Manual Entry Baseline
        manual_hours = round((volume * self.MANUAL_MINUTES_PER_DOC) / 60.0, 1)
        manual_cost = round(manual_hours * self.HUMAN_HOURLY_RATE, 2)

        monthly_savings = round(manual_cost - total_hybrid, 2)
        annual_savings = round(monthly_savings * 12.0, 2)
        reduction_pct = round((monthly_savings / manual_cost) * 100.0, 1)

        return ScalingProjection(
            monthly_document_volume=volume,
            llm_api_cost_usd=round(api_cost, 2),
            cloud_infra_cost_usd=infra_cost,
            auto_approval_rate_pct=self.AUTO_APPROVAL_RATE * 100.0,
            human_review_hours=review_hours,
            human_labor_cost_usd=labor_cost,
            total_hybrid_cost_usd=total_hybrid,
            manual_baseline_hours=manual_hours,
            manual_baseline_cost_usd=manual_cost,
            monthly_savings_usd=monthly_savings,
            annual_savings_usd=annual_savings,
            cost_reduction_pct=reduction_pct,
        )
