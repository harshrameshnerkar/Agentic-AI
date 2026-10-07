"""
schemas.py
==========
JSON Schema Definitions for 4 Enterprise Tools (Day 4 - Session 2)

Key Guidelines for Writing Good Tool Schemas:
1. Naming:
   - Use clear, lower_case_with_underscores, imperative verb-noun names (e.g. 'web_search', 'read_file', 'query_database', 'send_email').
   - Avoid generic or ambiguous names like 'get_data', 'do_action', 'helper'.
2. Descriptions Written for the Model:
   - Specify *when* to call the tool and *when not* to call it.
   - For database queries: Include the table names and schemas right in the tool description so the model doesn't have to guess column names!
   - For file operations: Explicitly state path constraints (relative paths, text files only).
3. Typed and Validated Arguments:
   - Provide explicit types ('string', 'integer', 'array', 'boolean').
   - Provide field descriptions detailing formatting requirements (e.g. email syntax, SQL SELECT syntax).
   - Set 'required' arrays explicitly.
4. Keep Tool Count Small:
   - Don't create 20 micro-tools (e.g. 'search_python_docs', 'search_gemini_docs', 'search_postgres_docs').
   - Consolidate into 4 clean, robust capabilities: Web Search, File Reader, Database Query, Email Dispatcher.
"""

from typing import List, Dict, Any
import json

# ---------------------------------------------------------------------------
# 1. Web Search Tool Schema
# ---------------------------------------------------------------------------

WEB_SEARCH_SCHEMA: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "Searches the web for recent documentation, facts, external news, and current events. "
            "Use this tool whenever the user asks about current software releases (e.g. Python 3.12 features), "
            "external company websites, weather forecasts, market news, or questions requiring outside real-time knowledge. "
            "Do NOT use this tool for internal corporate database queries or reading local project files."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Specific search keywords or phrase, e.g. 'Python 3.12 release notes subinterpreters' or 'NYC current weather'.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of search results to return (between 1 and 10). Defaults to 3.",
                    "default": 3,
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
}

# ---------------------------------------------------------------------------
# 2. File Reader Tool Schema
# ---------------------------------------------------------------------------

READ_FILE_SCHEMA: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": (
            "Safely reads text content from a local file within the project workspace. "
            "Use this tool when you need to inspect source code, configuration files (.env, .json), "
            "markdown documents, or local text data. "
            "Supports pagination via 'start_line' and 'max_lines' to prevent token context overflow."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Relative path to the target file within the workspace (e.g. 'requirements.txt', 'schemas.py').",
                },
                "max_lines": {
                    "type": "integer",
                    "description": "Number of lines to read (1 to 500). Defaults to 150.",
                    "default": 150,
                },
                "start_line": {
                    "type": "integer",
                    "description": "The 1-indexed line number to start reading from. Defaults to 1.",
                    "default": 1,
                },
            },
            "required": ["file_path"],
            "additionalProperties": False,
        },
    },
}

# ---------------------------------------------------------------------------
# 3. Database Query Tool Schema
# ---------------------------------------------------------------------------

QUERY_DATABASE_SCHEMA: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "query_database",
        "description": (
            "Executes a read-only SQL query against the enterprise SQLite database. "
            "Use this tool to lookup internal employees, salary figures, order statuses, or inventory stock levels. "
            "\nAVAILABLE SCHEMAS:"
            "\n- employees (id, name, department, role, salary, email)"
            "\n- orders (order_id, customer_name, product, quantity, total_amount, order_date, status)"
            "\n- inventory (sku, product_name, stock_level, reorder_threshold, unit_price)"
            "\nRULES: Only SELECT and PRAGMA statements are permitted. Mutation queries (INSERT, UPDATE, DELETE, DROP) will be rejected."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "sql_query": {
                    "type": "string",
                    "description": "The valid SQL SELECT statement to execute, e.g. 'SELECT name, role, email FROM employees WHERE department = \"Engineering\"'.",
                }
            },
            "required": ["sql_query"],
            "additionalProperties": False,
        },
    },
}

# ---------------------------------------------------------------------------
# 4. Email Sender Tool Schema
# ---------------------------------------------------------------------------

SEND_EMAIL_SCHEMA: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "send_email",
        "description": (
            "Sends an email message via the corporate mail gateway. "
            "Use this tool whenever the user instructs you to send an email, notify a colleague, "
            "dispatch a report to a manager, or send confirmation to a customer. "
            "Returns a delivery confirmation receipt with an audit Message ID."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "to_email": {
                    "type": "string",
                    "description": "The primary recipient's valid email address (e.g. 'sarah.connor@enterprise.io'). Must be a valid email format.",
                },
                "subject": {
                    "type": "string",
                    "description": "The email subject line (e.g. 'Q3 Architecture Report Summary'). Must not be empty.",
                },
                "body": {
                    "type": "string",
                    "description": "The full body text of the email message.",
                },
                "cc": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of additional email addresses to carbon copy.",
                },
            },
            "required": ["to_email", "subject", "body"],
            "additionalProperties": False,
        },
    },
}


SESSION_2_TOOLS: List[Dict[str, Any]] = [
    WEB_SEARCH_SCHEMA,
    READ_FILE_SCHEMA,
    QUERY_DATABASE_SCHEMA,
    SEND_EMAIL_SCHEMA,
]


def get_all_tools() -> List[Dict[str, Any]]:
    """Returns the four production tool schemas."""
    return SESSION_2_TOOLS


if __name__ == "__main__":
    print(f"=== Registered {len(SESSION_2_TOOLS)} Production Tools ===")
    for t in SESSION_2_TOOLS:
        fn = t["function"]
        req = fn["parameters"].get("required", [])
        props = list(fn["parameters"]["properties"].keys())
        print(f"• Tool: {fn['name']:<16} | Params: {props} | Required: {req}")
