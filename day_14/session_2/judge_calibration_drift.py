"""
Day 14 - Session 2: Judge Calibration Drift Detector
=====================================================
Monitors LLM-as-a-Judge score stability across time:
  - Tracks score distribution shifts against a Frozen Calibration Benchmark
  - Detects 'Leniency Drift' (judge becoming excessively forgiving)
  - Detects 'Harshness Drift' (judge unfairly penalizing harmless variations)
  - Provides mathematical z-score calibration re-centering
"""

import math
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class JudgeCalibrationReport:
    judge_name: str
    evaluation_cycle: str
    sample_count: int
    baseline_mean_score: float
    current_mean_score: float
    score_delta: float
    baseline_std_dev: float
    current_std_dev: float
    drift_status: str               # "STABLE", "LENIENCY_DRIFT", "HARSHNESS_DRIFT"
    recalibration_factor: float
    requires_recalibration: bool
    diagnostic_details: str


class JudgeCalibrationDriftDetector:
    """Detects and compensates for statistical distribution shifts in automated LLM evaluators."""

    DRIFT_TOLERANCE_THRESHOLD: float = 0.05  # +/- 5% change in mean score indicates drift

    @classmethod
    def analyze_drift(
        cls,
        baseline_scores: List[float],
        current_scores: List[float],
        judge_name: str = "LLM_Judge_Claude_3.5_Sonnet",
        cycle_name: str = "Sprint_42_Eval_Run",
    ) -> JudgeCalibrationReport:
        """
        Analyzes statistical distribution drift between baseline and current evaluation runs.
        """
        if not baseline_scores or not current_scores:
            raise ValueError("Scores lists cannot be empty.")

        n_base = len(baseline_scores)
        n_curr = len(current_scores)

        # 1. Means
        mu_base = sum(baseline_scores) / n_base
        mu_curr = sum(current_scores) / n_curr
        delta = mu_curr - mu_base

        # 2. Standard Deviations
        var_base = sum((x - mu_base) ** 2 for x in baseline_scores) / max(1, n_base - 1)
        var_curr = sum((x - mu_curr) ** 2 for x in current_scores) / max(1, n_curr - 1)
        std_base = math.sqrt(var_base)
        std_curr = math.sqrt(var_curr)

        # 3. Classify Drift
        if delta > cls.DRIFT_TOLERANCE_THRESHOLD:
            status = "LENIENCY_DRIFT"
            diag = (
                f"Judge is scoring {delta:+.3f} higher on average than baseline. "
                f"Risk: False sense of improvement masking regressions."
            )
            recal = round(mu_base / max(0.001, mu_curr), 4)
            req_recal = True
        elif delta < (-cls.DRIFT_TOLERANCE_THRESHOLD):
            status = "HARSHNESS_DRIFT"
            diag = (
                f"Judge is scoring {abs(delta):.3f} lower on average than baseline. "
                f"Risk: False positive CI failures blocking valid pull requests."
            )
            recal = round(mu_base / max(0.001, mu_curr), 4)
            req_recal = True
        else:
            status = "STABLE"
            diag = f"Score distribution within acceptable tolerance ({delta:+.3f}). Judge is calibrated."
            recal = 1.0
            req_recal = False

        return JudgeCalibrationReport(
            judge_name=judge_name,
            evaluation_cycle=cycle_name,
            sample_count=n_curr,
            baseline_mean_score=round(mu_base, 4),
            current_mean_score=round(mu_curr, 4),
            score_delta=round(delta, 4),
            baseline_std_dev=round(std_base, 4),
            current_std_dev=round(std_curr, 4),
            drift_status=status,
            recalibration_factor=recal,
            requires_recalibration=req_recal,
            diagnostic_details=diag,
        )

    @classmethod
    def apply_recalibration(cls, uncalibrated_scores: List[float], recalibration_factor: float) -> List[float]:
        """Applies mathematical scaling factor to normalize uncalibrated judge scores."""
        return [round(min(1.0, max(0.0, s * recalibration_factor)), 4) for s in uncalibrated_scores]
