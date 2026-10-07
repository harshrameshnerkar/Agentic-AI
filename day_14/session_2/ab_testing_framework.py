"""
Day 14 - Session 2: Production A/B Testing & Online Evaluation Framework
========================================================================
Implements real-world production experiment tracking:
  - Splits traffic between Variant A (Baseline Agent) and Variant B (Candidate Agent)
  - Tracks live operational KPIs:
      * Mean Time to Resolution (MTTR in seconds)
      * Human Escalation / Override Rate (%)
      * Tool Execution Success Rate (%)
      * Compensating Action (Undo) Frequency (%)
  - Computes two-sample z-test for statistical significance (p-value, alpha = 0.05)
  - Generates experiment decision scorecard: PROMOTE, HOLD, or ROLLBACK
"""

import math
import random
import time
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class ABExperimentMetrics:
    variant_name: str
    total_sessions: int
    successful_resolutions: int
    human_escalations: int
    tool_failures: int
    undo_compensations: int
    mean_resolution_time_sec: float
    success_rate_pct: float
    escalation_rate_pct: float
    undo_rate_pct: float


@dataclass
class ABExperimentDecision:
    experiment_name: str
    sample_size_per_variant: int
    variant_a_metrics: ABExperimentMetrics
    variant_b_metrics: ABExperimentMetrics
    z_score: float
    p_value: float
    is_statistically_significant: bool
    recommendation: str           # "PROMOTE_VARIANT_B", "REVERT_TO_VARIANT_A", "INCONCLUSIVE_CONTINUE_TEST"
    rationale: str


class ABTestingEngine:
    """Manages randomized online A/B traffic split experiments and hypothesis testing."""

    @staticmethod
    def simulate_production_experiment(
        experiment_name: str = "Prompt_Optimization_v1_to_v2",
        sample_size: int = 500,
    ) -> ABExperimentDecision:
        """
        Simulates an online production A/B test with sample_size sessions per variant.
        Variant A = Baseline production prompt
        Variant B = Candidate optimized prompt
        """
        # Baseline simulation parameters
        a_success = int(sample_size * 0.91)
        a_escalations = int(sample_size * 0.07)
        a_failures = int(sample_size * 0.02)
        a_undos = int(sample_size * 0.015)
        a_mttr = 142.5

        # Candidate simulation parameters (improved resolution rate, reduced escalations)
        b_success = int(sample_size * 0.96)
        b_escalations = int(sample_size * 0.03)
        b_failures = int(sample_size * 0.01)
        b_undos = int(sample_size * 0.005)
        b_mttr = 98.2

        var_a = ABExperimentMetrics(
            variant_name="Variant_A_Baseline",
            total_sessions=sample_size,
            successful_resolutions=a_success,
            human_escalations=a_escalations,
            tool_failures=a_failures,
            undo_compensations=a_undos,
            mean_resolution_time_sec=a_mttr,
            success_rate_pct=round((a_success / sample_size) * 100.0, 2),
            escalation_rate_pct=round((a_escalations / sample_size) * 100.0, 2),
            undo_rate_pct=round((a_undos / sample_size) * 100.0, 2),
        )

        var_b = ABExperimentMetrics(
            variant_name="Variant_B_Candidate",
            total_sessions=sample_size,
            successful_resolutions=b_success,
            human_escalations=b_escalations,
            tool_failures=b_failures,
            undo_compensations=b_undos,
            mean_resolution_time_sec=b_mttr,
            success_rate_pct=round((b_success / sample_size) * 100.0, 2),
            escalation_rate_pct=round((b_escalations / sample_size) * 100.0, 2),
            undo_rate_pct=round((b_undos / sample_size) * 100.0, 2),
        )

        # Statistical hypothesis testing: Two-proportion Z-test
        p1 = var_a.success_rate_pct / 100.0
        p2 = var_b.success_rate_pct / 100.0
        n1 = sample_size
        n2 = sample_size

        # Pooled probability
        p_pool = (a_success + b_success) / (n1 + n2)
        se = math.sqrt(p_pool * (1.0 - p_pool) * (1.0 / n1 + 1.0 / n2))

        z_score = (p2 - p1) / max(1e-6, se)

        # Standard normal two-tailed p-value approximation
        # using error function
        p_value = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(z_score) / math.sqrt(2.0))))

        is_significant = (p_value < 0.05) and (z_score > 0)

        if is_significant and var_b.success_rate_pct > var_a.success_rate_pct:
            rec = "PROMOTE_VARIANT_B"
            rat = (
                f"Variant B demonstrates statistically significant improvement in resolution rate "
                f"({var_b.success_rate_pct}% vs {var_a.success_rate_pct}%, z={z_score:.2f}, p={p_value:.4f} < 0.05). "
                f"MTTR reduced by {a_mttr - b_mttr:.1f}s."
            )
        elif is_significant and var_b.success_rate_pct < var_a.success_rate_pct:
            rec = "REVERT_TO_VARIANT_A"
            rat = f"Variant B regressed resolution rate with statistical significance. Rollback immediately."
        else:
            rec = "INCONCLUSIVE_CONTINUE_TEST"
            rat = f"Observed difference not statistically significant (p={p_value:.4f} >= 0.05). Continue sampling."

        return ABExperimentDecision(
            experiment_name=experiment_name,
            sample_size_per_variant=sample_size,
            variant_a_metrics=var_a,
            variant_b_metrics=var_b,
            z_score=round(z_score, 3),
            p_value=round(p_value, 5),
            is_statistically_significant=is_significant,
            recommendation=rec,
            rationale=rat,
        )
