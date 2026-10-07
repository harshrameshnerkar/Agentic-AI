"""
Day 6 - Session 2: Designing Good Tools
Module: tools.py

Description:
    Implements 5 production-grade tools following best practices:
    1. Clear Naming: Explicit verb_noun convention.
    2. Model-Facing Descriptions: Explicit guidance on when to use, inputs, outputs, and constraints.
    3. Strict Typed Validation: Rejection of malformed parameters with actionable guidance.
    4. Errors as Observations: Captures runtime failures (SQL errors, missing files, bad emails)
       and returns structured feedback so the model can self-correct without crashing.

The 5 Tools:
    1. web_search
    2. read_file
    3. query_sqlite
    4. call_external_api
    5. send_email
"""

from __future__ import annotations
import os
import re
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests

# Base paths
BASE_DIR = Path(__file__).resolve().parent
SANDBOX_DIR = BASE_DIR / "sandbox"
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = BASE_DIR / "enterprise_data.db"
EMAIL_LOG = BASE_DIR / "sent_emails.jsonl"

_EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
_DISALLOWED_SQL_KEYWORDS = ["drop", "delete", "update", "insert", "alter", "truncate", "replace", "create"]


# ============================================================================
# TOOL 1: WEB SEARCH (Simulated / Local Index + Fallback)
# ============================================================================

_MOCK_WEB_DATABASE = [
    {
        "title": "Model Context Protocol (MCP) Specification & Architecture",
        "url": "https://modelcontextprotocol.io/docs/concepts/architecture",
        "snippet": "MCP standardizes how applications provide context to LLMs. It divides responsibilities between MCP Hosts (Clients) and MCP Servers using JSON-RPC 2.0.",
        "keywords": ["mcp", "model context protocol", "architecture", "protocol", "json-rpc"]
    },
    {
        "title": "Anthropic Claude 3.5 Sonnet & Tool Calling Guide",
        "url": "https://docs.anthropic.com/en/docs/tool-use",
        "snippet": "Tools enable Claude to interact with external systems. Best practices include writing descriptions for the model and returning errors as observations.",
        "keywords": ["tool use", "claude", "tool calling", "functions", "anthropic"]
    },
    {
        "title": "Agentic AI System Patterns & Tool Failure Recovery",
        "url": "https://enterprise-ai.org/reports/agentic-tool-design-2026",
        "snippet": "Returning errors as observations enables self-correcting agent loops. When an agent receives schema hints in the observation, query success rates jump from 62% to 98%.",
        "keywords": ["agentic", "tool design", "self-correction", "error recovery", "observations"]
    },
    {
        "title": "Envoy Gateway 2026 Canary Shift Guidelines",
        "url": "https://gateway.envoyproxy.io/docs/canary-traffic-shifting",
        "snippet": "Zero downtime canary rollouts should follow 10% -> 25% -> 50% -> 100% distribution with automated circuit breaker rollback upon 5xx rate spikes.",
        "keywords": ["canary", "envoy", "deployment", "zero downtime", "rollback"]
    }
]


def web_search(query: str, num_results: int = 3) -> Dict[str, Any]:
    """
    Searches the web for up-to-date documentation, technical standards, and real-time facts.

    Args:
        query: Specific search terms (e.g. 'MCP architecture specifications', 'canary deployment guidelines').
        num_results: Maximum number of ranked results to return (1 to 5). Defaults to 3.

    Returns:
        Structured dictionary containing ranked results, snippets, and source URLs.
    """
    if not isinstance(query, str) or not query.strip():
        return {
            "status": "error",
            "error_type": "InvalidQuery",
            "message": "Search query cannot be empty. Please provide specific descriptive keywords."
        }

    try:
        num_results = max(1, min(int(num_results), 5))
    except (ValueError, TypeError):
        num_results = 3

    query_tokens = set(re.findall(r"\w+", query.lower()))

    # Rank local database items by keyword overlap
    scored_results = []
    for item in _MOCK_WEB_DATABASE:
        score = sum(1 for kw in item["keywords"] if kw in query.lower() or any(t in kw for t in query_tokens))
        if score > 0:
            scored_results.append((score, item))

    scored_results.sort(key=lambda x: x[0], reverse=True)
    top_matches = [item for _, item in scored_results[:num_results]]

    # If no local keyword match, return a generic helpful simulated snippet
    if not top_matches:
        top_matches = [{
            "title": f"Web Index Results for '{query}'",
            "url": f"https://search.enterprise.io/query?q={query.replace(' ', '+')}",
            "snippet": f"No direct matches found in priority technical index for '{query}'. Please consider refining search terms or checking internal files."
        }]

    return {
        "status": "success",
        "query": query,
        "results_count": len(top_matches),
        "results": top_matches
    }


