"""
Model Pricing Engine for LLMOps Token Cost Calculation.
Prices are calibrated per 1,000,000 tokens (industry standard).
"""

from typing import Dict


class ModelPricingEngine:
    # Rates per 1M tokens in USD
    # Format: {"model_name": {"prompt_per_1m": float, "completion_per_1m": float}}
    PRICING_CATALOG: Dict[str, Dict[str, float]] = {
        "claude-3-5-sonnet": {
            "prompt_per_1m": 3.00,
            "completion_per_1m": 15.00,
        },
        "claude-3-haiku": {
            "prompt_per_1m": 0.25,
            "completion_per_1m": 1.25,
        },
        "gpt-4o": {
            "prompt_per_1m": 2.50,
            "completion_per_1m": 10.00,
        },
        "gpt-4o-mini": {
            "prompt_per_1m": 0.15,
            "completion_per_1m": 0.60,
        },
        "default": {
            "prompt_per_1m": 2.00,
            "completion_per_1m": 8.00,
        },
    }

    @classmethod
    def calculate_cost(
        cls,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """
        Calculates the dollar cost of an inference call given prompt and completion tokens.
        """
        rates = cls.PRICING_CATALOG.get(model_name.lower(), cls.PRICING_CATALOG["default"])
        prompt_cost = (prompt_tokens / 1_000_000.0) * rates["prompt_per_1m"]
        completion_cost = (completion_tokens / 1_000_000.0) * rates["completion_per_1m"]
        return round(prompt_cost + completion_cost, 6)

    @classmethod
    def get_rates(cls, model_name: str) -> Dict[str, float]:
        return cls.PRICING_CATALOG.get(model_name.lower(), cls.PRICING_CATALOG["default"])
