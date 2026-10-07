"""
Day 14 - Session 2: Stratified Golden Evaluation Dataset (100 Cases)
=====================================================================
Defines the schema and data models for an enterprise evaluation suite
mined from production traces and stratified across 5 critical query types:
  1. INFRA_DIAGNOSTIC       (25 cases) - CPU throttle, memory leaks, disk fill, pod crashes
  2. DESTRUCTIVE_REMEDIATION (25 cases) - Restarts, rollbacks, node drains, table drops
  3. DATABASE_STORAGE       (20 cases) - Connection pool exhaustion, WAL corruptions, replication lag
  4. NETWORK_INGRESS        (15 cases) - 502/504 gateway errors, DNS failures, TLS expiration
  5. SECURITY_ADVERSARIAL   (15 cases) - Prompt injections, brute-force surges, privilege escalations
"""

import os
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class StratifiedTestCase:
    case_id: str
    stratum: str                         # "INFRA_DIAGNOSTIC", "DESTRUCTIVE_REMEDIATION", "DATABASE_STORAGE", "NETWORK_INGRESS", "SECURITY_ADVERSARIAL"
    incident_query: str
    ground_truth_tool: str
    is_destructive: bool
    mandatory_approval: bool
    expected_root_cause_tags: List[str]
    production_frequency_weight: float   # Real-world traffic weighting (0.01 - 1.0)
    source_trace_id: str


class StratifiedDatasetRegistry:
    """Manages the 100-case stratified golden evaluation dataset."""

    @staticmethod
    def get_strata_breakdown(cases: List[StratifiedTestCase]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for c in cases:
            counts[c.stratum] = counts.get(c.stratum, 0) + 1
        return counts

    @staticmethod
    def export_json(cases: List[StratifiedTestCase], filepath: str) -> None:
        raw = [asdict(c) for c in cases]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(raw, f, indent=2)

    @staticmethod
    def load_json(filepath: str) -> List[StratifiedTestCase]:
        with open(filepath, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return [StratifiedTestCase(**item) for item in raw]
