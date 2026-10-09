"""Handover Pack Validator for Day 19 Session 3.

Validates that all handover documentation, checklist items, architecture diagrams,
runbook SOPs, and cost model economics meet enterprise standards.
"""

from dataclasses import dataclass
import json
import os
from typing import Any, Dict, List, Tuple


@dataclass
class ValidationReport:
    is_valid: bool
    total_checklist_items: int
    verified_items: int
    missing_sections: List[str]
    cost_pilot_usd: float
    cost_enterprise_usd: float


class HandoverPackValidator:
    """Validates the completeness and integrity of the Handover Pack."""

    REQUIRED_SECTIONS = [
        "1. Clean-Clone Quickstart Guide",
        "2. End-to-End System Architecture",
        "3. Prompts, Schemas & Configuration Catalog",
        "4. Evaluation & Regression Testing Guide",
        "5. Operational SRE Runbook & On-Call SOPs",
        "6. Enterprise Cost Model & Token Unit Economics",
        "7. Future Roadmap & Next Steps",
        "8. Recorded Walkthrough & Handover Sign-Off",
    ]

    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = base_dir
        self.doc_path = os.path.join(base_dir, "HANDOVER_PACK.md")
        self.json_path = os.path.join(base_dir, "HANDOVER_CHECKLIST.json")

    def validate_checklist_json(self) -> Tuple[bool, int, int]:
        if not os.path.exists(self.json_path):
            return False, 0, 0
        with open(self.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data.get("checklist_items", [])
        verified = sum(1 for it in items if it.get("verified", False))
        return (verified == len(items) and len(items) >= 8), len(items), verified

    def validate_markdown_sections(self) -> Tuple[bool, List[str]]:
        if not os.path.exists(self.doc_path):
            return False, self.REQUIRED_SECTIONS
        with open(self.doc_path, "r", encoding="utf-8") as f:
            content = f.read()

        missing = []
        for sec in self.REQUIRED_SECTIONS:
            # Check for header anchor or title
            title_part = sec.split(". ", 1)[-1]
            if title_part.lower() not in content.lower():
                missing.append(sec)
        return (len(missing) == 0), missing

    @staticmethod
    def calculate_cost_model(query_count: int, cost_per_query: float = 0.0028, base_infra: float = 15.0) -> float:
        """Calculates total monthly cost in USD."""
        return (query_count * cost_per_query) + base_infra

    def run_full_validation(self) -> ValidationReport:
        json_ok, total_items, verified_items = self.validate_checklist_json()
        doc_ok, missing_sections = self.validate_markdown_sections()

        cost_pilot = self.calculate_cost_model(1000, 0.0028, 15.0)
        cost_enterprise = self.calculate_cost_model(100000, 0.0028, 220.0)

        is_valid = json_ok and doc_ok and (len(missing_sections) == 0)

        return ValidationReport(
            is_valid=is_valid,
            total_checklist_items=total_items,
            verified_items=verified_items,
            missing_sections=missing_sections,
            cost_pilot_usd=cost_pilot,
            cost_enterprise_usd=cost_enterprise,
        )
