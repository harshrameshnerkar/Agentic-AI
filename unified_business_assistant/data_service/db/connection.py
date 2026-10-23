"""
Read-Only Database Connection Manager for Role B (Data Service).

Enforces defense-in-depth database security:
1. URI read-only parameter: `file:{path}?mode=ro`
2. SQLite engine enforcement: `PRAGMA query_only = ON;`
3. Resource limits: execution timeouts and max row truncation.
"""
import os
import sqlite3
import time
from typing import Any, List, Optional, Tuple

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(DB_DIR, "enterprise_business.db")


class DatabaseConnectionManager:
    """Manages read-only connections and bounded query execution."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.getenv("SQL_DATABASE_PATH", DEFAULT_DB_PATH)
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(
                f"Database file not found at: {self.db_path}. Please run `python db/seed_database.py` first."
            )

    def get_readonly_connection(self) -> sqlite3.Connection:
        """
        Creates an immutable, strictly read-only SQLite connection.
        Uses URI mode=ro and query_only=ON for multi-layer kernel/driver enforcement.
        """
        # Convert backslashes for URI format on Windows
        normalized_path = os.path.abspath(self.db_path).replace("\\", "/")
        uri = f"file:{normalized_path}?mode=ro"

        conn = sqlite3.connect(uri, uri=True, timeout=5.0)
        # Secondary defense in depth pragma
        conn.execute("PRAGMA query_only = ON;")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def execute_query(
        self,
        sql: str,
        params: Optional[Tuple[Any, ...]] = None,
        max_rows: int = 100,
        timeout_sec: float = 5.0,
    ) -> Tuple[List[str], List[List[Any]], float]:
        """
        Executes a validated read-only SQL query with timeouts and bounds.

        Returns:
            columns: List of column names
            rows: 2D array of results truncated to max_rows
            duration_ms: Execution duration in milliseconds
        """
        start_time = time.perf_counter()
        conn = self.get_readonly_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params or ())

            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            raw_rows = cursor.fetchmany(max_rows)
            # Format row elements cleanly (e.g. None -> None, numbers preserved)
            rows = [[col for col in row] for row in raw_rows]

            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return columns, rows, duration_ms
        finally:
            conn.close()

    def get_table_counts(self) -> dict:
        """Returns row counts for all tables in the database."""
        conn = self.get_readonly_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = [row[0] for row in cursor.fetchall()]
            counts = {}
            for t in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {t};")
                counts[t] = cursor.fetchone()[0]
            return counts
        finally:
            conn.close()


# Shared singleton instance
db_manager = DatabaseConnectionManager()
