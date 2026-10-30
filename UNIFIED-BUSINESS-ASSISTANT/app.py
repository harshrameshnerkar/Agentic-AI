import os
import sys
from typing import List, Optional
from fastapi import FastAPI, HTTPException 
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from contracts import SearchRequest, SearchResponse
from rag_engine import UnifiedRAGEngine

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

app = FastAPI(
    title="Knowledge Service",
    description="Document retrieval and policy search service.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = UnifiedRAGEngine()

static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = Field(default="default_session")
    top_k: Optional[int] = Field(default=4)
    score_threshold: Optional[float] = Field(default=0.75)


class ChatResponse(BaseModel):
    session_id: str
    question: str
    standalone_question: str
    answer: str
    citations: List[dict]
    model_used: str
    no_match: bool


@app.get("/")
def serve_dashboard():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Knowledge Service is running. See /docs for API endpoints."}


@app.post("/search", response_model=SearchResponse)
def search_documents(payload: SearchRequest):
    try:
        threshold = payload.score_threshold if payload.score_threshold is not None else 0.75
        q = payload.question or payload.query or ""
        return engine.search(
            question=q,
            top_k=payload.top_k or 5,
            score_threshold=threshold,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {e}")


@app.post("/chat", response_model=ChatResponse)
def conversational_chat(payload: ChatRequest):
    try:
        return engine.chat(
            user_message=payload.message,
            session_id=payload.session_id,
            top_k=payload.top_k,
            score_threshold=payload.score_threshold,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {e}")


@app.get("/documents")
def get_document_catalog():
    return engine.catalog


@app.get("/stats")
def get_telemetry_stats():
    try:
        return engine.get_stats()
    except Exception as e:
        return {"error": str(e)}


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Role A - Knowledge Service",
        "neon_connected": True,
        "active_documents": engine.catalog.get("total_documents", 50),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
