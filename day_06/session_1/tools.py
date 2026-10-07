"""
Day 6 - Session 1: How Tool Calling Works
Module: tools.py

Description:
    Implements the two required local tools:
    1. calculator: Safe AST-based mathematical expression evaluator (zero eval() vulnerability).
    2. get_time: Real-world time retriever supporting worldwide IANA timezones.

    Also provides a central dispatcher that safely routes tool requests to implementations
    and formats responses as structured observations.
"""

from __future__ import annotations
import ast
import operator
from datetime import datetime
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# Allowed operators for safe AST evaluation
_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval_ast_node(node: ast.AST) -> float:
    """Recursively evaluates an AST node safely without calling eval()."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise ValueError(f"Unsupported constant type: {type(node.value).__name__}")

    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_OPERATORS:
            raise ValueError(f"Forbidden or unsupported operator: {op_type.__name__}")
        left = _eval_ast_node(node.left)
        right = _eval_ast_node(node.right)
        
        # Division by zero protection
        if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right == 0:
            raise ZeroDivisionError("Division or modulo by zero is not permitted.")
        
        # Prevent computational explosion on huge exponents
        if op_type == ast.Pow and (right > 100 or left > 10000):
            raise OverflowError("Exponentiation exceeds safe magnitude limits (base <= 10000, exponent <= 100).")

        return _ALLOWED_OPERATORS[op_type](left, right)

    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_OPERATORS:
            raise ValueError(f"Forbidden unary operator: {op_type.__name__}")
        operand = _eval_ast_node(node.operand)
        return _ALLOWED_OPERATORS[op_type](operand)

    else:
        raise ValueError(f"Unsupported AST node expression: {type(node).__name__}")


def calculator(expression: str) -> Dict[str, Any]:
    """
    Evaluates a mathematical expression safely using an Abstract Syntax Tree (AST).

    Args:
        expression: Mathematical expression string, e.g. "45 * 12 + 180 / 3" or "(2500 - 450) * 1.08".

    Returns:
        Structured result dictionary with status, evaluated value, and original expression.
    """
    if not isinstance(expression, str) or not expression.strip():
        return {
            "status": "error",
            "error_type": "InvalidInput",
            "message": "Mathematical expression must be a non-empty string."
        }

    clean_expr = expression.strip().replace("×", "*").replace("÷", "/")

    try:
        parsed_ast = ast.parse(clean_expr, mode="eval")
        result = _eval_ast_node(parsed_ast.body)
        
        # Return integer if mathematically identical (e.g. 12.0 -> 12)
        if result.is_integer():
            final_result = int(result)
        else:
            final_result = round(result, 6)

        return {
            "status": "success",
            "expression": expression,
            "result": final_result
        }
    except ZeroDivisionError as zde:
        return {
            "status": "error",
            "error_type": "ZeroDivisionError",
            "message": str(zde)
        }
    except (ValueError, SyntaxError, OverflowError) as pe:
        return {
            "status": "error",
            "error_type": type(pe).__name__,
            "message": f"Failed to evaluate expression '{expression}': {str(pe)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_type": "UnexpectedEvaluationError",
            "message": f"Calculation error: {str(e)}"
        }


def get_time(timezone: str = "UTC") -> Dict[str, Any]:
    """
    Retrieves the current date and time for a specified IANA timezone.

    Args:
        timezone: IANA timezone string (e.g. 'UTC', 'Asia/Kolkata', 'America/New_York',
                  'Europe/London', 'Asia/Tokyo', 'Australia/Sydney'). Defaults to 'UTC'.

    Returns:
        Structured dictionary containing ISO timestamp, formatted strings, and timezone info.
    """
    if not isinstance(timezone, str) or not timezone.strip():
        timezone = "UTC"
    
    clean_tz = timezone.strip()

    # Common aliases mapping
    tz_aliases = {
        "ist": "Asia/Kolkata",
        "india": "Asia/Kolkata",
        "est": "America/New_York",
        "edt": "America/New_York",
        "pst": "America/Los_Angeles",
        "pdt": "America/Los_Angeles",
        "gmt": "UTC",
        "bst": "Europe/London",
        "tokyo": "Asia/Tokyo",
        "japan": "Asia/Tokyo"
    }

    resolved_tz_str = tz_aliases.get(clean_tz.lower(), clean_tz)

    try:
        tz_obj = ZoneInfo(resolved_tz_str)
        now = datetime.now(tz_obj)

        return {
            "status": "success",
            "requested_timezone": timezone,
            "resolved_timezone": resolved_tz_str,
            "iso_timestamp": now.isoformat(),
            "formatted_datetime": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "date": now.strftime("%Y-%m-%d"),
            "time_12hr": now.strftime("%I:%M:%S %p"),
            "time_24hr": now.strftime("%H:%M:%S"),
            "day_of_week": now.strftime("%A"),
            "utc_offset": now.strftime("%z")
        }
    except ZoneInfoNotFoundError:
        return {
            "status": "error",
            "error_type": "ZoneInfoNotFoundError",
            "message": f"Timezone '{timezone}' was not recognized. Please provide a standard IANA timezone name (e.g. 'UTC', 'America/New_York', 'Asia/Kolkata', 'Europe/London', 'Asia/Tokyo')."
        }
    except Exception as e:
        return {
            "status": "error",
            "error_type": "TimeRetrievalError",
            "message": f"Failed to retrieve time for '{timezone}': {str(e)}"
        }


def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Safely routes a requested tool name and argument dictionary to the corresponding implementation.

    Args:
        tool_name: Name of the tool requested by the model.
        arguments: Validated dictionary of arguments parsed from model output.

    Returns:
        Structured observation dictionary ready to return to model.
    """
    if tool_name == "calculator":
        expr = arguments.get("expression", "")
        return calculator(expression=expr)
    elif tool_name == "get_time":
        tz = arguments.get("timezone", "UTC")
        return get_time(timezone=tz)
    else:
        return {
            "status": "error",
            "error_type": "ToolNotFound",
            "message": f"Tool '{tool_name}' is not registered on this client. Available tools: ['calculator', 'get_time']."
        }
