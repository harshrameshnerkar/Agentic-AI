"""
Failure Taxonomy Classifier for Role B (Data Service).

Categorises SQL generation and execution failures into standard taxonomies:
1. WRONG_JOIN
2. WRONG_AGGREGATION
3. HALLUCINATED_COLUMN
4. AMBIGUOUS_QUESTION
5. OUT_OF_SCOPE_UNANSWERABLE

(UNIFIED-BUSINESS-ASSISTAN.md §4.6 Day 4, Acceptance Criterion 5).
"""
import re
from enum import Enum
from typing import Dict, List, Optional, Tuple

from sql.schema_context import SCHEMA_METADATA


class FailureCategory(str, Enum):
    WRONG_JOIN = "WRONG_JOIN"
    WRONG_AGGREGATION = "WRONG_AGGREGATION"
    HALLUCINATED_COLUMN = "HALLUCINATED_COLUMN"
    AMBIGUOUS_QUESTION = "AMBIGUOUS_QUESTION"
    OUT_OF_SCOPE_UNANSWERABLE = "OUT_OF_SCOPE_UNANSWERABLE"
    SYNTAX_ERROR = "SYNTAX_ERROR"
    TIMEOUT_RESOURCE = "TIMEOUT_RESOURCE"


class FailureTaxonomyClassifier:
    """Classifies text-to-SQL errors into formal failure categories with root cause analysis."""

    ALL_VALID_COLUMNS = {
        col_name.lower()
        for tbl, meta in SCHEMA_METADATA.items()
        for col_name, _ in meta["columns"]
    }
    ALL_VALID_TABLES = set(SCHEMA_METADATA.keys())

    @classmethod
    def classify(
        cls,
        question: str,
        sql: Optional[str],
        error_message: Optional[str],
        is_answerable: bool,
    ) -> FailureCategory:
        """
        Determines the failure category from question, SQL, and error metadata.
        """
        err_lower = (error_message or "").lower()
        sql_lower = (sql or "").lower()
        q_lower = question.lower()

        # 1. Check for unanswerable / out of scope
        if not is_answerable or "unanswerable" in err_lower or "does not exist in the structured" in err_lower:
            return FailureCategory.OUT_OF_SCOPE_UNANSWERABLE

        # 2. Check for Hallucinated Column or Table
        if "no such column" in err_lower or "no such table" in err_lower:
            return FailureCategory.HALLUCINATED_COLUMN

        # Inspect SQL tokens for unknown column references
        if sql:
            # Check for common hallucinated aliases
            hallucinated_aliases = ["client_name", "customer_revenue", "employee_name", "total_sales_amount"]
            for h in hallucinated_aliases:
                if h in sql_lower:
                    return FailureCategory.HALLUCINATED_COLUMN

        # 3. Check for Wrong Join
        if "ambiguous column name" in err_lower or "join" in err_lower and "on" not in sql_lower:
            return FailureCategory.WRONG_JOIN
        if "join" in sql_lower and ("on" not in sql_lower and "using" not in sql_lower):
            return FailureCategory.WRONG_JOIN

        # 4. Check for Wrong Aggregation
        if "group by" in err_lower or "misuse of aggregate" in err_lower:
            return FailureCategory.WRONG_AGGREGATION
        # Aggregation without GROUP BY when selecting non-aggregates
        if re.search(r"SELECT\s+[^,]+,\s*(?:SUM|AVG|COUNT|MIN|MAX)\(", sql_lower) and "group by" not in sql_lower:
            return FailureCategory.WRONG_AGGREGATION

        # 5. Check for Ambiguous Question
        ambiguous_triggers = ["best", "highest rated", "popular", "performance", "recent", "normal"]
        if any(trig in q_lower for trig in ambiguous_triggers) and "limit" not in sql_lower and "order by" not in sql_lower:
            return FailureCategory.AMBIGUOUS_QUESTION

        # 6. Syntax or Generic
        if "syntax error" in err_lower or "near" in err_lower:
            return FailureCategory.SYNTAX_ERROR

        return FailureCategory.AMBIGUOUS_QUESTION
