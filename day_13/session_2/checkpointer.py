"""
Day 13 - Session 2: Durable SQLite Checkpointer (LangGraph Persistence Specification)
=====================================================================================
Implements:
  1. Transactional State Checkpointing (ACID SQLite backing)
  2. Granular Step-Level State Serialization (node_name, step_index, graph_state)
  3. Parent Checkpoint Chaining for Auditability & Time-Travel Debugging
  4. Tenant-Scoped Partitioning (strict multi-tenant isolation)
"""

import os
import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class CheckpointRecord:
    checkpoint_id: str
    session_id: str
    tenant_id: str
    step_index: int
    node_name: str
    state: Dict[str, Any]
    parent_checkpoint_id: Optional[str]
    created_at: str


class SqliteCheckpointer:
    """
    Durable SQLite State Checkpoint Engine.
    Persists agent graph execution state at every node boundary.
    Enables interrupted / crashed runs to resume exactly from their last step.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(current_dir, "agent_checkpoints.db")
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
        """Initializes checkpoint schema and index."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    checkpoint_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    step_index INTEGER NOT NULL,
                    node_name TEXT NOT NULL,
                    state_json TEXT NOT NULL,
                    parent_checkpoint_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_checkpoints_session 
                ON checkpoints(session_id, tenant_id, step_index);
            """)
            conn.commit()

    def save_checkpoint(
        self,
        session_id: str,
        tenant_id: str,
        step_index: int,
        node_name: str,
        state: Dict[str, Any],
        parent_checkpoint_id: Optional[str] = None,
    ) -> str:
        """Persists an atomic step checkpoint to SQLite."""
        checkpoint_id = f"CHK-{uuid.uuid4().hex[:12].upper()}"
        state_serialized = json.dumps(state, ensure_ascii=False)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO checkpoints (
                    checkpoint_id, session_id, tenant_id, step_index, node_name, state_json, parent_checkpoint_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (checkpoint_id, session_id, tenant_id, step_index, node_name, state_serialized, parent_checkpoint_id))
            conn.commit()

        return checkpoint_id

    def load_latest(self, session_id: str, tenant_id: str) -> Optional[CheckpointRecord]:
        """Loads the most recent checkpoint for a given session and tenant."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT checkpoint_id, session_id, tenant_id, step_index, node_name, state_json, parent_checkpoint_id, created_at
                FROM checkpoints
                WHERE session_id = ? AND tenant_id = ?
                ORDER BY step_index DESC, created_at DESC
                LIMIT 1;
            """, (session_id, tenant_id))
            row = cursor.fetchone()
            if not row:
                return None

            return CheckpointRecord(
                checkpoint_id=row["checkpoint_id"],
                session_id=row["session_id"],
                tenant_id=row["tenant_id"],
                step_index=row["step_index"],
                node_name=row["node_name"],
                state=json.loads(row["state_json"]),
                parent_checkpoint_id=row["parent_checkpoint_id"],
                created_at=row["created_at"],
            )

    def list_checkpoints(self, session_id: str, tenant_id: str) -> List[CheckpointRecord]:
        """Lists full chronological checkpoint lineage for an execution run."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT checkpoint_id, session_id, tenant_id, step_index, node_name, state_json, parent_checkpoint_id, created_at
                FROM checkpoints
                WHERE session_id = ? AND tenant_id = ?
                ORDER BY step_index ASC;
            """, (session_id, tenant_id))
            rows = cursor.fetchall()

            return [
                CheckpointRecord(
                    checkpoint_id=r["checkpoint_id"],
                    session_id=r["session_id"],
                    tenant_id=r["tenant_id"],
                    step_index=r["step_index"],
                    node_name=r["node_name"],
                    state=json.loads(r["state_json"]),
                    parent_checkpoint_id=r["parent_checkpoint_id"],
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    def purge_session(self, session_id: str, tenant_id: str) -> int:
        """Deletes all checkpoints for a session (compliance & data retention)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM checkpoints WHERE session_id = ? AND tenant_id = ?", (session_id, tenant_id))
            count = cursor.rowcount
            conn.commit()
            return count

    def purge_tenant(self, tenant_id: str) -> int:
        """Hard purge of all checkpoints for a tenant (GDPR right-to-be-forgotten)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM checkpoints WHERE tenant_id = ?", (tenant_id,))
            count = cursor.rowcount
            conn.commit()
            return count
