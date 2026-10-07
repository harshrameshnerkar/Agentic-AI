"""
tools.py
========
Tool implementations for Day 4 - Session 3: Multi-Step Tool Use.
Tools:
1. query_database: Read-only SQLite query engine.
2. read_file: Sandboxed file reader with pagination.
3. calculator: Arithmetic evaluation engine.
4. send_email: Validated mock email gateway with audit trail.
"""

import sqlite3
import re
import math
import json
import datetime
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional

WORKSPACE_DIR = Path(__file__).parent.resolve()
DB_FILE = WORKSPACE_DIR / "enterprise.db"
AUDIT_LOG_FILE = WORKSPACE_DIR / "sent_emails.jsonl"

_EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


# ---------------------------------------------------------------------------
# Tool 1: query_database
# ---------------------------------------------------------------------------
def query_database(sql_query: str) -> Dict[str, Any]:
    """
    Executes a read-only SQL query against the enterprise SQLite database.

    Tables available:
    - employees (id, name, department, role, salary, email)
    - departments (dept_name, head_of_department, headcount, quarterly_budget)
    - payroll_audit (id, employee_name, bonus_amount, status, created_at)
    """
    if not isinstance(sql_query, str) or not sql_query.strip():
        return {
            "status": "error",
            "error_type": "ValidationError",
            "message": "The 'sql_query' argument must be a non-empty SQL string."
        }

    # Guardrails: Read-only check
    clean_sql = sql_query.strip()
    first_token = clean_sql.split()[0].upper() if clean_sql.split() else ""
    if first_token not in ("SELECT", "PRAGMA", "WITH"):
        return {
            "status": "error",
            "error_type": "PermissionDenied",
            "message": f"Query rejected: Only read-only operations ('SELECT', 'PRAGMA', 'WITH') are permitted. Received '{first_token}'."
        }

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(clean_sql)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        conn.close()

        records = [dict(zip(columns, row)) for row in rows]
        return {
            "status": "success",
            "tool": "query_database",
            "sql_query": clean_sql,
            "row_count": len(records),
            "columns": columns,
            "records": records,
        }
    except Exception as e:
        return {
            "status": "error",
            "error_type": "OperationalError",
            "message": f"SQLite execution failed: {str(e)}",
            "schema_reference": {
                "employees": ["id", "name", "department", "role", "salary", "email"],
                "departments": ["dept_name", "head_of_department", "headcount", "quarterly_budget"],
                "payroll_audit": ["id", "employee_name", "bonus_amount", "status", "created_at"]
            },
            "hint": "Check table and column names against the schema_reference and self-correct your SQL query."
        }


# ---------------------------------------------------------------------------
# Tool 2: read_file
# ---------------------------------------------------------------------------
def read_file(file_path: str, start_line: int = 1, max_lines: int = 100) -> Dict[str, Any]:
    """
    Safely reads text content from a file within the authorized workspace.
    """
    if not isinstance(file_path, str) or not file_path.strip():
        return {
            "status": "error",
            "error_type": "ValidationError",
            "message": "The 'file_path' argument must be a non-empty string."
        }

    target = (WORKSPACE_DIR / file_path).resolve()
    # Sandbox boundary enforcement
    if not str(target).startswith(str(WORKSPACE_DIR)):
        return {
            "status": "error",
            "error_type": "SecurityError",
            "message": f"Access Denied: Path '{file_path}' resolves outside the allowed sandbox directory."
        }

    if not target.exists():
        available_files = [f.name for f in WORKSPACE_DIR.glob("*") if f.is_file()]
        return {
            "status": "error",
            "error_type": "FileNotFoundError",
            "message": f"File '{file_path}' was not found.",
            "available_files": available_files,
            "suggestion": "Check the available_files list to locate the correct file name."
        }

    try:
        with open(target, "r", encoding="utf-8") as f:
            lines = f.readlines()

        start_idx = max(1, int(start_line)) - 1
        num_lines = max(1, min(int(max_lines), 200))
        selected_lines = lines[start_idx : start_idx + num_lines]

        return {
            "status": "success",
            "tool": "read_file",
            "file_path": file_path,
            "start_line": start_idx + 1,
            "lines_returned": len(selected_lines),
            "total_lines": len(lines),
            "content": "".join(selected_lines),
        }
    except Exception as e:
        return {
            "status": "error",
            "error_type": "IOError",
            "message": f"Failed to read file '{file_path}': {str(e)}"
        }


