"""
FastAPI Serving Application for Capstone OpsSentinel AI.
Endpoints:
- POST /api/chat: Non-streaming JSON endpoint with tool calls & citations.
- POST /api/chat/stream: Server-Sent Events (SSE) streaming endpoint.
- GET  /api/sessions: Lists active sessions.
- GET  /api/sessions/{session_id}: Inspects specific session state.
- DELETE /api/sessions/{session_id}: Clears session conversation history.
- GET  /health: Service health and readiness probe.
"""

import json
import asyncio
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from session_manager import SessionManager
from agent_service import CapstoneAgentService

app = FastAPI(
    title="Capstone Project: Autonomous AI SRE Copilot API",
    description="Enterprise SRE & Incident Response Agent Microservice with RAG, Tools, Memory, and Guardrails.",
    version="1.0.0",
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session_manager = SessionManager()
agent_service = CapstoneAgentService()


class ChatRequest(BaseModel):
    message: str = Field(..., description="User query or command")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    user_role: Optional[str] = Field("Admin", description="User role: Admin, Engineer, Auditor")


class ChatResponse(BaseModel):
    session_id: str
    final_answer: str
    tools_called: List[Dict[str, Any]]
    citations: List[Dict[str, Any]]
    tokens_used: int
    latency_ms: float
    is_blocked: bool


@app.get("/health")
def health_check():
    return {
        "status": "HEALTHY",
        "service": "Capstone AI SRE Copilot Serving Engine",
        "model": agent_service.model,
        "active_sessions": len(session_manager.list_all()),
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    """Synchronous JSON endpoint returning response, tools invoked, and cited sources."""
    sess = session_manager.get_or_create(req.session_id, user_role=req.user_role)
    if req.user_role:
        session_manager.update_role(sess.session_id, req.user_role)

    result = agent_service.run(sess, req.message)

    # Record into session memory
    session_manager.add_message(
        session_id=sess.session_id,
        role="user",
        content=req.message,
    )
    session_manager.add_message(
        session_id=sess.session_id,
        role="assistant",
        content=result.get("final_answer", ""),
        tools_called=result.get("tools_called", []),
        citations=result.get("citations", []),
        latency_ms=result.get("latency_ms", 0.0),
        tokens_used=result.get("tokens_used", 0),
    )

    return ChatResponse(
        session_id=sess.session_id,
        final_answer=result.get("final_answer", ""),
        tools_called=result.get("tools_called", []),
        citations=result.get("citations", []),
        tokens_used=result.get("tokens_used", 0),
        latency_ms=result.get("latency_ms", 0.0),
        is_blocked=result.get("is_blocked", False),
    )


@app.post("/api/chat/stream")
def chat_stream_endpoint(req: ChatRequest):
    """Server-Sent Events (SSE) streaming endpoint emitting real-time agent events."""
    sess = session_manager.get_or_create(req.session_id, user_role=req.user_role)
    if req.user_role:
        session_manager.update_role(sess.session_id, req.user_role)

    def event_generator():
        # Record user message first
        session_manager.add_message(sess.session_id, "user", req.message)
        final_pack = {}

        for event in agent_service.stream_run(sess, req.message):
            if event.get("type") == "complete":
                final_pack = event
            # Format SSE event
            payload = json.dumps(event)
            yield f"event: {event.get('type')}\ndata: {payload}\n\n"

        # Record assistant reply into session memory
        if final_pack:
            session_manager.add_message(
                session_id=sess.session_id,
                role="assistant",
                content=final_pack.get("final_answer", ""),
                tools_called=final_pack.get("tools_called", []),
                citations=final_pack.get("citations", []),
                latency_ms=final_pack.get("latency_ms", 0.0),
                tokens_used=final_pack.get("tokens_used", 0),
            )

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/sessions")
def list_sessions_endpoint():
    return {"sessions": session_manager.list_all()}


@app.get("/api/sessions/{session_id}")
def get_session_endpoint(session_id: str):
    sess = session_manager.get(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    return sess.model_dump()


@app.delete("/api/sessions/{session_id}")
def clear_session_endpoint(session_id: str):
    cleared = session_manager.clear(session_id)
    if not cleared:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "SUCCESS", "message": f"Session '{session_id}' cleared."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="127.0.0.1", port=8000, reload=False)
