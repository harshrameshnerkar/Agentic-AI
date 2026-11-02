"""Real Role B API. main.py is the deterministic mock API."""

from __future__ import annotations

import logging
import os
import re
import uuid
from threading import Lock
from typing import Any, Callable

from fastapi import FastAPI
from pydantic import BaseModel, Field

logger = logging.getLogger("role_b.data_service")

MAX_SQL_ATTEMPTS = 3  # Initial attempt plus at most two corrections.
FAILURE_COUNTS: dict[str, int] = {}
_failure_counts_lock = Lock()


def _record_failure(category: str) -> int:
    """Count process-local failures without retaining query contents."""
    with _failure_counts_lock:
        FAILURE_COUNTS[category] = FAILURE_COUNTS.get(category, 0) + 1
        return FAILURE_COUNTS[category]


def _requires_complete_result(question: str) -> bool:
    """Identify requests for all records unless an explicit count bound exists."""
    text = question.lower()

    # Explicit result-count bounds take precedence over completeness wording.
    bounded_patterns = (
        r"\b(?:limit|top|first|only)\s+\d+\b",
        r"\blimited\s+to\s+\d+\b",
        r"\bup\s+to\s+\d+\b",
        r"\bat\s+most\s+\d+\b",
        r"\bno\s+more\s+than\s+\d+\b",
    )
    if any(re.search(pattern, text) for pattern in bounded_patterns):
        return False

    return bool(
        re.search(r"\b(?:all|every|each|full|entire|whole)\b", text)
        or re.search(r"\b(?:complete|all\s+rows|all\s+records|all\s+details|full\s+table|entire\s+table|all\s+the)\b", text)
    )


def classify_failure(question: str, error: str) -> str:
    """Classify a failure without logging the question or SQL."""
    text = str(error).lower()

    if any(
        token in text
        for token in (
            "ambiguous column",
            "ambiguous reference",
            "ambiguous question",
            "unclear which",
        )
    ):
        return "ambiguous_question"

    if any(
        token in text
        for token in (
            "group by",
            "aggregate",
            "aggregation",
            "must appear in the group",
        )
    ):
        return "incorrect_aggregation"

    if any(
        token in text
        for token in (
            "join",
            "foreign key",
            "relation does not exist",
            "missing from-clause",
        )
    ):
        return "wrong_join"

    if any(
        token in text
        for token in (
            "does not exist",
            "undefined column",
            "unknown column",
            "column not found",
        )
    ):
        return "hallucinated_column"

    if any(
        token in text
        for token in (
            "outside the approved schema",
            "cannot be answered",
            "unanswerable",
        )
    ):
        return "unanswerable_or_schema_mismatch"

    if any(
        token in text
        for token in (
            "syntax",
            "unsafe sql",
            "select queries are permitted",
        )
    ):
        return "validation_error"

    if any(
        token in text
        for token in ("generation", "groq", "provider")
    ):
        return "generation_error"

    return "execution_error"


def _safe_feedback(exc: Exception) -> str:
    """Return bounded diagnostic text suitable for SQL correction."""
    diag = getattr(exc, "diag", None)
    message = (
        getattr(diag, "message_primary", None)
        or str(exc)
        or type(exc).__name__
    )

    message = re.sub(
        r"(?:postgres(?:ql)?|https?)://[^\s]+",
        "[REDACTED_URL]",
        message,
        flags=re.IGNORECASE,
    )
    message = re.sub(r"'[^']{1,200}'", "'[REDACTED]'", message)

    return message[:500]


class QueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        description="Natural-language business question",
    )


class QueryResponse(BaseModel):
    """Shared response contract used by the mock and real APIs."""

    success: bool
    sql: str
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int
    error: str | None
    answerable: bool


def _failure(error: str) -> QueryResponse:
    """Return a consistent failure response without result data."""
    return QueryResponse(
        success=False,
        sql="",
        columns=[],
        rows=[],
        row_count=0,
        error=error,
        answerable=False,
    )


