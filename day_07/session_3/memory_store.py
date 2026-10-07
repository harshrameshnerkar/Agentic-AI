"""
Day 7 - Session 3: Memory
Module: memory_store.py

Implements persistent multi-tier memory for AI agents:
1. Long-Term Persistent Memory: Scoped by per-user key (user_id), backed by SQLite disk storage.
2. Short-Term Conversation Buffer: Scoped by session key (thread_id).
3. Summarization Memory: Compacting older turns into episodic milestone summaries.
4. Security Sanitizer: Enforcement of 'What Must NEVER Be Persisted' (API keys, passwords, PII).
5. Just-In-Time Retrieval: Injecting relevant memory into system prompt before LLM invocation.
"""

from __future__ import annotations
import os
import re
import json
import sqlite3
import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DB_PATH = Path(__file__).resolve().parent / "agent_memory.db"


class SecuritySanitizer:
    """
    Enforces strict security boundaries on what is allowed into long-term memory.
    Rejects or redacts:
    - API keys & access tokens (e.g. sk-..., AIza..., bearer tokens, AWS secrets).
    - Passwords & private keys.
    - PII / PCI data (credit card numbers, social security numbers).
    """

    SECRET_PATTERNS = [
        (re.compile(r"sk-[A-Za-z0-9_\-]{15,}", re.IGNORECASE), "OPENAI_API_KEY"),
        (re.compile(r"AIza[0-9A-Za-z\-_]{35}", re.IGNORECASE), "GOOGLE_API_KEY"),
        (re.compile(r"(?:api[_-]?key|secret|token|password|auth|credential|bearer)", re.IGNORECASE), "CREDENTIAL_KEYWORD"),
        (re.compile(r"\b(?:\d[ -]*?){13,16}\b"), "CREDIT_CARD_NUMBER"),
        (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "SSN"),
    ]

    @classmethod
    def inspect_and_sanitize(cls, key: str, value: str) -> Tuple[bool, str, Optional[str]]:
        """
        Inspects candidate memory key/value pair.
        Returns: (is_safe, sanitized_value, violation_reason)
        """
        combined = f"{key} {value}"
        for pattern, label in cls.SECRET_PATTERNS:
            if pattern.search(combined):
                return False, "[REDACTED_SENSITIVE_DATA]", f"Blocked by Security Policy: Detected forbidden sensitive pattern '{label}'. Ephemeral credentials and PII must NEVER be persisted."
        return True, value, None


class PersistentMemoryStore:
    """
    SQLite-backed persistent memory engine that survives complete process restarts.
    """

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_schema(self):
        """Initializes tables for long-term user preferences and session summaries."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 1. Long-term user preferences table (scoped by user_id)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id TEXT NOT NULL,
                    pref_key TEXT NOT NULL,
                    pref_value TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT 'general',
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (user_id, pref_key)
                );
            """)

            # 2. Session summaries table (scoped by thread_id)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS session_summaries (
                    thread_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)
            conn.commit()

    def save_user_preference(
        self,
        user_id: str,
        key: str,
        value: str,
        category: str = "general"
    ) -> Dict[str, Any]:
        """
        Saves a user preference with strict security validation.
        """
        clean_user = (user_id or "").strip()
        clean_key = (key or "").strip().lower()
        clean_val = (value or "").strip()

        if not clean_user or not clean_key or not clean_val:
            return {
                "status": "error",
                "message": "user_id, key, and value must not be empty."
            }

        # Security check: What must NEVER be persisted
        is_safe, sanitized_val, violation = SecuritySanitizer.inspect_and_sanitize(clean_key, clean_val)
        if not is_safe:
            return {
                "status": "security_violation",
                "message": violation,
                "key": clean_key,
                "sanitized": True
            }

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_preferences (user_id, pref_key, pref_value, category, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id, pref_key) DO UPDATE SET
                    pref_value = excluded.pref_value,
                    category = excluded.category,
                    updated_at = excluded.updated_at;
            """, (clean_user, clean_key, sanitized_val, category, now_iso))
            conn.commit()

        return {
            "status": "success",
            "user_id": clean_user,
            "key": clean_key,
            "value": sanitized_val,
            "category": category,
            "saved_at": now_iso
        }

    def get_user_preferences(self, user_id: str) -> List[Dict[str, str]]:
        """Retrieves all stored long-term preferences for a specific user_id."""
        clean_user = (user_id or "").strip()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pref_key, pref_value, category, updated_at
                FROM user_preferences
                WHERE user_id = ?
                ORDER BY updated_at ASC;
            """, (clean_user,))
            rows = cursor.fetchall()

        return [
            {"key": r[0], "value": r[1], "category": r[2], "updated_at": r[3]}
            for r in rows
        ]

    def build_memory_prompt_injection(self, user_id: str) -> str:
        """
        Just-in-Time Memory Retrieval:
        Formats recalled user preferences into an injection block for the system prompt.
        """
        prefs = self.get_user_preferences(user_id)
        if not prefs:
            return ""

        lines = [f"[LONG-TERM USER MEMORY RECALLED for '{user_id}']"]
        lines.append("The user has established the following persistent preferences across prior sessions:")
        for p in prefs:
            lines.append(f"  • {p['key'].replace('_', ' ').title()}: {p['value']} (Category: {p['category']})")
        lines.append("You MUST adhere to these preferences throughout the interaction.")
        return "\n".join(lines)

    def save_session_summary(self, thread_id: str, user_id: str, summary: str):
        """Persists episodic session summary when conversation buffer exceeds limit."""
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO session_summaries (thread_id, user_id, summary, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(thread_id) DO UPDATE SET
                    summary = excluded.summary,
                    updated_at = excluded.updated_at;
            """, (thread_id, user_id, summary, now_iso))
            conn.commit()

    def get_session_summary(self, thread_id: str) -> Optional[str]:
        """Retrieves episodic session summary."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT summary FROM session_summaries WHERE thread_id = ?;", (thread_id,))
            row = cursor.fetchone()
            return row[0] if row else None

    def reset_for_clean_test(self):
        """Helper to reinitialize tables for test reproducibility."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_preferences;")
            cursor.execute("DELETE FROM session_summaries;")
            conn.commit()
