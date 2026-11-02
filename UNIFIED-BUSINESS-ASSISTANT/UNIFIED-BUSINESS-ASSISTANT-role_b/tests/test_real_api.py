"""
Unit and Contract Tests for Role B Real API
Provides FakeGenerator for offline contract and readiness verification.
"""

from types import SimpleNamespace
from typing import Any, List, Dict

class FakeQueryResult:
    def __init__(self, columns: List[str], rows: List[Dict[str, Any]]):
        self.columns = columns
        self.rows = rows

class FakeValidator:
    def execute(self, sql: str, require_complete: bool = False):
        return FakeQueryResult(
            columns=["customername"],
            rows=[{"customername": "Alfreds Futterkiste"}]
        )

class FakeGenerator:
    def __init__(self):
        self.validator = FakeValidator()

    def generate_sql(self, question: str, correction_feedback: str | None = None):
        return SimpleNamespace(
            sql="SELECT customername FROM customers",
            answerable=True
        )
