import os
import time
import uuid
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from contracts import QueryRequest, QueryResponse
from correction.self_correction import correction_engine
from db.connection import db_manager
from safety.errors import SQLSecurityException
from safety.validator import SQLSafetyValidator
from sql.generator import sql_generator
from sql.schema_context import SCHEMA_METADATA

app = FastAPI(
    title="Data Service",
    version="1.0.0",
    description="Read-only text-to-SQL service with AST validation and query self-correction.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def serve_dashboard():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {
        "service": "Data Service",
        "status": "online",
        "documentation": "/docs",
        "endpoints": ["POST /query", "GET /health", "GET /schema"],
    }


@app.post("/query", response_model=QueryResponse)
def execute_business_query(payload: QueryRequest, request: Request) -> QueryResponse:
    req_id = str(uuid.uuid4())[:8]
    start_time = time.perf_counter()

    question = payload.question.strip()
    limit = payload.limit or 100

    generated_sql, is_answerable, gen_note = sql_generator.generate_sql(question)
    if not is_answerable or not generated_sql:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return QueryResponse(
            columns=[],
            rows=[],
            sql=None,
            answerable=False,
            error=gen_note or "Question cannot be answered from the database schema.",
            execution_time_ms=duration_ms,
        )

    try:
        _, validated_sql, _ = SQLSafetyValidator.validate(generated_sql)
    except SQLSecurityException as sec_err:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return QueryResponse(
            columns=[],
            rows=[],
            sql=generated_sql,
            answerable=False,
            error=str(sec_err),
            execution_time_ms=duration_ms,
        )

    columns, rows, final_sql, exec_ok, exec_err, _ = correction_engine.execute_with_self_correction(
        question=question,
        initial_sql=validated_sql,
        limit=limit,
        request_id=req_id,
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
        raise HTTPException(status_code=503, detail=f"Database unhealthy: {e}")


@app.get("/schema")
def get_schema():
    return {
        "tables": SCHEMA_METADATA,
        "database_type": "SQLite 3",
        "access_mode": "read_only",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8002, reload=True)
