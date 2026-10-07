"""
Durable Transactional State Checkpointer for OpsSentinel Enterprise.
Provides SQLite-backed ACID state checkpointing with Write-Ahead Logging (WAL),
idempotent step recovery, and audit tracking across crashes and process restarts.
"""

import sqlite3
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel, Field

from contextlib import contextmanager

import sys
_script_dir = Path(__file__).resolve().parent
_workspace_root = _script_dir.parent.parent
for _p in [str(_workspace_root), str(_script_dir)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from day_15.session_1.config import config
except ImportError:
    try:
        from .config import config
    except ImportError:
        from config import config

class WorkflowStatus(str, Enum):
    INITIALIZED = "INITIALIZED"
    ROUTING = "ROUTING"
    DIAGNOSING = "DIAGNOSING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    EXECUTING_ACTION = "EXECUTING_ACTION"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"

class SessionState(BaseModel):
    session_id: str
    user_id: str = "sre-operator"
    tenant_id: str = "tenant-default"
    status: WorkflowStatus = WorkflowStatus.INITIALIZED
    current_step: int = 0
    query: str
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    routing_decision: Optional[Dict[str, Any]] = None
    accumulated_context: Dict[str, Any] = Field(default_factory=dict)
    pending_approval_id: Optional[str] = None
    final_output: Optional[str] = None

class DurableStateCheckpointer:
    """ACID SQLite checkpointer with WAL journaling for resilient agent execution."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or config.sqlite_db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path), timeout=15.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        try:
            yield conn
        finally:
            conn.close()

    def _init_database(self) -> None:
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    current_step INTEGER NOT NULL DEFAULT 0,
                    query TEXT NOT NULL,
                    routing_decision_json TEXT,
                    accumulated_context_json TEXT,
                    pending_approval_id TEXT,
                    final_output TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS checkpoints (
                    checkpoint_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    step_index INTEGER NOT NULL,
                    step_name TEXT NOT NULL,
                    state_snapshot_json TEXT NOT NULL,
                    checksum_hash TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                );

                CREATE TABLE IF NOT EXISTS step_executions (
                    execution_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    step_index INTEGER NOT NULL,
                    tool_name TEXT NOT NULL,
                    tier TEXT NOT NULL,
                    input_params_json TEXT NOT NULL,
                    output_result_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    latency_ms REAL NOT NULL,
                    error_msg TEXT,
                    created_at REAL NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                );

                CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
                CREATE INDEX IF NOT EXISTS idx_checkpoints_session ON checkpoints(session_id, step_index);
            """)
            conn.commit()

    def create_session(
        self,
        session_id: str,
        query: str,
        user_id: str = "sre-operator",
        tenant_id: str = "tenant-default"
    ) -> SessionState:
        now = time.time()
        initial_state = SessionState(
            session_id=session_id,
            user_id=user_id,
            tenant_id=tenant_id,
            status=WorkflowStatus.INITIALIZED,
            current_step=0,
            query=query,
            created_at=now,
            updated_at=now
        )
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO sessions (
                    session_id, user_id, tenant_id, status, current_step,
                    query, routing_decision_json, accumulated_context_json,
                    pending_approval_id, final_output, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                initial_state.session_id,
                initial_state.user_id,
                initial_state.tenant_id,
                initial_state.status.value,
                initial_state.current_step,
                initial_state.query,
                None,
                json.dumps(initial_state.accumulated_context),
                None,
                None,
                initial_state.created_at,
                initial_state.updated_at
            ))
            conn.commit()

        self.save_checkpoint(session_id, "SESSION_INITIALIZED", initial_state.model_dump())
        return initial_state

    def save_checkpoint(self, session_id: str, step_name: str, state_snapshot: Dict[str, Any]) -> int:
        serialized = json.dumps(state_snapshot, sort_keys=True)
        checksum = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        now = time.time()
        step_index = state_snapshot.get("current_step", 0)

        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO checkpoints (
                    session_id, step_index, step_name, state_snapshot_json, checksum_hash, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, step_index, step_name, serialized, checksum, now))
            checkpoint_id = cursor.lastrowid or 0
            conn.commit()
            return checkpoint_id

    def update_session(
        self,
        session_id: str,
        status: Optional[WorkflowStatus] = None,
        current_step: Optional[int] = None,
        routing_decision: Optional[Dict[str, Any]] = None,
        accumulated_context: Optional[Dict[str, Any]] = None,
        pending_approval_id: Optional[str] = None,
        final_output: Optional[str] = None
    ) -> None:
        now = time.time()
        with self._get_connection() as conn:
            cur = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Session {session_id} not found in database.")

            new_status = status.value if status else row["status"]
            new_step = current_step if current_step is not None else row["current_step"]
            new_routing = json.dumps(routing_decision) if routing_decision is not None else row["routing_decision_json"]
            new_context = json.dumps(accumulated_context) if accumulated_context is not None else row["accumulated_context_json"]
            new_pending = pending_approval_id if pending_approval_id is not None else row["pending_approval_id"]
            new_final = final_output if final_output is not None else row["final_output"]

            conn.execute("""
                UPDATE sessions SET
                    status = ?,
                    current_step = ?,
                    routing_decision_json = ?,
                    accumulated_context_json = ?,
                    pending_approval_id = ?,
                    final_output = ?,
                    updated_at = ?
                WHERE session_id = ?
            """, (new_status, new_step, new_routing, new_context, new_pending, new_final, now, session_id))
            conn.commit()

    def record_tool_execution(
        self,
        execution_id: str,
        session_id: str,
        step_index: int,
        tool_name: str,
        tier: str,
        input_params: Dict[str, Any],
        output_result: Dict[str, Any],
        status: str,
        latency_ms: float,
        error_msg: Optional[str] = None
    ) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO step_executions (
                    execution_id, session_id, step_index, tool_name, tier,
                    input_params_json, output_result_json, status, latency_ms, error_msg, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                execution_id,
                session_id,
                step_index,
                tool_name,
                tier,
                json.dumps(input_params),
                json.dumps(output_result),
                status,
                latency_ms,
                error_msg,
                time.time()
            ))
            conn.commit()

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cur = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
            row = cur.fetchone()
            if not row:
                return None
            return {
                "session_id": row["session_id"],
                "user_id": row["user_id"],
                "tenant_id": row["tenant_id"],
                "status": row["status"],
                "current_step": row["current_step"],
                "query": row["query"],
                "routing_decision": json.loads(row["routing_decision_json"]) if row["routing_decision_json"] else None,
                "accumulated_context": json.loads(row["accumulated_context_json"]) if row["accumulated_context_json"] else {},
                "pending_approval_id": row["pending_approval_id"],
                "final_output": row["final_output"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }

    def get_checkpoints(self, session_id: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cur = conn.execute("""
                SELECT checkpoint_id, step_index, step_name, state_snapshot_json, checksum_hash, timestamp
                FROM checkpoints WHERE session_id = ? ORDER BY checkpoint_id ASC
            """, (session_id,))
            rows = cur.fetchall()
            return [
                {
                    "checkpoint_id": r["checkpoint_id"],
                    "step_index": r["step_index"],
                    "step_name": r["step_name"],
                    "state_snapshot": json.loads(r["state_snapshot_json"]),
                    "checksum_hash": r["checksum_hash"],
                    "timestamp": r["timestamp"]
                }
                for r in rows
            ]

    def list_active_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cur = conn.execute("""
                SELECT session_id, user_id, tenant_id, status, current_step, query, updated_at
                FROM sessions ORDER BY updated_at DESC LIMIT ?
            """, (limit,))
            rows = cur.fetchall()
            return [dict(r) for r in rows]
