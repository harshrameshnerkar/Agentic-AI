"""
Memory Subsystem for Capstone OpsSentinel AI.
Implements:
1. Short-Term Working Memory (Sliding conversation buffer preserving multi-turn context).
2. Long-Term Semantic & Entity Memory (User identity, role, environment state, active incident tracking).
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ConversationTurn(BaseModel):
    turn_id: int
    user_query: str
    tools_called: List[str] = Field(default_factory=list)
    agent_response: str
    timestamp: float


class EntityMemoryStore:
    """Stores persistent session and entity state (User, Role, Active Incidents)."""

    def __init__(self):
        self.entities: Dict[str, Any] = {
            "current_user": "Sarah Conner",
            "user_role": "Admin",  # Roles: "Admin", "Engineer", "Auditor"
            "environment": "production",
            "datacenter": "us-east-1",
            "active_ticket": "INC-801",
            "approval_token": "AUTH-OPS-APPROVE-2026",
            "preferences": {
                "timezone": "UTC",
                "default_log_lines": 10,
                "preferred_channel": "#ops-incident-war-room",
            },
        }

    def get_entity(self, key: str, default: Any = None) -> Any:
        return self.entities.get(key, default)

    def set_entity(self, key: str, value: Any) -> None:
        self.entities[key] = value

    def to_system_context(self) -> str:
        """Serializes current entity memory into compact system prompt context."""
        return (
            f"[SESSION ENTITY CONTEXT] User: {self.entities.get('current_user')} | "
            f"Role: {self.entities.get('user_role')} | "
            f"Env: {self.entities.get('environment')} ({self.entities.get('datacenter')}) | "
            f"Active Ticket: {self.entities.get('active_ticket')}"
        )


class ConversationMemoryBuffer:
    """Manages short-term conversation turns using a bounded sliding window."""

    def __init__(self, max_turns: int = 6):
        self.max_turns = max_turns
        self.history: List[ConversationTurn] = []

    def add_turn(self, user_query: str, agent_response: str, tools_called: List[str], timestamp: float) -> None:
        turn = ConversationTurn(
            turn_id=len(self.history) + 1,
            user_query=user_query,
            tools_called=tools_called,
            agent_response=agent_response,
            timestamp=timestamp,
        )
        self.history.append(turn)
        # Enforce sliding window capacity
        if len(self.history) > self.max_turns:
            self.history = self.history[-self.max_turns:]

    def get_recent_messages(self) -> List[Dict[str, str]]:
        """Returns message list formatted for chat completion history."""
        msgs = []
        for turn in self.history:
            msgs.append({"role": "user", "content": turn.user_query})
            msgs.append({"role": "assistant", "content": turn.agent_response})
        return msgs

    def clear(self) -> None:
        self.history.clear()


class MemoryManager:
    """Unified memory controller combining short-term dialogue buffer and long-term entity store."""

    def __init__(self, max_turns: int = 6):
        self.entity_store = EntityMemoryStore()
        self.buffer = ConversationMemoryBuffer(max_turns=max_turns)

    def get_context_injection(self) -> str:
        return self.entity_store.to_system_context()

    def record_interaction(self, query: str, response: str, tools: List[str], timestamp: float) -> None:
        self.buffer.add_turn(user_query=query, agent_response=response, tools_called=tools, timestamp=timestamp)

    def reset_history(self) -> None:
        self.buffer.clear()
