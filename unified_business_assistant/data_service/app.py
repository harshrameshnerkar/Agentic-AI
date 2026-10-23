"""
Role B: Data Service — Main Production FastAPI Application.

Provides the canonical POST /query endpoint (Interface 2) defined in UNIFIED-BUSINESS-ASSISTAN.md §4.5.
Features AST-based SQL safety validation, read-only bounded execution, self-correction,
and strict answerability gating.

Run:
    uvicorn app:app --host 127.0.0.1 --port 8002 --reload
"""
import time
import uuid
from typing import Any, Dict
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from contracts import QueryRequest, QueryResponse
from correction.self_correction import correction_engine
from db.connection import db_manager
from safety.errors import SQLSecurityException
from safety.validator import SQLSafetyValidator
from sql.generator import sql_generator
from sql.schema_context import SCHEMA_METADATA, SchemaContextBuilder

app = FastAPI(
    title="Data Service (Role B) - Production",
    version="1.0.0",
    description="Production text-to-SQL service with AST safety validation and self-correction loop",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/query", response_model=QueryResponse)
def execute_business_query(payload: QueryRequest, request: Request) -> QueryResponse:
    """
    Translates a natural language question into validated, safe SQL and executes it.
    Matches Interface 2 contract exactly.
    """
    req_id = str(uuid.uuid4())[:8]
    start_time = time.perf_counter()

    question = payload.question.strip()
    limit = payload.limit or 100

    # 1. Text-to-SQL Generation (with Semantic Answerability Check)
    generated_sql, is_answerable, gen_note = sql_generator.generate_sql(question)

    if not is_answerable or not generated_sql:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return QueryResponse(
            columns=[],
            rows=[],
            sql=None,
            answerable=False,
            error=gen_note or "Question cannot be answered from the structured database schema.",
            execution_time_ms=duration_ms,
        )

    # 2. Pre-Execution AST Safety Validation Gate
    try:
        is_valid, validated_sql, val_err = SQLSafetyValidator.validate(generated_sql)
    except SQLSecurityException as sec_err:
        # Crucial acceptance check: destructive operations blocked at validation phase
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return QueryResponse(
            columns=[],
            rows=[],
            sql=generated_sql,
            answerable=False,
            error=str(sec_err),
            execution_time_ms=duration_ms,
        )

    # 3. Read-Only Bounded Execution with Self-Correction Loop
    columns, rows, final_sql, exec_ok, exec_err, attempt_logs = (
        correction_engine.execute_with_self_correction(
            question=question,
            initial_sql=validated_sql,
            limit=limit,
            request_id=req_id,
        )
    )

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return QueryResponse(
        columns=columns,
        rows=rows,
        sql=final_sql,
        answerable=exec_ok,
        error=exec_err,
        execution_time_ms=duration_ms,
    )


@app.get("/health")
def health():
    """Health check endpoint exposing table metrics and status."""
    try:
        counts = db_manager.get_table_counts()
        return {
            "status": "healthy",
            "service": "data_service",
            "role": "Role B",
            "mode": "production",
            "database": "sqlite_readonly",
            "tables": counts,
            "total_records": sum(counts.values()),
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database unhealthy: {str(e)}")


@app.get("/schema")
def get_schema():
    """Returns database schema definition and relationship metadata."""
    return {
        "tables": SCHEMA_METADATA,
        "database_type": "SQLite 3",
        "access_mode": "read_only",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8002, reload=True)
