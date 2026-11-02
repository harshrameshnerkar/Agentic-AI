"""PostgreSQL SQL validation and read-only execution for the real API."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor
import sqlglot
from sqlglot import exp


DEFAULT_ROW_LIMIT = 100
MAX_ROW_LIMIT = 10000
ALLOWED_TABLES = {
    "categories", "customers", "employees", "orderdetails",
    "orders", "products", "shippers", "suppliers",
}
FORBIDDEN_NODES = (
    exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Alter, exp.Create,
    exp.Command, exp.Merge, exp.Transaction, exp.Commit, exp.Rollback,
)


class PostgresSQLValidationError(ValueError):
    """Raised when SQL is not an allowed read-only PostgreSQL query."""


@dataclass(frozen=True)
class PostgresQueryResult:
    columns: list[str]
    rows: list[dict[str, Any]]


class PostgresSafetyValidator:
    def __init__(
        self,
        connection_factory=None,
        default_limit: int = DEFAULT_ROW_LIMIT,
        max_limit: int = MAX_ROW_LIMIT,
        statement_timeout_ms: int = 10000,
    ):
        if not (1 <= default_limit <= max_limit <= MAX_ROW_LIMIT):
            raise ValueError("Limits must satisfy 1 <= default_limit <= max_limit <= 1000.")
        if not (100 <= statement_timeout_ms <= 60000):
            raise ValueError("Statement timeout must be between 100 and 60000 ms.")
        self.connection_factory = connection_factory or self._connect
        self.default_limit = default_limit
        self.max_limit = max_limit
        self.statement_timeout_ms = statement_timeout_ms

    @staticmethod
    def _connect():
        # Do not log or include the connection URL in raised errors.
        from src.generator.sql_generator import load_env_file
        load_env_file()
        url = os.environ.get("NEONDB_URL") or os.environ.get("DATABASE_URL")
        if not url:
            raise RuntimeError("NEONDB_URL or DATABASE_URL is not configured.")
        return psycopg2.connect(url, connect_timeout=5)

    def describe_live_schema(self) -> str:
        """Read columns and foreign keys for approved public tables from Neon."""
        connection = None
        cursor = None
        try:
            connection = self.connection_factory()
            connection.autocommit = False
            cursor = connection.cursor()
            cursor.execute("SET TRANSACTION READ ONLY")
            cursor.execute("SET LOCAL statement_timeout = %s", (self.statement_timeout_ms,))
            cursor.execute(
                """
                SELECT table_name, column_name, data_type, udt_name
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = ANY(%s)
                ORDER BY table_name, ordinal_position
                """,
                (sorted(ALLOWED_TABLES),),
            )
            column_rows = cursor.fetchall()
            cursor.execute(
                """
                SELECT tc.table_name, kcu.column_name, ccu.table_name, ccu.column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_catalog = kcu.constraint_catalog
                 AND tc.constraint_schema = kcu.constraint_schema
                 AND tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_catalog = tc.constraint_catalog
                 AND ccu.constraint_schema = tc.constraint_schema
                 AND ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_schema = 'public'
                  AND tc.table_name = ANY(%s)
                ORDER BY tc.table_name, kcu.column_name
                """,
                (sorted(ALLOWED_TABLES),),
            )
            foreign_keys = cursor.fetchall()
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    pass
            if connection is not None:
                try:
                    connection.rollback()
                except Exception:
                    pass
                finally:
                    connection.close()

        if not column_rows:
            raise RuntimeError("No approved tables were found in the live public schema.")

        by_table: dict[str, list[str]] = {}
        for table, column, data_type, _udt_name in column_rows:
            by_table.setdefault(table, []).append(f"{column} {data_type}")
        lines = [
            f"- public.{table}({', '.join(columns)})"
            for table, columns in sorted(by_table.items())
        ]
        if foreign_keys:
            lines.append("RELATIONSHIPS:")
            lines.extend(
                f"- public.{table}.{column} = public.{foreign_table}.{foreign_column}"
                for table, column, foreign_table, foreign_column in foreign_keys
            )
        return "\n".join(lines)

    def validate(
    self,
    raw_sql: str,
    *,
    require_complete: bool = False,
) -> str:
        if not isinstance(raw_sql, str) or not raw_sql.strip():
            raise PostgresSQLValidationError("SQL query is empty.")
        # Reject multiple statements, including trailing semicolon.
        try:
            parsed = sqlglot.parse(raw_sql, read="postgres")
        except Exception as exc:
            raise PostgresSQLValidationError("SQL is not valid PostgreSQL syntax.") from exc
        statements = [item for item in parsed if item is not None]
        if len(statements) != 1:
            raise PostgresSQLValidationError("Exactly one SQL statement is required.")
        tree = statements[0]
        if not isinstance(tree, (exp.Select, exp.Union, exp.Intersect, exp.Except)):
            raise PostgresSQLValidationError("Only read-only SELECT queries are permitted.")
        for node in tree.walk():
            if isinstance(node, FORBIDDEN_NODES):
                raise PostgresSQLValidationError("Unsafe SQL operation is not permitted.")
            if isinstance(node, exp.Func):
                name = node.sql_name().upper()
                if name in {"PG_READ_FILE", "PG_WRITE_FILE", "PG_LS_DIR", "LO_IMPORT", "LO_EXPORT"}:
                    raise PostgresSQLValidationError("Restricted PostgreSQL function is not permitted.")
            if isinstance(node, exp.Table):
                table = node.name.lower()
                schema = (node.db or "public").lower()
                if schema != "public" or table not in ALLOWED_TABLES:
                    raise PostgresSQLValidationError("Query references a table outside the approved schema.")
        # Refuse SELECT INTO, which can create a table.
        if any(isinstance(node, exp.Into) for node in tree.walk()):
            raise PostgresSQLValidationError("SELECT INTO is not permitted.")

        # Validate any supplied limit before applying completeness policy.
        limit = tree.args.get("limit")
        if limit is not None:
            value = None
            expr = limit.expression
            if isinstance(expr, exp.Literal) and not expr.is_string:
                try:
                    value = int(expr.this)
                except (TypeError, ValueError):
                    pass
            if value is None or value < 1 or value > self.max_limit:
                raise PostgresSQLValidationError(
                    f"LIMIT must be between 1 and {self.max_limit}."
                )
            if not require_complete:
                return tree.sql(dialect="postgres")

        if require_complete:
            # Remove only the outer limit. Nested query limits remain intact.
            tree.set("limit", None)
            tree = tree.limit(self.max_limit + 1)
        elif limit is None:
            tree = tree.limit(self.default_limit)

        return tree.sql(dialect="postgres")


    def execute(
        self,
        raw_sql: str,
        *,
        require_complete: bool = False,
    ) -> PostgresQueryResult:
        sql = self.validate(raw_sql, require_complete=require_complete)
        connection = None
        cursor = None
        try:
            connection = self.connection_factory()
            connection.autocommit = False
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SET TRANSACTION READ ONLY")
            cursor.execute("SET LOCAL statement_timeout = %s", (self.statement_timeout_ms,))
            # Ask PostgreSQL to resolve tables, columns, operators, and types before execution.
            cursor.execute("EXPLAIN " + sql)
            cursor.fetchall()
            cursor.execute(sql)
            rows = cursor.fetchmany(self.max_limit + 1)
            if len(rows) > self.max_limit:
                raise RuntimeError("Query returned more rows than the configured maximum.")
            columns = [desc.name for desc in cursor.description] if cursor.description else []
            return PostgresQueryResult(columns=columns, rows=[dict(row) for row in rows])
        except PostgresSQLValidationError:
            raise
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    pass
            if connection is not None:
                try:
                    connection.rollback()
                except Exception:
                    pass
                finally:
                    connection.close()
