"""
database_tool.py
================
Tool 3 of 4: Safe SQLite Database Query Tool (Day 4 - Session 2)

Design Best Practices Implemented:
1. Clear Naming: 'query_database' conveys exact database querying function.
2. Model-Facing Description:
   - Contains explicit table schemas (employees, orders, inventory).
   - Instructs the model to write standard SQL SELECT queries.
3. Read-Only Guardrails:
   - Forbids destructive queries (DROP, DELETE, UPDATE, ALTER, TRUNCATE, INSERT).
4. Error as Observation (Self-Correction Enabler):
   - SQLite syntax errors (e.g. misspelled keywords, bad column names) are captured
     and returned as observations with schema hints so the LLM can self-correct!
"""

import sqlite3
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

DB_FILE = Path(__file__).parent / "enterprise.db"

_FORBIDDEN_KEYWORDS = [
    "drop", "delete", "update", "insert", "alter", "truncate",
    "replace", "create", "attach", "detach", "grant", "revoke"
]


def _get_table_schema(conn: sqlite3.Connection, table_name: str) -> List[str]:
    """Retrieves column names for a given table."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    rows = cursor.fetchall()
    return [r[1] for r in rows]


def query_database(sql_query: str, db_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Executes a read-only SQL query against the enterprise SQLite database.

    Available Tables:
    1. employees (id, name, department, role, salary, email)
    2. orders (order_id, customer_name, product, quantity, total_amount, order_date, status)
    3. inventory (sku, product_name, stock_level, reorder_threshold, unit_price)

    Args:
        sql_query: The SQL SELECT statement to execute.
    """
    target_db = db_path or DB_FILE

    # 1. Argument Validation
    if not isinstance(sql_query, str) or not sql_query.strip():
        return {
            "status": "error",
            "error_type": "ValidationError",
            "message": "The 'sql_query' argument must be a non-empty SQL string.",
        }

    clean_query = sql_query.strip().rstrip(";")

    # 2. Read-Only Guardrail Enforcement
    # Tokenize first word
    words = re.findall(r"\b[A-Za-z]+\b", clean_query.lower())
    if not words:
        return {
            "status": "error",
            "error_type": "ValidationError",
            "message": "No valid SQL commands found in query.",
        }

    primary_command = words[0]
    if primary_command not in ("select", "pragma", "with", "explain"):
        return {
            "status": "error",
            "error_type": "PermissionDenied",
            "message": (
                f"Query rejected: Only read-only operations ('SELECT', 'PRAGMA', 'WITH') "
                f"are permitted. Detected modifying verb '{primary_command.upper()}'."
            ),
        }

    # Inspect for destructive embedded commands
    for word in words:
        if word in _FORBIDDEN_KEYWORDS:
            return {
                "status": "error",
                "error_type": "PermissionDenied",
                "message": f"Query contains forbidden mutation keyword '{word.upper()}'. Read-only access enforced.",
            }

    # 3. Database Connection & Safe Execution
    if not target_db.exists():
        return {
            "status": "error",
            "error_type": "DatabaseNotFoundError",
            "message": f"Database file '{target_db.name}' does not exist. Please run database_setup.py first.",
        }

    try:
        conn = sqlite3.connect(f"file:{target_db}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(clean_query)
        rows = cursor.fetchall()

        column_names = [col[0] for col in cursor.description] if cursor.description else []
        records = [dict(zip(column_names, [r[c] for c in column_names])) for r in rows]
        total_rows = len(records)

        conn.close()

        return {
            "status": "success",
            "sql_query": clean_query,
            "row_count": total_rows,
            "columns": column_names,
            "records": records[:50],  # Protect context window from massive dumps
            "is_truncated": total_rows > 50,
        }

    except sqlite3.OperationalError as e:
        err_msg = str(e)
        # Check if error mentions a missing column or table and provide schema hints
        schema_hint: Optional[Dict[str, List[str]]] = None
        try:
            diag_conn = sqlite3.connect(f"file:{target_db}?mode=ro", uri=True)
            schema_hint = {
                "employees": _get_table_schema(diag_conn, "employees"),
                "orders": _get_table_schema(diag_conn, "orders"),
                "inventory": _get_table_schema(diag_conn, "inventory"),
            }
            diag_conn.close()
        except Exception:
            pass

        return {
            "status": "error",
            "error_type": "OperationalError",
            "message": f"SQLite execution failed: {err_msg}",
            "schema_reference": schema_hint,
            "hint": "Check table and column names against the schema_reference and self-correct your SQL query.",
        }
    except Exception as e:
        return {
            "status": "error",
            "error_type": "DatabaseError",
            "message": f"Unexpected database error: {str(e)}",
        }


if __name__ == "__main__":
    print("=== Testing query_database Tool ===")

    # 1. Valid Query
    res_valid = query_database("SELECT name, department, role, salary FROM employees WHERE salary > 140000")
    print("Valid SELECT:", res_valid["status"], f"({res_valid.get('row_count')} rows)")
    for rec in res_valid.get("records", []):
        print(f"  - {rec['name']} ({rec['department']}): ${rec['salary']:,}")

    # 2. Syntax/Column Error with Self-Correction Hint Observation
    res_err = query_database("SELECT full_name, pay FROM employees")
    print("\nColumn Error (Observation):", res_err["error_type"], "-", res_err["message"])
    print("Self-Correction Hint Columns:", res_err.get("schema_reference", {}).get("employees"))

    # 3. Forbidden Mutation Block
    res_blocked = query_database("DROP TABLE employees")
    print("\nDestructive Block (Observation):", res_blocked["error_type"], "-", res_blocked["message"])
