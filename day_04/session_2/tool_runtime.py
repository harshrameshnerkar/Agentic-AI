"""
tool_runtime.py
===============
Safe Tool Execution Dispatcher (Day 4 - Session 2)

Responsibilities:
1. Tool Dispatch: Routes requested tool calls to the matching Python implementation.
2. Error as Observation Principle:
   - CRITICAL AGENTIC RULE: Never crash the runtime or throw raw exceptions to the LLM.
   - Any runtime failure, validation mismatch, syntax error, or missing file is caught
     and returned as a structured observation:
     `{"status": "error", "error_type": "...", "message": "...", "suggestion": "..."}`
   - This empowers the agent to inspect the error, self-correct its query, and retry!
"""

import json
from typing import Dict, Any, Callable

from web_search_tool import web_search
from file_reader_tool import read_file
from database_tool import query_database
from email_tool import send_email

TOOL_MAP: Dict[str, Callable[..., Dict[str, Any]]] = {
    "web_search": web_search,
    "read_file": read_file,
    "query_database": query_database,
    "send_email": send_email,
}


def dispatch_tool(name: str, arguments: Dict[str, Any]) -> str:
    """
    Safely executes a tool by name with arguments and serializes the result into JSON.
    Errors are captured and returned as informative observations.
    """
    if name not in TOOL_MAP:
        error_observation = {
            "status": "error",
            "error_type": "UnknownToolError",
            "message": f"Tool '{name}' is not recognized.",
            "available_tools": list(TOOL_MAP.keys()),
            "suggestion": "Please choose from the registered tools: web_search, read_file, query_database, send_email.",
        }
        return json.dumps(error_observation)

    tool_fn = TOOL_MAP[name]
    try:
        # Execute the tool
        result_dict = tool_fn(**arguments)
        return json.dumps(result_dict)
    except TypeError as e:
        # Parameter mismatch (e.g. wrong argument names)
        error_observation = {
            "status": "error",
            "error_type": "ArgumentSignatureError",
            "message": f"Tool parameter mismatch: {str(e)}",
            "provided_arguments": arguments,
            "suggestion": "Check the tool parameter schema and ensure all required arguments are supplied.",
        }
        return json.dumps(error_observation)
    except Exception as e:
        # General unhandled exception
        error_observation = {
            "status": "error",
            "error_type": "RuntimeExecutionError",
            "message": f"Execution of tool '{name}' failed unexpectedly: {str(e)}",
        }
        return json.dumps(error_observation)


if __name__ == "__main__":
    print("=== Testing Safe Tool Runtime Dispatcher ===")

    # 1. Successful Web Search
    out1 = dispatch_tool("web_search", {"query": "PostgreSQL 16 logical replication"})
    print("1. web_search dispatch:", json.loads(out1)["status"])

    # 2. Successful Database Query
    out2 = dispatch_tool("query_database", {"sql_query": "SELECT count(*) as count FROM employees"})
    print("2. query_database dispatch:", json.loads(out2)["records"])

    # 3. Successful File Read
    out3 = dispatch_tool("read_file", {"file_path": "requirements.txt"})
    print("3. read_file dispatch:", json.loads(out3)["status"], f"({json.loads(out3)['lines_returned']} lines)")

    # 4. Unknown Tool (Error as Observation)
    out_err = dispatch_tool("hack_mainframe", {})
    print("4. Unknown Tool Error Observation:", json.loads(out_err)["error_type"], "-", json.loads(out_err)["message"])
