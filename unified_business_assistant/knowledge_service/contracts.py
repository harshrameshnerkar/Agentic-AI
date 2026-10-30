from typing import List, Optional
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: Optional[int] = Field(default=5, ge=1, le=20)
    score_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class PassageResult(BaseModel):
    text: str
    source_file: str
    page: int = Field(..., ge=1)
    score: float
    chunk_id: str
    title: Optional[str] = None
    company: Optional[str] = None


class SearchResponse(BaseModel):
    results: List[PassageResult]
    no_match: bool
    embedding_model: Optional[str] = None
