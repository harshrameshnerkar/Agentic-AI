"""Report Generator & SLA Verifier for Day 20 Session 2.

Validates benchmark results against Day 16 Charter criteria and outputs
structured results and limitations analysis.
"""

from dataclasses import dataclass
import json
import os
from typing import Any, Dict, List, Tuple


@dataclass
class SLAVerificationResult:
    all_slas_met: bool
    pass_rate_ok: bool
    latency_ok: bool
    cost_ok: bool
    regressions_ok: bool
    total_golden_cases: int
    stratified_categories: int
    limitations_count: int


class ResultsReportManager:
    """Manages results analysis and charter verification."""

    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = base_dir
        self.metrics_path = os.path.join(base_dir, "RESULTS_METRICS.json")
        self.report_path = os.path.join(base_dir, "RESULTS_AND_LIMITATIONS_REPORT.md")

    def load_metrics(self) -> Dict[str, Any]:
        if not os.path.exists(self.metrics_path):
            raise FileNotFoundError(f"Metrics file missing: {self.metrics_path}")
        with open(self.metrics_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def verify_charter_slas(self) -> SLAVerificationResult:
        metrics = self.load_metrics()
        charter = metrics.get("charter_comparison", {})

        pr = charter.get("pass_rate", {})
        pass_rate_ok = pr.get("measured_value", 0.0) >= pr.get("target_sla", 95.0)

        lat = charter.get("p95_latency", {})
        latency_ok = lat.get("measured_value", 999999.0) <= lat.get("target_sla", 90000.0)

        cost = charter.get("cost_per_query", {})
        cost_ok = cost.get("measured_value", 999.0) <= cost.get("target_sla", 0.150)

        regs = charter.get("critical_regressions", {})
        regressions_ok = regs.get("measured_value", 999) <= regs.get("target_sla", 0)

        stratified = metrics.get("stratified_pass_rate", [])
        total_cases = sum(c.get("total_cases", 0) for c in stratified)
        limitations = metrics.get("honest_limitations", [])

        all_ok = pass_rate_ok and latency_ok and cost_ok and regressions_ok

        return SLAVerificationResult(
            all_slas_met=all_ok,
            pass_rate_ok=pass_rate_ok,
            latency_ok=latency_ok,
            cost_ok=cost_ok,
            regressions_ok=regressions_ok,
            total_golden_cases=total_cases,
            stratified_categories=len(stratified),
            limitations_count=len(limitations),
        )
