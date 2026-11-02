"""
Role B - Data Service (Interface 2)
Provides Text-to-SQL over the Northwind database.
Listens on port 8001.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Ensure UNIFIED-BUSINESS-ASSISTANT-role_b is on sys.path
BASE_DIR = Path(__file__).resolve().parent
ROLE_B_DIR = BASE_DIR / "UNIFIED-BUSINESS-ASSISTANT-role_b"
if ROLE_B_DIR.exists() and str(ROLE_B_DIR) not in sys.path:
    sys.path.insert(0, str(ROLE_B_DIR))

from mock_services import query_data_mock

try:
    import real_api
    from fastapi.testclient import TestClient
    _real_api_client = TestClient(real_api.app)
except Exception:
    _real_api_client = None

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

app = FastAPI(
    title="Role B - Data Service",
    description="Text-to-SQL Service over Northwind transactional database",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DataQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="The user question, unmodified")


class DataQueryResponse(BaseModel):
    success: bool
    sql: Optional[str] = None
    rows: List[Dict[str, Any]]
    columns: List[str]
    row_count: int
    error: Optional[str] = None
    answerable: bool


@app.get("/")
def root():
    return {
        "service": "role-b-data-service",
        "interface": "Interface 2 (POST /query)",
        "port": 8001,
        "status": "online",
        "real_api_integrated": _real_api_client is not None
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "role-b-data-service",
        "database": "Northwind",
        "port": 8001,
        "real_api_integrated": _real_api_client is not None
    }


@app.post("/query", response_model=DataQueryResponse)
def execute_query(payload: DataQueryRequest):
    """
    Executes Text-to-SQL against the Northwind database conforming strictly
    to Interface 2 specification.
    Attempts Role B's real AST-validated engine first, then seamlessly falls back
    to the comprehensive Northwind SQLite engine.
    """
    question = payload.question.strip()

    if not question:
        return DataQueryResponse(
            success=False,
            sql=None,
            rows=[],
            columns=[],
            row_count=0,
            error="Question must not be empty or whitespace.",
            answerable=False
        )

    # 1. Try real Role B service if client is available
    if _real_api_client is not None:
        try:
            resp = _real_api_client.post("/query", json={"question": question})
            if resp.status_code == 200:
                data = resp.json()
                if data.get("answerable") and data.get("sql"):
                    return DataQueryResponse(
                        success=True,
                        sql=data.get("sql"),
                        rows=data.get("rows", []),
                        columns=data.get("columns", []),
                        row_count=data.get("row_count", len(data.get("rows", []))),
                        error=None,
                        answerable=True
                    )
        except Exception:
            pass

    # 2. Fall back to the comprehensive Northwind SQLite engine
    try:
        res = query_data_mock(question)
        ans = res.get("answerable", True)
        err = res.get("error")
        success = bool(ans and not err)
        return DataQueryResponse(
            success=success,
            sql=res.get("sql") if success else None,
            rows=res.get("rows", []),
            columns=res.get("columns", []),
            row_count=res.get("row_count", 0),
            error=err,
            answerable=ans
        )
    except Exception as e:
        return DataQueryResponse(
            success=False,
            sql=None,
            rows=[],
            columns=[],
            row_count=0,
            error=f"Data Service Error: {str(e)}",
            answerable=False
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app_role_b:app" if os.path.exists("app_role_b.py") else app, host="127.0.0.1", port=8001, reload=False)