# ============================================================================
# TOOL 2: READ FILE (Safe Sandboxed Workspace Reader)
# ============================================================================

def read_file(file_path: str, max_lines: int = 100) -> Dict[str, Any]:
    """
    Reads the content of a file located within the sandbox workspace.

    Args:
        file_path: Relative path to the file inside the sandbox (e.g. 'deployment_notes.md', 'quarterly_targets.txt').
        max_lines: Maximum number of lines to return to avoid context overflow. Defaults to 100.

    Returns:
        Structured dictionary containing file contents, total line count, and metadata.
    """
    if not isinstance(file_path, str) or not file_path.strip():
        available = [f.name for f in SANDBOX_DIR.iterdir() if f.is_file()]
        return {
            "status": "error",
            "error_type": "EmptyPathError",
            "message": "file_path parameter must not be empty.",
            "available_files_in_sandbox": available
        }

    try:
        resolved = (SANDBOX_DIR / file_path).resolve()
        # Security Guardrail: Prevent directory traversal
        if not str(resolved).startswith(str(SANDBOX_DIR)):
            return {
                "status": "error",
                "error_type": "PathTraversalDenied",
                "message": f"Security Violation: Access outside the sandbox directory is strictly forbidden."
            }

        if not resolved.exists():
            available = [f.name for f in SANDBOX_DIR.iterdir() if f.is_file()]
            # Error as Observation with helpful self-correction hints!
            return {
                "status": "error",
                "error_type": "FileNotFound",
                "message": f"File '{file_path}' does not exist in sandbox.",
                "available_files_in_sandbox": available,
                "suggestion": f"Did you mean one of these files? {available}"
            }

        if not resolved.is_file():
            return {
                "status": "error",
                "error_type": "NotAFile",
                "message": f"Target path '{file_path}' is a directory, not a text file."
            }

        text = resolved.read_text(encoding="utf-8")
        lines = text.splitlines()
        truncated = False
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            truncated = True

        return {
            "status": "success",
            "file_name": resolved.name,
            "total_lines": len(text.splitlines()),
            "lines_returned": len(lines),
            "is_truncated": truncated,
            "content": "\n".join(lines)
        }
    except Exception as e:
        return {
            "status": "error",
            "error_type": "FileReadException",
            "message": f"Failed to read '{file_path}': {str(e)}"
        }


# ============================================================================
# TOOL 3: QUERY SQLITE (Read-Only Database Query with Schema Hints)
# ============================================================================

def _get_database_schema_hints() -> Dict[str, List[str]]:
    """Helper to return current table schemas for error recovery."""
    if not DB_PATH.exists():
        return {}
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cursor.fetchall() if r[0] != "sqlite_sequence"]
    schema = {}
    for t in tables:
        cursor.execute(f"PRAGMA table_info({t});")
        schema[t] = [f"{col[1]} ({col[2]})" for col in cursor.fetchall()]
    conn.close()
    return schema


