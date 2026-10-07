"""
Day 13 - Session 2: Multi-Tenant State, Sessions & Data Retention
=================================================================
Implements:
  1. Per-User & Per-Tenant Isolation (scoping by tenant_id and user_id)
  2. Durable Conversation Storage (append-only turn journal in SQLite)
  3. Data Retention & Automatic TTL Deletion (purge_expired_sessions)
  4. Enterprise Compliance & Right-to-be-Forgotten (hard_delete_tenant)
"""

import os
import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class ConversationTurn:
    turn_id: str
    session_id: str
    tenant_id: str
    user_id: str
    role: str       # "user" | "assistant" | "system" | "tool"
    content: str
    metadata: Dict[str, Any]
    created_at: float


class TenantSessionManager:
    """
    Enterprise Multi-Tenant Session and Conversation Store.
    Strictly partitions all interactions by tenant_id to guarantee zero data leakage.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(current_dir, "multi_tenant_store.db")
        self.db_path = db_path
        self._init_database()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_database(self) -> None:
        """Creates conversation journal and session index."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_turns (
                    turn_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at REAL NOT NULL
                );
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tenant_session 
                ON conversation_turns(tenant_id, session_id, created_at);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tenant_user 
                ON conversation_turns(tenant_id, user_id);
            """)
            conn.commit()

    def append_turn(
        self,
        session_id: str,
        tenant_id: str,
        user_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Appends a conversation message to the tenant's isolated journal."""
        turn_id = f"TRN-{uuid.uuid4().hex[:10].upper()}"
        meta_json = json.dumps(metadata or {}, ensure_ascii=False)
        now = time.time()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conversation_turns (
                    turn_id, session_id, tenant_id, user_id, role, content, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (turn_id, session_id, tenant_id, user_id, role, content, meta_json, now))
            conn.commit()

        return turn_id

    def get_conversation_history(
        self,
        session_id: str,
        tenant_id: str,
        limit: int = 50,
    ) -> List[ConversationTurn]:
        """Retrieves conversation turns strictly isolated to the requesting tenant."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT turn_id, session_id, tenant_id, user_id, role, content, metadata_json, created_at
                FROM conversation_turns
                WHERE session_id = ? AND tenant_id = ?
                ORDER BY created_at ASC
                LIMIT ?;
            """, (session_id, tenant_id, limit))
            rows = cursor.fetchall()

            return [
                ConversationTurn(
                    turn_id=r["turn_id"],
                    session_id=r["session_id"],
                    tenant_id=r["tenant_id"],
                    user_id=r["user_id"],
                    role=r["role"],
                    content=r["content"],
                    metadata=json.loads(r["metadata_json"]),
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    def purge_expired_sessions(self, max_age_seconds: float) -> int:
        """Prunes conversation history older than retention policy TTL."""
        cutoff = time.time() - max_age_seconds
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM conversation_turns WHERE created_at < ?;", (cutoff,))
            count = cursor.rowcount
            conn.commit()
            return count

    def hard_delete_tenant(self, tenant_id: str) -> int:
        """GDPR compliance: purges all data for a specific enterprise tenant."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM conversation_turns WHERE tenant_id = ?;", (tenant_id,))
            count = cursor.rowcount
            conn.commit()
            return count

    def delete_user_sessions(self, tenant_id: str, user_id: str) -> int:
        """Purges all sessions belonging to a specific user within a tenant."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM conversation_turns WHERE tenant_id = ? AND user_id = ?;", (tenant_id, user_id))
            count = cursor.rowcount
            conn.commit()
            return count
