"""Lightweight checks that generated ranking SQL follows explicit user intent."""

import re
import sqlglot
from sqlglot import exp

_NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}
_LOW_WORDS = re.compile(r"\b(lowest|cheapest|least expensive|bottom|ascending)\b", re.I)
_HIGH_WORDS = re.compile(r"\b(highest|most expensive|top|descending)\b", re.I)
_NUMBER = r"(\d+|one|two|three|four|five|six|seven|eight|nine|ten)"
_ENTITY = r"(?:products?|items?|records?|rows?|customers?|orders?|suppliers?|employees?)"


def _number(value: str) -> int:
    value = value.lower()
    return int(value) if value.isdigit() else _NUMBER_WORDS[value]


def validate_question_alignment(question: str, sql: str) -> None:
    """Reject explicit ranking/count mismatches; leave other intents to SQL generation."""
    text = question.lower()
    direction = None
    low_match = _LOW_WORDS.search(text)
    high_match = _HIGH_WORDS.search(text)
    if low_match and not high_match:
        direction = "ASC"
    elif high_match and not low_match:
        direction = "DESC"

    try:
        tree = sqlglot.parse_one(sql, read="postgres")
    except Exception as exc:
        raise ValueError("Could not check generated SQL against the requested ranking.") from exc

    if direction:
        order = tree.args.get("order")
        ordered = order.expressions[0] if order and order.expressions else None
        if ordered is None:
            raise ValueError(f"The question requests {direction} ranking, but the SQL has no ORDER BY.")
        actual = "DESC" if bool(ordered.args.get("desc")) else "ASC"
        if actual != direction:
            raise ValueError(f"The question requests {direction} ranking, but SQL uses {actual}.")

    count_match = re.search(rf"\b{_NUMBER}\s+{_ENTITY}\b", text)
    if count_match:
        requested = _number(count_match.group(1))
        limit = tree.args.get("limit")
        limit_expr = limit.expression if limit else None
        if not isinstance(limit_expr, exp.Literal) or limit_expr.is_string:
            raise ValueError(f"The question requests {requested} rows, but SQL has no matching numeric LIMIT.")
        try:
            actual_limit = int(limit_expr.this)
        except (TypeError, ValueError) as exc:
            raise ValueError("Could not verify the requested row count against SQL LIMIT.") from exc
        if actual_limit != requested:
            raise ValueError(f"The question requests {requested} rows, but SQL LIMIT is {actual_limit}.")