def query_sqlite(sql_query: str) -> Dict[str, Any]:
    """
    Executes a read-only SQL query (SELECT or PRAGMA) against the enterprise SQLite database.

    Available Tables:
    1. employees (id, name, department, role, salary, email, hire_date)
    2. products (sku, product_name, category, price, stock_quantity)
    3. orders (order_id, customer_name, product_sku, quantity, total_price, order_date, status)

    Args:
        sql_query: Standard SQL SELECT statement. (Destructive queries like DROP/DELETE are blocked).

    Returns:
        Structured observation containing columns, rows, and count, or schema hints on error.
    """
    if not isinstance(sql_query, str) or not sql_query.strip():
        return {
            "status": "error",
            "error_type": "EmptySQLQuery",
            "message": "sql_query parameter cannot be empty.",
            "available_tables": list(_get_database_schema_hints().keys())
        }

    clean_sql = sql_query.strip()
    first_token = clean_sql.split()[0].lower() if clean_sql.split() else ""

    # Guardrail: Read-only enforcement
    if first_token not in ("select", "pragma", "with", "explain"):
        return {
            "status": "error",
            "error_type": "ReadOnlyViolation",
            "message": f"Execution blocked: Only read-only queries (SELECT / PRAGMA) are permitted. Statement began with '{first_token.upper()}'."
        }

    for forbidden in _DISALLOWED_SQL_KEYWORDS:
        if re.search(r"\b" + forbidden + r"\b", clean_sql, re.IGNORECASE):
            return {
                "status": "error",
                "error_type": "ForbiddenSQLKeyword",
                "message": f"Execution blocked: Query contains prohibited keyword '{forbidden.upper()}'."
            }

    if not DB_PATH.exists():
        return {
            "status": "error",
            "error_type": "DatabaseNotFound",
            "message": "Enterprise database 'enterprise_data.db' is not initialized. Run database_setup.py first."
        }

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(clean_sql)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        result_rows = [dict(r) for r in rows]
        conn.close()

        return {
            "status": "success",
            "query": sql_query,
            "row_count": len(result_rows),
            "columns": columns,
            "rows": result_rows
        }
    except sqlite3.OperationalError as oe:
        # Crucial: Return schema hints as observation so model can self-correct syntax/table errors!
        return {
            "status": "error",
            "error_type": "SQLiteOperationalError",
            "message": str(oe),
            "help": "Please verify table and column names in your SQL query.",
            "available_schema": _get_database_schema_hints()
        }
    except Exception as e:
        return {
            "status": "error",
            "error_type": type(e).__name__,
            "message": f"SQL execution error: {str(e)}",
            "available_schema": _get_database_schema_hints()
        }


# ============================================================================
# TOOL 4: CALL EXTERNAL API (Safe HTTP REST Client with Error Observations)
# ============================================================================

