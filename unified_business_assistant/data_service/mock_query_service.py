"""
Day 1 deliverable: Mock POST /query endpoint for Role B (Data Service).

Returns TWO REAL ROWS from the authentic database plus a real SQL string
in the exact contracted shape (contracts.py), allowing Role C (orchestrator)
to develop without dependencies.

Run:
    uvicorn mock_query_service:app --port 8002
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from contracts import QueryRequest, QueryResponse

app = FastAPI(
    title="Data Service (Role B) - MOCK",
    version="1.0.0-mock",
    description="Mock text-to-SQL endpoint for Role C orchestrator integration",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MOCK_COLUMNS = ["CustomerName", "InvoiceCount"]
MOCK_ROWS = [
    ["Luís Gonçalves", 7],
    ["Leonie Köhler", 7],
]
MOCK_SQL = (
    "SELECT c.FirstName || ' ' || c.LastName AS CustomerName, COUNT(i.InvoiceId) AS InvoiceCount "
    "FROM Customer c "
    "JOIN Invoice i ON c.CustomerId = i.CustomerId "
    "GROUP BY c.CustomerId, CustomerName "
    "ORDER BY InvoiceCount DESC "
    "LIMIT 2;"
)


@app.post("/query", response_model=QueryResponse)
def mock_query(payload: QueryRequest) -> QueryResponse:
    q = payload.question.lower()

    # Simulated service failure branch for Role C resilience tests
    if "error" in q:
        raise HTTPException(
            status_code=503,
            detail="MOCK: Simulated database connection or query execution failure",
        )

    # Simulated unanswerable branch for Role C answerability tests
    if "unanswerable" in q or "out-of-scope" in q or "unknown" in q:
        return QueryResponse(
            columns=[],
            rows=[],
            sql=None,
            answerable=False,
            error="MOCK: The question cannot be answered from the structured database schema.",
            execution_time_ms=1.2,
        )

    # Standard contracted mock response (2 real rows + SQL + answerable=True)
    return QueryResponse(
        columns=MOCK_COLUMNS,
        rows=MOCK_ROWS[: payload.limit],
        sql=MOCK_SQL,
        answerable=True,
        error=None,
        execution_time_ms=2.5,
    )


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "data_service",
        "role": "Role B",
        "mode": "mock",
    }
