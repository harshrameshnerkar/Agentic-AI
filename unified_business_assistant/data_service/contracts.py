"""
Shared API contract for the Role B Data Service (UNIFIED-BUSINESS-ASSISTAN.md §4.5).

Both the Day 1 mock (mock_query_service.py) and the real service (app.py) import
these models, ensuring strict schema parity with zero drift for Role C (orchestrator).

Contract Specifications:
------------------------
Endpoint: POST /query

Fields:
- `columns`: list of column header strings in execution order.
- `rows`: list of rows, where each row is an array of scalar values corresponding to `columns`.
- `sql`: the exact generated and validated SQL string executed (or attempted).
         Role C requires this for user transparency and auditability.
- `answerable`: boolean flag. True if the query can be and was answered from the database.
                False if the question asks for data not in the schema, is ambiguous,
                or out of domain (avoids hallucinated data).
- `error`: optional string containing a user-safe error message if query failed or was blocked.
- `execution_time_ms`: optional timing metric in milliseconds for observability.
"""
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Payload for POST /query."""
    question: str = Field(
        ...,
        min_length=1,
        description="Natural-language structured data question (e.g. 'What are the top 5 customers by revenue?')",
    )
    limit: Optional[int] = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of rows to return (default: 100)",
    )


class QueryResponse(BaseModel):
    """Contract response for POST /query."""
    columns: List[str] = Field(
        default_factory=list,
        description="Ordered list of column names for the returned dataset",
    )
    rows: List[List[Any]] = Field(
        default_factory=list,
        description="2D array of row records corresponding to the column names",
    )
    sql: Optional[str] = Field(
        default=None,
        description="The validated SQL query generated and executed against the database",
    )
    answerable: bool = Field(
        ...,
        description="True if the question is answerable from the schema and answered; False if out-of-scope/unanswerable",
    )
    error: Optional[str] = Field(
        default=None,
        description="Sanitized error description if query execution or validation failed",
    )
    execution_time_ms: Optional[float] = Field(
        default=None,
        description="Query pipeline execution duration in milliseconds",
    )