def create_app(
    generator_factory: Callable[[], Any] | None = None,
) -> FastAPI:
    """Create the real API, optionally injecting an offline test generator."""
    api = FastAPI(
        title="Role B - Data Service",
        description=(
            "Groq-powered, PostgreSQL-validated, read-only Neon query API"
        ),
        version="1.3.0",
    )

    def make_generator() -> Any:
        if generator_factory is not None:
            return generator_factory()

        # Lazy construction allows health checks without requiring live
        # database or model-provider configuration.
        from src.generator.postgres_sql_generator import (
            PostgresGroqSQLGenerator,
        )

        return PostgresGroqSQLGenerator()

    @api.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": "role-b-data-service",
        }

    @api.post("/query", response_model=QueryResponse)
    def query(request: QueryRequest) -> QueryResponse:
        question = request.question.strip()

        if not question:
            return _failure(
                "Question must not be empty or whitespace."
            )

        query_id = uuid.uuid4().hex[:12]

        try:
            generator = make_generator()
        except Exception as exc:
            category = classify_failure(
                question,
                _safe_feedback(exc),
            )
            category_count = _record_failure(category)

            logger.warning(
                "query_failed query_id=%s attempt=0 "
                "category=%s category_count=%s",
                query_id,
                category,
                category_count,
            )

            return _failure(
                "SQL service is not configured or could not start."
            )

        feedback: str | None = None
        last_category = "generation_error"

        for attempt in range(1, MAX_SQL_ATTEMPTS + 1):
            try:
                generated = generator.generate_sql(
                    question,
                    correction_feedback=feedback,
                )

                if not getattr(generated, "answerable", True):
                    logger.info(
                        "query_unanswerable query_id=%s attempt=%s",
                        query_id,
                        attempt,
                    )
                    return _failure(
                        "The database schema cannot answer this question."
                    )

                sql = generated.sql

                # The generator's validator remains responsible for
                # validating SQL before opening/executing a connection.
                result = generator.validator.execute(
                    sql,
                    require_complete=_requires_complete_result(question),
                )

                columns = list(result.columns)

                # Preserve dictionary-shaped rows to match the API contract.
                rows = [
                    {column: row[column] for column in columns}
                    for row in result.rows
                ]

                logger.info(
                    "query_succeeded query_id=%s attempt=%s "
                    "corrected=%s row_count=%s",
                    query_id,
                    attempt,
                    attempt > 1,
                    len(rows),
                )

                return QueryResponse(
                    success=True,
                    sql=sql,
                    columns=columns,
                    rows=rows,
                    row_count=len(rows),
                    error=None,
                    answerable=True,
                )

            except Exception as exc:
                diagnostic = getattr(exc, "diagnostic", None)

                if diagnostic:
                    diagnostic = str(diagnostic)
                else:
                    diagnostic = _safe_feedback(exc)

                diagnostic = re.sub(
                    r"(?:postgres(?:ql)?|https?)://[^\s]+",
                    "[REDACTED_URL]",
                    diagnostic,
                    flags=re.IGNORECASE,
                )
                diagnostic = re.sub(
                    r"'[^']{1,200}'",
                    "'[REDACTED]'",
                    diagnostic,
                )
                diagnostic = diagnostic[:500]

                feedback = (
                    f"Diagnostic: {diagnostic}\n"
                    "Please regenerate a safe PostgreSQL query."
                )

                last_category = classify_failure(
                    question,
                    diagnostic,
                )
                category_count = _record_failure(last_category)

                if attempt < MAX_SQL_ATTEMPTS:
                    logger.warning(
                        "sql_correction query_id=%s attempt=%s "
                        "category=%s category_count=%s",
                        query_id,
                        attempt,
                        last_category,
                        category_count,
                    )
                else:
                    logger.error(
                        "query_failed query_id=%s attempts=%s "
                        "category=%s category_count=%s",
                        query_id,
                        attempt,
                        last_category,
                        category_count,
                    )

        failure_message = (
            f"A safe answer could not be produced after "
            f"{MAX_SQL_ATTEMPTS} attempts."
        )
        if os.environ.get("ROLE_B_DEBUG_ERRORS", "").lower() in {"1", "true", "yes"} and feedback:
            failure_message = f"{failure_message} {feedback[:700]}"
        return _failure(failure_message)

    return api


app = create_app()
