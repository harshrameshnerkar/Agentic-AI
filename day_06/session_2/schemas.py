"""
Day 6 - Session 2: Designing Good Tools
Module: schemas.py

Description:
    Defines model-facing JSON Schemas and Pydantic validation models for the 5 tools:
    1. web_search
    2. read_file
    3. query_sqlite
    4. call_external_api
    5. send_email

Key Pedagogical Design:
    - Descriptions are written specifically FOR THE MODEL, not for software developers.
    - Includes clear trigger conditions ("When to use this tool").
    - Explicitly sets boundaries ("Do NOT use this tool for...").
    - Provides concrete parameter examples.
    - Keeps the active tool count strictly under ~10 (exactly 5 tools) to optimize token
      efficiency and avoid tool selection confusion.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# ============================================================================
# 1. Pydantic Argument Models (Strict Typing & Auto-Validation)
# ============================================================================

class WebSearchInput(BaseModel):
    query: str = Field(
        ...,
        description="The technical or factual search query, e.g. 'Model Context Protocol architecture' or 'Envoy gateway canary shift'."
    )
    num_results: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Maximum number of ranked search results to return (between 1 and 5)."
    )


class ReadFileInput(BaseModel):
    file_path: str = Field(
        ...,
        description="The relative filename within the sandbox workspace, e.g. 'deployment_notes.md' or 'quarterly_targets.txt'."
    )
    max_lines: int = Field(
        default=100,
        ge=1,
        le=500,
        description="Maximum lines of content to read to avoid prompt overflow."
    )


class QuerySqliteInput(BaseModel):
    sql_query: str = Field(
        ...,
        description=(
            "The read-only SQL query to execute against the SQLite database. "
            "Must start with SELECT or PRAGMA. Example: 'SELECT name, department, salary FROM employees WHERE salary > 150000'."
        )
    )


class CallExternalApiInput(BaseModel):
    endpoint: str = Field(
        ...,
        description="Target REST URL or mock service endpoint, e.g. 'https://httpbin.org/get' or 'mock://cluster/metrics'."
    )
    method: str = Field(
        default="GET",
        pattern="^(GET|POST)$",
        description="HTTP method. Permitted values: 'GET' or 'POST'."
    )
    params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional dictionary of query parameters or POST body data."
    )


class SendEmailInput(BaseModel):
    to_email: str = Field(
        ...,
        pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
        description="Primary recipient email address with valid '@' and domain, e.g. 'alice.chen@enterprise.io'."
    )
    subject: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Subject line of the email message."
    )
    body: str = Field(
        ...,
        min_length=1,
        description="Full text or markdown content of the email notification."
    )
    cc: Optional[List[str]] = Field(
        default=None,
        description="Optional list of additional valid email addresses to carbon copy."
    )


# ============================================================================
# 2. Standard JSON Schemas Written For the Model
# ============================================================================

WEB_SEARCH_SCHEMA: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "Searches technical documentation, industry specifications, and real-time public web facts. "
            "WHEN TO USE: Call this tool when the user asks about external technologies, protocols (MCP, Envoy), "
            "or public knowledge not contained in local database tables or sandbox files. "
            "DO NOT USE: Do NOT use this tool to find internal employee salaries, internal product SKUs, "
            "or company deployment notes."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Specific search terms, e.g. 'MCP JSON-RPC specification' or 'Canary traffic shifting'."
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of ranked results (1 to 5). Defaults to 3.",
                    "default": 3
                }
            },
            "required": ["query"]
        }
    }
}

READ_FILE_SCHEMA: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": (
            "Reads the plain-text content of a documentation or operational file from the safe sandbox workspace. "
            "WHEN TO USE: Call this when inspecting local files such as 'deployment_notes.md' or 'quarterly_targets.txt'. "
            "FAILURE RECOVERY: If the file does not exist, the tool observation will list all available sandbox files "
            "so you can re-attempt with the correct filename."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Relative filename within sandbox, e.g. 'deployment_notes.md'."
                },
                "max_lines": {
                    "type": "integer",
                    "description": "Maximum lines to read. Defaults to 100.",
                    "default": 100
                }
            },
            "required": ["file_path"]
        }
    }
}

QUERY_SQLITE_SCHEMA: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "query_sqlite",
        "description": (
            "Executes a read-only SQL query against the enterprise SQLite database. "
            "AVAILABLE TABLES & COLUMNS:\n"
            "1. employees (id, name, department, role, salary, email, hire_date)\n"
            "2. products (sku, product_name, category, price, stock_quantity)\n"
            "3. orders (order_id, customer_name, product_sku, quantity, total_price, order_date, status)\n"
            "WHEN TO USE: Use this for retrieving employee compensation, product stock, and customer orders. "
            "CONSTRAINTS: Only SELECT or PRAGMA queries are allowed. Destructive queries (DROP/DELETE) are blocked. "
            "FAILURE RECOVERY: If a SQL syntax error occurs, the observation will return schema hints so you can self-correct."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "sql_query": {
                    "type": "string",
                    "description": "The SQL SELECT statement, e.g. 'SELECT name, role, salary FROM employees WHERE department = \"Engineering\"'."
                }
            },
            "required": ["sql_query"]
        }
    }
}

CALL_EXTERNAL_API_SCHEMA: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "call_external_api",
        "description": (
            "Performs an HTTP REST request to external web APIs or internal mock microservices. "
            "SUPPORTED ENDPOINTS:\n"
            "- 'mock://cluster/metrics': Real-time cluster CPU, memory, and gateway telemetry.\n"
            "- 'https://httpbin.org/get': General connectivity echo verification.\n"
            "WHEN TO USE: Call this when live cluster metrics or REST data are needed."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "endpoint": {
                    "type": "string",
                    "description": "Target REST URL or mock service endpoint."
                },
                "method": {
                    "type": "string",
                    "enum": ["GET", "POST"],
                    "description": "HTTP method to execute (defaults to 'GET').",
                    "default": "GET"
                },
                "params": {
                    "type": "object",
                    "description": "Optional dictionary of query parameters or JSON body."
                }
            },
            "required": ["endpoint"]
        }
    }
}

SEND_EMAIL_SCHEMA: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "send_email",
        "description": (
            "Sends an official notification email via the enterprise gateway and records an immutable audit receipt. "
            "WHEN TO USE: Call this only after gathering necessary data (from SQL or files) to report conclusions "
            "or alert team members. "
            "VALIDATION: 'to_email' must be a valid email format with domain (e.g. 'alice.chen@enterprise.io'). "
            "Subject must be between 3 and 100 characters. Body must not be empty."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "to_email": {
                    "type": "string",
                    "description": "Valid recipient email address, e.g. 'elena.rostova@enterprise.io'."
                },
                "subject": {
                    "type": "string",
                    "description": "Descriptive email subject line."
                },
                "body": {
                    "type": "string",
                    "description": "Complete text or markdown body of the message."
                },
                "cc": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of additional CC email addresses."
                }
            },
            "required": ["to_email", "subject", "body"]
        }
    }
}

# Master List of 5 Tools (Well under the recommended ~10 tool threshold)
DESIGNED_TOOLS: List[Dict[str, Any]] = [
    WEB_SEARCH_SCHEMA,
    READ_FILE_SCHEMA,
    QUERY_SQLITE_SCHEMA,
    CALL_EXTERNAL_API_SCHEMA,
    SEND_EMAIL_SCHEMA
]


def get_designed_tools() -> List[Dict[str, Any]]:
    """Returns the curated list of 5 production tools."""
    return DESIGNED_TOOLS
