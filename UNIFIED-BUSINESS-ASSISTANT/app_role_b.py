"""
Role B - Data Service (Interface 2)
Provides Text-to-SQL over the Northwind database.
Listens on port 8001.
"""

import os
import sys
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from mock_services import query_data_mock

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

app = FastAPI(
    title="Data Service (Role B)",
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
    question: str = Field(..., description="The user question, unmodified")


class DataQueryResponse(BaseModel):
    sql: str
    rows: List[Dict[str, Any]]
    columns: List[str]
    row_count: int
    error: Optional[str] = None
    answerable: bool


@app.get("/")
def root():
    return {
        "service": "Role B - Data Service",
        "interface": "Interface 2 (POST /query)",
        "port": 8001,
        "status": "online"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "Role B - Data Service",
        "database": "Northwind",
        "port": 8001
    }
 

@app.post("/query", response_model=DataQueryResponse)
def execute_query(payload: DataQueryRequest):
    """
    Executes Text-to-SQL against the Northwind database conforming strictly
    to Interface 2 specification.
    """
    try:
        res = query_data_mock(payload.question)
        return DataQueryResponse(
            sql=res.get("sql", ""),
            rows=res.get("rows", []),
            columns=res.get("columns", []),
            row_count=res.get("row_count", 0),
            error=res.get("error"),
            answerable=res.get("answerable", True)
        )
    except Exception as e:
        return DataQueryResponse(
            sql="",
            rows=[],
            columns=[],
            row_count=0,
            error=f"Data Service Error: {str(e)}",
            answerable=False
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app_role_b.py:app" if os.path.exists("app_role_b.py") else app, host="127.0.0.1", port=8001, reload=False)
