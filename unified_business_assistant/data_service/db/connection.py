import os
import sqlite3
import time
from typing import Any, List, Optional, Tuple

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(DB_DIR, "enterprise_business.db")


class DatabaseConnectionManager:
    _cached_counts = None

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.getenv("SQL_DATABASE_PATH", DEFAULT_DB_PATH)
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(
                f"Database file not found at: {self.db_path}. Run `python db/seed_database.py` first."
            )

    def get_readonly_connection(self) -> sqlite3.Connection:
        normalized_path = os.path.abspath(self.db_path).replace("\\", "/")
        uri = f"file:{normalized_path}?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=5.0)
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
        start_time = time.perf_counter()
        conn = self.get_readonly_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params or ())

            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            raw_rows = cursor.fetchmany(max_rows)
            rows = [list(row) for row in raw_rows]

            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return columns, rows, duration_ms
        finally:
            conn.close()

    def get_table_counts(self) -> dict:
        if self._cached_counts is not None:
            return self._cached_counts
        conn = self.get_readonly_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = [row[0] for row in cursor.fetchall()]
            counts = {}
            for t in tables:
                cursor.execute(f'SELECT COUNT(*) FROM "{t}";')
                counts[t] = cursor.fetchone()[0]
            self._cached_counts = counts
            return counts
        finally:
            conn.close()


db_manager = DatabaseConnectionManager()
