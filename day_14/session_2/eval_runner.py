"""
Day 14 - Session 2: Stratified Evaluation Runner (100 Cases)
============================================================
Executes batch evaluation over the 100-case production-mined golden benchmark
and computes per-stratum scorecards:
  - INFRA_DIAGNOSTIC       (25 cases)
  - DESTRUCTIVE_REMEDIATION (25 cases)
  - DATABASE_STORAGE       (20 cases)
  - NETWORK_INGRESS        (15 cases)
  - SECURITY_ADVERSARIAL   (15 cases)
"""

import time
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass

try:
    from day_14.session_2.stratified_dataset import StratifiedTestCase
    from day_14.session_2.trace_miner import mine_100_stratified_cases
except ImportError:
    from stratified_dataset import StratifiedTestCase
    from trace_miner import mine_100_stratified_cases


@dataclass
class StratumScorecard:
    stratum_name: str
    total_cases: int
    passed_cases: int
    pass_rate_pct: float
    safety_score_pct: float
    mean_latency_ms: float


@dataclass
class Overall100Scorecard:
    prompt_version: str
    total_cases: int
    passed_cases: int
    overall_pass_rate_pct: float
    overall_safety_score_pct: float
    mean_latency_ms: float
    strata_scorecards: Dict[str, StratumScorecard]


class StratifiedEvaluationRunner:
    """Executes evaluation across all 100 stratified test cases."""

    def __init__(self, cases: Optional[List[StratifiedTestCase]] = None):
        self.cases = cases or mine_100_stratified_cases()

    def run_stratified_eval(self, prompt_version: str = "v1.0.0") -> Overall100Scorecard:
        """
        Simulates evaluation for the given prompt version across all 100 cases.
        v1.0.0 achieves 100% pass across all strata.
        v1.1.0-regressed fails destructive & schema gates.
        """
        results_by_stratum: Dict[str, List[Dict[str, Any]]] = {}

        for tc in self.cases:
            if tc.stratum not in results_by_stratum:
                results_by_stratum[tc.stratum] = []

            # Simulate evaluation result based on prompt version
            if prompt_version == "v1.0.0":
                # High-rigor baseline: passes schema, tool, and safety approval gates
                passed = True
                safe = True
                lat = 78.0 + (hash(tc.case_id) % 25)
            else:
                # Regressed candidate prompt:
                # Passes non-destructive read tools (50%), but fails destructive approval & schema
                if tc.is_destructive:
                    passed = False
                    safe = False  # Critical safety breach!
                elif tc.stratum == "SECURITY_ADVERSARIAL" and "injection" in tc.incident_query.lower():
                    passed = False
                    safe = True
                else:
                    passed = True
                    safe = True
                lat = 42.0 + (hash(tc.case_id) % 15)

            results_by_stratum[tc.stratum].append({
                "case_id": tc.case_id,
                "passed": passed,
                "safe": safe,
                "latency_ms": lat,
                "is_destructive": tc.is_destructive,
            })

        strata_cards: Dict[str, StratumScorecard] = {}
        total_all = len(self.cases)
        passed_all = 0
        safe_all = 0
        destructive_total_all = 0
        all_lats = []

        for stratum_name, res_list in results_by_stratum.items():
            tot = len(res_list)
            p_cnt = sum(1 for r in res_list if r["passed"])
            passed_all += p_cnt

            destruct_list = [r for r in res_list if r["is_destructive"]]
            if destruct_list:
                s_cnt = sum(1 for r in destruct_list if r["safe"])
                dest_tot = len(destruct_list)
                safety_pct = round((s_cnt / dest_tot) * 100.0, 2)
                destructive_total_all += dest_tot
                safe_all += s_cnt
            else:
                safety_pct = 100.0

            lats = [r["latency_ms"] for r in res_list]
            all_lats.extend(lats)
            m_lat = round(sum(lats) / len(lats), 2)

            strata_cards[stratum_name] = StratumScorecard(
                stratum_name=stratum_name,
                total_cases=tot,
                passed_cases=p_cnt,
                pass_rate_pct=round((p_cnt / tot) * 100.0, 2),
                safety_score_pct=safety_pct,
                mean_latency_ms=m_lat,
            )

        overall_pass = round((passed_all / total_all) * 100.0, 2)
        overall_safe = round((safe_all / max(1, destructive_total_all)) * 100.0, 2)
        overall_mean_lat = round(sum(all_lats) / max(1, len(all_lats)), 2)

        return Overall100Scorecard(
            prompt_version=prompt_version,
            total_cases=total_all,
            passed_cases=passed_all,
            overall_pass_rate_pct=overall_pass,
            overall_safety_score_pct=overall_safe,
            mean_latency_ms=overall_mean_lat,
            strata_scorecards=strata_cards,
        )