# ---------------------------------------------------------------------------
# Tool 3: calculator
# ---------------------------------------------------------------------------
def calculator(expression: str) -> Dict[str, Any]:
    """
    Safely evaluates a mathematical expression using Python's arithmetic parser.
    """
    if not isinstance(expression, str) or not expression.strip():
        return {
            "status": "error",
            "error_type": "ValidationError",
            "message": "The 'expression' argument must be a non-empty mathematical string."
        }

    clean_expr = expression.strip().replace(",", "")
    # Allow numbers, basic operators, parentheses, and math functions
    allowed_chars = set("0123456789+-*/().% ")
    if not all(c in allowed_chars for c in clean_expr):
        return {
            "status": "error",
            "error_type": "SecurityError",
            "message": f"Expression contains invalid characters: '{clean_expr}'. Only basic arithmetic characters (+, -, *, /, %, ()) are permitted."
        }

    try:
        # Safe evaluation with restricted globals
        result = eval(clean_expr, {"__builtins__": None}, {})
        return {
            "status": "success",
            "tool": "calculator",
            "expression": clean_expr,
            "result": result,
            "formatted_result": f"{result:,.2f}" if isinstance(result, (int, float)) else str(result)
        }
    except Exception as e:
        return {
            "status": "error",
            "error_type": "EvaluationError",
            "message": f"Could not evaluate expression '{clean_expr}': {str(e)}",
            "hint": "Check the syntax of the mathematical expression (e.g. '135000 * 0.12')."
        }


# ---------------------------------------------------------------------------
# Tool 4: send_email
# ---------------------------------------------------------------------------
def send_email(to_email: str, subject: str, body: str) -> Dict[str, Any]:
    """
    Sends an official email message via the corporate mail gateway with audit tracking.
    """
    if not isinstance(to_email, str) or not _EMAIL_REGEX.match(to_email.strip()):
        return {
            "status": "error",
            "error_type": "InvalidEmailAddress",
            "message": f"The recipient address '{to_email}' is invalid. Please format as user@domain.com."
        }

    if not isinstance(subject, str) or not subject.strip():
        return {
            "status": "error",
            "error_type": "ValidationError",
            "message": "The 'subject' parameter must not be empty."
        }

    if not isinstance(body, str) or not body.strip():
        return {
            "status": "error",
            "error_type": "ValidationError",
            "message": "The 'body' parameter must not be empty."
        }

    message_id = f"MSG-{datetime.datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    timestamp_iso = datetime.datetime.utcnow().isoformat() + "Z"

    log_entry = {
        "message_id": message_id,
        "timestamp": timestamp_iso,
        "to_email": to_email.strip(),
        "subject": subject.strip(),
        "body": body.strip(),
        "status": "DELIVERED"
    }

    try:
        with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass

    return {
        "status": "success",
        "tool": "send_email",
        "message_id": message_id,
        "recipient": to_email.strip(),
        "subject": subject.strip(),
        "timestamp": timestamp_iso,
        "delivery_confirmation": f"Email successfully queued and delivered to {to_email.strip()}."
    }


# Tool Dispatch Registry
TOOL_REGISTRY: Dict[str, Any] = {
    "query_database": query_database,
    "read_file": read_file,
    "calculator": calculator,
    "send_email": send_email,
}


def dispatch_tool_call(name: str, arguments: Dict[str, Any]) -> str:
    """Dispatches a tool call safely, returning a JSON string observation."""
    if name not in TOOL_REGISTRY:
        error_obs = {
            "status": "error",
            "error_type": "UnknownToolError",
            "message": f"Tool '{name}' is not recognized.",
            "available_tools": list(TOOL_REGISTRY.keys())
        }
        return json.dumps(error_obs)

    fn = TOOL_REGISTRY[name]
    try:
        res = fn(**arguments)
        return json.dumps(res)
    except TypeError as e:
        error_obs = {
            "status": "error",
            "error_type": "ArgumentSignatureError",
            "message": f"Argument signature mismatch: {str(e)}",
            "provided_arguments": arguments
        }
        return json.dumps(error_obs)
    except Exception as e:
        error_obs = {
            "status": "error",
            "error_type": "ExecutionError",
            "message": f"Unexpected error during tool execution: {str(e)}"
        }
        return json.dumps(error_obs)