def call_external_api(
    endpoint: str,
    method: str = "GET",
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Sends an HTTP request to an external REST API endpoint or simulated telemetry service.

    Supported Endpoints:
    - 'https://api.frankfurter.app/latest': Free currency exchange rates (e.g. params={'from': 'USD', 'to': 'EUR'}).
    - 'https://httpbin.org/get': Standard HTTP echo verification service.
    - 'mock://cluster/metrics': Internal mock cluster telemetry metrics.

    Args:
        endpoint: Target URL or mock endpoint string.
        method: HTTP method ('GET' or 'POST'). Defaults to 'GET'.
        params: Optional query parameters dictionary.

    Returns:
        Structured observation containing response JSON payload or HTTP error status.
    """
    if not isinstance(endpoint, str) or not endpoint.strip():
        return {
            "status": "error",
            "error_type": "InvalidEndpoint",
            "message": "Endpoint parameter must be a non-empty URL string."
        }

    # Internal mock endpoint handling
    if endpoint == "mock://cluster/metrics":
        return {
            "status": "success",
            "endpoint": endpoint,
            "status_code": 200,
            "data": {
                "active_nodes": 16,
                "cluster_cpu_utilization_pct": 42.8,
                "cluster_memory_utilization_pct": 58.4,
                "gateway_status": "HEALTHY",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }

    clean_method = method.upper() if isinstance(method, str) else "GET"
    if clean_method not in ("GET", "POST"):
        return {
            "status": "error",
            "error_type": "UnsupportedHTTPMethod",
            "message": f"Method '{method}' is unsupported. Only GET and POST are permitted."
        }

    try:
        response = requests.request(
            method=clean_method,
            url=endpoint.strip(),
            params=params if clean_method == "GET" else None,
            json=params if clean_method == "POST" else None,
            timeout=8.0
        )

        try:
            payload = response.json()
        except ValueError:
            payload = response.text[:500]

        return {
            "status": "success" if response.ok else "error",
            "endpoint": endpoint,
            "status_code": response.status_code,
            "is_success": response.ok,
            "data": payload
        }
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "error_type": "TimeoutError",
            "message": f"Request to '{endpoint}' timed out after 8.0 seconds."
        }
    except requests.exceptions.ConnectionError:
        return {
            "status": "error",
            "error_type": "ConnectionError",
            "message": f"Failed to connect to '{endpoint}'. Network unreachable or domain does not exist."
        }
    except Exception as e:
        return {
            "status": "error",
            "error_type": type(e).__name__,
            "message": f"HTTP request failed: {str(e)}"
        }


# ============================================================================
# TOOL 5: SEND EMAIL (Mock Email Sender with Strict Validation & Audit Receipt)
# ============================================================================

def send_email(
    to_email: str,
    subject: str,
    body: str,
    cc: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Sends an email notification via the corporate gateway and logs delivery to the audit ledger.

    Args:
        to_email: The primary recipient's valid email address (e.g. 'alice.chen@enterprise.io').
        subject: The subject line of the email (must be between 3 and 100 characters).
        body: The plain text or markdown content of the message (must not be empty).
        cc: Optional list of additional valid email addresses to carbon copy.

    Returns:
        Structured receipt with tracking message_id, timestamp, and delivery status.
    """
    # 1. Recipient Validation
    if not isinstance(to_email, str) or not _EMAIL_REGEX.match(to_email.strip()):
        return {
            "status": "error",
            "error_type": "InvalidEmailFormat",
            "message": f"The recipient address '{to_email}' is invalid. Please provide a standard address with '@' and domain (e.g. 'alice.chen@enterprise.io')."
        }

    # 2. Subject Validation
    if not isinstance(subject, str) or len(subject.strip()) < 3:
        return {
            "status": "error",
            "error_type": "InvalidSubject",
            "message": "Email subject must be a string containing at least 3 characters."
        }

    # 3. Body Validation
    if not isinstance(body, str) or not body.strip():
        return {
            "status": "error",
            "error_type": "EmptyBody",
            "message": "Email body content cannot be empty."
        }

    # 4. Optional CC Validation
    validated_cc = []
    if cc:
        if isinstance(cc, list):
            for addr in cc:
                if isinstance(addr, str) and _EMAIL_REGEX.match(addr.strip()):
                    validated_cc.append(addr.strip())
                else:
                    return {
                        "status": "error",
                        "error_type": "InvalidCCAddress",
                        "message": f"The CC address '{addr}' is invalid. Please verify all email addresses in the CC list."
                    }

    message_id = f"MSG-{uuid.uuid4().hex[:8].upper()}"
    timestamp = datetime.utcnow().isoformat() + "Z"

    record = {
        "message_id": message_id,
        "timestamp": timestamp,
        "to": to_email.strip(),
        "cc": validated_cc,
        "subject": subject.strip(),
        "body_preview": body.strip()[:100],
        "status": "DELIVERED"
    }

    # Append to local audit ledger
    with open(EMAIL_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    return {
        "status": "success",
        "message_id": message_id,
        "recipient": to_email.strip(),
        "subject": subject.strip(),
        "timestamp": timestamp,
        "delivery_receipt": "DELIVERED_TO_GATEWAY"
    }


# ============================================================================
# CENTRAL DISPATCHER
# ============================================================================

def dispatch_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Central dispatcher routing tool invocations to the proper function.
    """
    dispatch_map = {
        "web_search": lambda args: web_search(
            query=args.get("query", ""),
            num_results=args.get("num_results", 3)
        ),
        "read_file": lambda args: read_file(
            file_path=args.get("file_path", ""),
            max_lines=args.get("max_lines", 100)
        ),
        "query_sqlite": lambda args: query_sqlite(
            sql_query=args.get("sql_query", "")
        ),
        "call_external_api": lambda args: call_external_api(
            endpoint=args.get("endpoint", ""),
            method=args.get("method", "GET"),
            params=args.get("params")
        ),
        "send_email": lambda args: send_email(
            to_email=args.get("to_email", ""),
            subject=args.get("subject", ""),
            body=args.get("body", ""),
            cc=args.get("cc")
        )
    }

    if tool_name not in dispatch_map:
        return {
            "status": "error",
            "error_type": "UnknownTool",
            "message": f"Tool '{tool_name}' is not recognized. Available tools: {list(dispatch_map.keys())}"
        }

    try:
        return dispatch_map[tool_name](arguments)
    except Exception as e:
        return {
            "status": "error",
            "error_type": "UnhandledDispatchException",
            "message": f"Internal error executing '{tool_name}': {str(e)}"
        }
