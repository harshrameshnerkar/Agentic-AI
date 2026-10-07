"""
Day 14 - Session 2: Inter-Rater Agreement Calculator
=====================================================
Calculates statistical agreement metrics between human evaluators and LLM judges:
  1. Observed Proportion of Agreement (P_o)
  2. Expected Proportion of Agreement by Chance (P_e)
  3. Cohen's Kappa Coefficient (kappa = (P_o - P_e) / (1 - P_e))
  4. Confusion matrix and qualitative strength interpretation:
     - kappa >= 0.81 : Near-Perfect Agreement
     - 0.61 - 0.80   : Substantial Agreement
     - 0.41 - 0.60   : Moderate Agreement
     - < 0.40        : Poor / Unreliable Agreement
"""

from typing import List, Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class KappaAnalysisResult:
    rater_1_name: str
    rater_2_name: str
    total_samples: int
    observed_agreement_pct: float
    expected_agreement_chance_pct: float
    cohens_kappa: float
    strength_interpretation: str
    confusion_matrix: Dict[str, Dict[str, int]]


class InterRaterAgreementEngine:
    """Computes inter-rater reliability metrics across evaluation labels."""

    LABELS = ["PASS", "FAIL", "PARTIAL"]

    @classmethod
    def calculate_cohens_kappa(
        cls,
        rater_1_ratings: List[str],
        rater_2_ratings: List[str],
        rater_1_name: str = "Human_Staff_SRE",
        rater_2_name: str = "LLM_Judge_Claude",
    ) -> KappaAnalysisResult:
        """
        Computes Cohen's Kappa coefficient between two rating vectors.
        Both vectors must have equal length.
        """
        if len(rater_1_ratings) != len(rater_2_ratings):
            raise ValueError(f"Rating length mismatch: {len(rater_1_ratings)} vs {len(rater_2_ratings)}")

        total = len(rater_1_ratings)
        if total == 0:
            raise ValueError("Cannot calculate Kappa on empty rating list.")

        # 1. Build Confusion Matrix
        matrix: Dict[str, Dict[str, int]] = {l1: {l2: 0 for l2 in cls.LABELS} for l1 in cls.LABELS}
        agreements = 0

        for r1, r2 in zip(rater_1_ratings, rater_2_ratings):
            label1 = r1.upper()
            label2 = r2.upper()
            if label1 not in cls.LABELS:
                label1 = "FAIL"
            if label2 not in cls.LABELS:
                label2 = "FAIL"

            matrix[label1][label2] += 1
            if label1 == label2:
                agreements += 1

        # 2. Observed Agreement (P_o)
        p_o = agreements / total

        # 3. Expected Agreement by Chance (P_e)
        p_e = 0.0
        for label in cls.LABELS:
            # Row marginal (rater 1 frequency for label)
            row_sum = sum(matrix[label][l2] for l2 in cls.LABELS)
            p_r1 = row_sum / total

            # Column marginal (rater 2 frequency for label)
            col_sum = sum(matrix[l1][label] for l1 in cls.LABELS)
            p_r2 = col_sum / total

            p_e += (p_r1 * p_r2)

        # 4. Cohen's Kappa calculation
        if p_e >= 1.0:
            kappa = 1.0
        else:
            kappa = (p_o - p_e) / (1.0 - p_e)

        # 5. Qualitative Strength Interpretation
        if kappa >= 0.81:
            strength = "Near-Perfect Agreement (Gold Standard Benchmark)"
        elif kappa >= 0.61:
            strength = "Substantial Agreement (Valid for Production CI Gates)"
        elif kappa >= 0.41:
            strength = "Moderate Agreement (Evaluation Rubric Needs Refinement)"
        else:
            strength = "Poor Agreement (Judge Unreliable / Noisy Rubric)"

        return KappaAnalysisResult(
            rater_1_name=rater_1_name,
            rater_2_name=rater_2_name,
            total_samples=total,
            observed_agreement_pct=round(p_o * 100.0, 2),
            expected_agreement_chance_pct=round(p_e * 100.0, 2),
            cohens_kappa=round(kappa, 4),
            strength_interpretation=strength,
            confusion_matrix=matrix,
        )
