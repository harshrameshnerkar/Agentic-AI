"""
Day 4 - Session 4: Model Context Protocol (MCP) Server
Module: filesystem_mcp_server.py

Description:
    A standardized Model Context Protocol (MCP) Server implementing:
    - 3 Tools: list_directory, read_file, get_file_info
    - 2 Resources: resource://policy/company_policy, resource://system/server_status
    - 1 Prompt Template: review_operations_policy

    Supports both:
    1. Direct in-memory connection via FastMCP / MCPServer Client(app).
    2. Subprocess stdio transport for JSON-RPC 2.0 communication over standard input/output.
"""

from __future__ import annotations
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List

from mcp.server.mcpserver import MCPServer

# Base directory for server file operations (isolated sandbox)
BASE_DIR = Path(__file__).resolve().parent / "server_data"
BASE_DIR.mkdir(parents=True, exist_ok=True)

# Initialize MCP Server
server = MCPServer(
    name="enterprise-filesystem-mcp-server",
    version="1.0.0",
    description="Enterprise Filesystem MCP Server providing standardized tools and resources"
)


def _resolve_safe_path(target_rel_path: str) -> Path:
    """
    Resolves relative path against BASE_DIR and prevents directory traversal attacks.
    """
    clean_path = (BASE_DIR / target_rel_path).resolve()
    if not str(clean_path).startswith(str(BASE_DIR)):
        raise PermissionError(f"Access Denied: Path '{target_rel_path}' attempts to traverse outside '{BASE_DIR.name}'.")
    return clean_path


# ============================================================================
# MCP PRIMITIVE 1: TOOLS (Executable routines for the LLM)
# ============================================================================

@server.tool(
    name="list_directory",
    description="List all files and subdirectories located within the managed server filesystem sandbox."
)
def list_directory(sub_dir: str = ".") -> List[Dict[str, Any]]:
    """
    Args:
        sub_dir: Relative subdirectory inside the server workspace (defaults to root '.')

    Returns:
        A list of file and directory objects with metadata.
    """
    try:
        target_dir = _resolve_safe_path(sub_dir)
        if not target_dir.exists():
            return [{"error": f"Directory not found: '{sub_dir}'"}]
        if not target_dir.is_dir():
            return [{"error": f"Path is not a directory: '{sub_dir}'"}]

        entries = []
        for entry in sorted(target_dir.iterdir()):
            stat = entry.stat()
            entries.append({
                "name": entry.name,
                "type": "directory" if entry.is_dir() else "file",
                "size_bytes": stat.st_size if entry.is_file() else None,
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        return entries
    except Exception as e:
        return [{"error": f"Failed to list directory '{sub_dir}': {str(e)}"}]


@server.tool(
    name="read_file",
    description="Read the complete text content of a specified file from the managed server filesystem."
)
def read_file(file_name: str) -> str:
    """
    Args:
        file_name: The relative file path to read (e.g. 'company_policy.md', 'server_status.json')

    Returns:
        The text content of the file or a descriptive error message.
    """
    try:
        target_file = _resolve_safe_path(file_name)
        if not target_file.exists():
            return f"Error: File '{file_name}' does not exist in the server repository."
        if not target_file.is_file():
            return f"Error: Path '{file_name}' is a directory, not a file."

        content = target_file.read_text(encoding="utf-8")
        return content
    except Exception as e:
        return f"Error reading file '{file_name}': {str(e)}"


@server.tool(
    name="get_file_info",
    description="Retrieve structural metadata for a file including size, line count, character count, and extension."
)
def get_file_info(file_name: str) -> Dict[str, Any]:
    """
    Args:
        file_name: Relative file path to inspect

    Returns:
        Metadata dictionary with size, lines, characters, extension, and timestamp.
    """
    try:
        target_file = _resolve_safe_path(file_name)
        if not target_file.exists():
            return {"error": f"File '{file_name}' does not exist."}
        if not target_file.is_file():
            return {"error": f"Path '{file_name}' is not a file."}

        content = target_file.read_text(encoding="utf-8")
        stat = target_file.stat()
        lines = content.splitlines()

        return {
            "file_name": target_file.name,
            "extension": target_file.suffix,
            "size_bytes": stat.st_size,
            "line_count": len(lines),
            "char_count": len(content),
            "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
        }
    except Exception as e:
        return {"error": f"Failed to inspect file '{file_name}': {str(e)}"}


# ============================================================================
# MCP PRIMITIVE 2: RESOURCES (Application-controlled contextual data by URI)
# ============================================================================

@server.resource(
    uri="resource://policy/company_policy",
    name="Company Operations Policy",
    description="Official enterprise policy on travel reimbursement and security compliance"
)
def get_company_policy_resource() -> str:
    """Returns the company policy text directly as an MCP Resource."""
    policy_file = BASE_DIR / "company_policy.md"
    if policy_file.exists():
        return policy_file.read_text(encoding="utf-8")
    return "Company policy document not currently available."


@server.resource(
    uri="resource://system/server_status",
    name="Cluster Server Status",
    description="Current health and latency metrics for production cluster services"
)
def get_server_status_resource() -> str:
    """Returns the cluster status JSON directly as an MCP Resource."""
    status_file = BASE_DIR / "server_status.json"
    if status_file.exists():
        return status_file.read_text(encoding="utf-8")
    return "Server status document not currently available."


# ============================================================================
# MCP PRIMITIVE 3: PROMPTS (Reusable prompt templates for common user tasks)
# ============================================================================

@server.prompt(
    name="review_operations_policy",
    description="Predefined prompt template to audit compliance against corporate policies"
)
def review_operations_policy(policy_focus: str = "travel and security") -> str:
    """Returns a standardized instruction prompt."""
    return (
        f"You are an enterprise compliance auditor. Review our company policies specifically "
        f"focusing on '{policy_focus}'. Cite the exact document reference, list all reimbursement "
        f"ceilings, and summarize security credential rotation mandates."
    )


# ============================================================================
# STDIO SERVER RUNNER (JSON-RPC over standard I/O)
# ============================================================================

if __name__ == "__main__":
    # When launched directly via subprocess command, run the stdio JSON-RPC transport loop
    server.run(transport="stdio")
