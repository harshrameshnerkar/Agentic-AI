"""Retrospective Analyzer for Day 20 Session 3.

Calculates Sprint Board variance, catalogs specific technical mistakes,
and tracks action items for continuous engineering improvement.
"""

from dataclasses import dataclass
import json
import os
from typing import Any, Dict, List, Tuple


@dataclass
class VarianceSummary:
    total_estimated_hours: float
    total_actual_hours: float
    net_variance_hours: float
    tasks_analyzed: int
    mistakes_cataloged: int
    action_items_count: int


class SprintRetrospectiveManager:
    """Analyzes sprint estimation accuracy and technical takeaways."""

    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = base_dir
        self.data_path = os.path.join(base_dir, "RETROSPECTIVE_DATA.json")

    def load_retro_data(self) -> Dict[str, Any]:
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Retrospective data missing at: {self.data_path}")
        with open(self.data_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def calculate_variance_summary(self) -> VarianceSummary:
        data = self.load_retro_data()
        tasks = data.get("sprint_variance", [])
        mistakes = data.get("three_specific_mistakes", [])
        actions = data.get("action_items_next_sprint", [])

        total_est = sum(t.get("estimated_hours", 0.0) for t in tasks)
        total_act = sum(t.get("actual_hours", 0.0) for t in tasks)
        net_var = round(total_act - total_est, 2)

        return VarianceSummary(
            total_estimated_hours=round(total_est, 2),
            total_actual_hours=round(total_act, 2),
            net_variance_hours=net_var,
            tasks_analyzed=len(tasks),
            mistakes_cataloged=len(mistakes),
            action_items_count=len(actions),
        )

    def get_mistakes(self) -> List[Dict[str, Any]]:
        return self.load_retro_data().get("three_specific_mistakes", [])
