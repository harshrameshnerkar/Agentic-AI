from typing import Any, List, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    limit: Optional[int] = Field(default=100, ge=1, le=1000)


class QueryResponse(BaseModel):
    columns: List[str] = Field(default_factory=list)
    rows: List[List[Any]] = Field(default_factory=list)
    sql: Optional[str] = Field(default=None)
    answerable: bool
    error: Optional[str] = Field(default=None)
    execution_time_ms: Optional[float] = Field(default=None)
