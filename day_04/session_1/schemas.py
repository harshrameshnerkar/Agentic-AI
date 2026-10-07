"""
schemas.py
==========
JSON Schema Definitions for Function / Tool Calling (Day 4 - Session 1)

Responsibilities:
1. Define official OpenAI / Gemini compliant tool specifications using JSON Schema.
2. Provide strict property type definitions, required parameter lists, and semantic descriptions.
3. Expose utilities to inspect and format schemas for model invocation.

How the Model Reads Tool Schemas:
- The API translates each tool's JSON schema into a structured prompt header sent to the model.
- The model's attention mechanism analyzes the `description` to decide relevance, and the
  `parameters` schema to construct valid JSON matching the required types.
"""

from typing import List, Dict, Any
import json


# ---------------------------------------------------------------------------
# 1. Calculator Tool Schema
# ---------------------------------------------------------------------------

CALCULATOR_TOOL: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": (
            "Evaluates a mathematical or arithmetic expression accurately. "
            "Use this tool whenever the user asks to calculate, compute, multiply, divide, "
            "add, subtract, compute percentages, square roots (sqrt), powers, or solve math equations. "
            "Never guess arithmetic when this tool is available."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": (
                        "The mathematical expression to evaluate, such as '345 * 28', "
                        "'sqrt(144) + 15', '45000 / 12 * 1.15', or '(250 - 45) * 1.08'."
                    ),
                }
            },
            "required": ["expression"],
            "additionalProperties": False,
        },
    },
}


# ---------------------------------------------------------------------------
# 2. Get Current Time Tool Schema
# ---------------------------------------------------------------------------

GET_CURRENT_TIME_TOOL: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_current_time",
        "description": (
            "Retrieves the live, real-time date and time for a given timezone. "
            "Use this tool whenever the user asks for the current time, current date, "
            "day of the week, or time across different cities/timezones (e.g. UTC, IST, EST, PST). "
            "The model has no internal clock, so this tool is required for any real-time temporal question."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": (
                        "The timezone code or identifier, e.g. 'UTC', 'IST', 'PST', 'EST', "
                        "'America/New_York', 'Asia/Kolkata', 'Europe/London'. "
                        "If the user does not specify a timezone, default to 'UTC'."
                    ),
                    "default": "UTC",
                }
            },
            "required": [],
            "additionalProperties": False,
        },
    },
}


# ---------------------------------------------------------------------------
# 3. Tool Collection & Inspection Helpers
# ---------------------------------------------------------------------------

ALL_TOOLS: List[Dict[str, Any]] = [
    CALCULATOR_TOOL,
    GET_CURRENT_TIME_TOOL,
]


def get_available_tools() -> List[Dict[str, Any]]:
    """Returns the list of tool definitions ready for chat completion calls."""
    return ALL_TOOLS


def get_tool_names() -> List[str]:
    """Returns the names of all registered tools."""
    return [t["function"]["name"] for t in ALL_TOOLS]


def format_schema_summary() -> str:
    """Formats an educational summary of the registered JSON schemas."""
    summary_lines = []
    for t in ALL_TOOLS:
        fn = t["function"]
        props = fn["parameters"]["properties"]
        req = fn["parameters"].get("required", [])
        
        summary_lines.append(f"Tool: '{fn['name']}'")
        summary_lines.append(f"  Description: {fn['description'][:90]}...")
        summary_lines.append("  Parameters:")
        for p_name, p_info in props.items():
            is_req = "(REQUIRED)" if p_name in req else "(OPTIONAL)"
            summary_lines.append(f"    - {p_name} [{p_info['type']}] {is_req}: {p_info['description'][:75]}...")
        summary_lines.append("")
    return "\n".join(summary_lines)


if __name__ == "__main__":
    print("=== Registered Tool JSON Schemas ===")
    print(format_schema_summary())
    print("\n=== Raw JSON Schema Example (Calculator) ===")
    print(json.dumps(CALCULATOR_TOOL, indent=2))
