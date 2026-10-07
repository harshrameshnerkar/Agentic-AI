"""
Session Manager for Capstone OpsSentinel Serving Layer.
Maintains isolated state, conversation history, and entity configurations per session_id.
"""

import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MessageRecord(BaseModel):
    role: str  # "user", "assistant", "system"
    content: str
    tools_called: List[Dict[str, Any]] = Field(default_factory=list)
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    latency_ms: float = 0.0
    tokens_used: int = 0
    timestamp: float = Field(default_factory=time.time)


class SessionState(BaseModel):
    session_id: str
    user_name: str = "Sarah Conner"
    user_role: str = "Admin"  # "Admin", "Engineer", "Auditor"
    environment: str = "production"
    datacenter: str = "us-east-1"
    active_ticket: str = "INC-801"
    approval_token: str = "AUTH-OPS-APPROVE-2026"
    messages: List[MessageRecord] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)

    def to_system_context(self) -> str:
        return (
            f"[SESSION ENTITY CONTEXT] User: {self.user_name} | "
            f"Role: {self.user_role} | "
            f"Env: {self.environment} ({self.datacenter}) | "
            f"Active Ticket: {self.active_ticket}"
        )


class SessionManager:
    """In-memory thread-safe session registry."""

    def __init__(self):
        self._sessions: Dict[str, SessionState] = {}

    def get_or_create(self, session_id: Optional[str] = None, user_role: str = "Admin") -> SessionState:
        sid = session_id or f"sess-{uuid.uuid4().hex[:8]}"
        if sid not in self._sessions:
            self._sessions[sid] = SessionState(session_id=sid, user_role=user_role)
        return self._sessions[sid]

    def get(self, session_id: str) -> Optional[SessionState]:
        return self._sessions.get(session_id)

    def update_role(self, session_id: str, role: str) -> None:
        if session_id in self._sessions:
            self._sessions[session_id].user_role = role
            self._sessions[session_id].updated_at = time.time()

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tools_called: Optional[List[Dict[str, Any]]] = None,
        citations: Optional[List[Dict[str, Any]]] = None,
        latency_ms: float = 0.0,
        tokens_used: int = 0,
    ) -> MessageRecord:
        sess = self.get_or_create(session_id)
        msg = MessageRecord(
            role=role,
            content=content,
            tools_called=tools_called or [],
            citations=citations or [],
            latency_ms=latency_ms,
            tokens_used=tokens_used,
            timestamp=time.time(),
        )
        sess.messages.append(msg)
        sess.updated_at = time.time()
        return msg

    def clear(self, session_id: str) -> bool:
        if session_id in self._sessions:
            self._sessions[session_id].messages.clear()
            self._sessions[session_id].updated_at = time.time()
            return True
        return False

    def list_all(self) -> List[Dict[str, Any]]:
        return [
            {
                "session_id": s.session_id,
                "user_role": s.user_role,
                "message_count": len(s.messages),
                "created_at": s.created_at,
                "updated_at": s.updated_at,
            }
            for s in self._sessions.values()
        ]
