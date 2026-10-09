"""Conversion Evaluator for Day 20 Session 4.

Computes multi-week rubric scores, evaluates system-design defense metrics,
and validates final full-time conversion recommendation.
"""

from dataclasses import dataclass
import json
import os
from typing import Any, Dict, List, Tuple


@dataclass
class ConversionSummary:
    candidate_name: str
    target_role: str
    composite_score: float
    max_score: float
    verdict: str
    weeks_evaluated: int
    unanimous_strong_hire: bool
    panel_count: int


class ConversionReviewManager:
    """Calculates and verifies internship conversion evaluation metrics."""

    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = base_dir
        self.eval_file = os.path.join(base_dir, "CONVERSION_EVALUATION.json")

    def load_evaluation_data(self) -> Dict[str, Any]:
        if not os.path.exists(self.eval_file):
            raise FileNotFoundError(f"Conversion evaluation file missing at: {self.eval_file}")
        with open(self.eval_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def evaluate_conversion(self) -> ConversionSummary:
        data = self.load_evaluation_data()
        cand = data.get("candidate", {})
        panel = data.get("review_panel", [])
        rubric = data.get("competency_rubric", [])

        # Calculate average rubric score
        total_score = sum(w.get("score", 0.0) for w in rubric)
        avg_score = round(total_score / len(rubric), 2) if rubric else 0.0

        # Check unanimous recommendation
        unanimous = all(p.get("recommendation") == "STRONG_HIRE" for p in panel) and len(panel) >= 3

        decision = data.get("final_decision", {})
        verdict = decision.get("verdict", "PENDING")

        return ConversionSummary(
            candidate_name=cand.get("name", "Unknown"),
            target_role=cand.get("target_conversion_role", "Unknown"),
            composite_score=avg_score,
            max_score=5.0,
            verdict=verdict,
            weeks_evaluated=len(rubric),
            unanimous_strong_hire=unanimous,
            panel_count=len(panel),
        )
