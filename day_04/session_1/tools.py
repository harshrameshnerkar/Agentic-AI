"""
tools.py
========
Tool / Function Implementations (Day 4 - Session 1)

Responsibilities:
1. Pure Python function implementations:
   - calculator: Safe arithmetic and mathematical expression evaluation.
   - get_current_time: Real-time clock lookup supporting global timezones.
2. Tool Registry: Central mapping of tool names to callable Python functions.
3. Tool Execution Dispatcher: Safely parses parameters and executes local code.

Why the Model Never Runs Code Itself:
- An LLM is a probabilistic next-token generator. It has no CPU, memory sandbox,
  system clock, or API socket.
- It merely emits a structured JSON string requesting that the HOST APPLICATION
  (our Python code) run the function and supply the result back.
"""

import ast
import operator
import math
import datetime
import json
from typing import Dict, Any, Callable


# ---------------------------------------------------------------------------
# 1. Safe Calculator Tool
# ---------------------------------------------------------------------------

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

_ALLOWED_FUNCTIONS = {
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "floor": math.floor,
    "ceil": math.ceil,
    "round": round,
    "abs": abs,
}

_ALLOWED_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
}


def _safe_eval_node(node: ast.AST) -> float:
    """Recursively evaluates an AST node safely without using arbitrary eval()."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise ValueError(f"Unsupported constant type: {type(node.value)}")

    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type in _ALLOWED_OPERATORS:
            left = _safe_eval_node(node.left)
            right = _safe_eval_node(node.right)
            return _ALLOWED_OPERATORS[op_type](left, right)
        raise ValueError(f"Unsupported operator: {op_type}")

    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type in _ALLOWED_OPERATORS:
            operand = _safe_eval_node(node.operand)
            return _ALLOWED_OPERATORS[op_type](operand)
        raise ValueError(f"Unsupported unary operator: {op_type}")

    if isinstance(node, ast.Name):
        if node.id in _ALLOWED_CONSTANTS:
            return _ALLOWED_CONSTANTS[node.id]
        raise ValueError(f"Unknown variable or constant: {node.id}")

    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in _ALLOWED_FUNCTIONS:
            func = _ALLOWED_FUNCTIONS[node.func.id]
            args = [_safe_eval_node(arg) for arg in node.args]
            return float(func(*args))
        raise ValueError(f"Unsupported function call: {ast.dump(node)}")

    raise ValueError(f"Unsupported expression syntax: {ast.dump(node)}")


def calculator(expression: str) -> Dict[str, Any]:
    """
    Evaluates a mathematical expression and returns the exact numerical result.
    
    Args:
        expression: A valid mathematical string, e.g. '345 * 28', '(1200 + 450) / 5', 'sqrt(144)'.
    """
    # Clean expression
    expr_clean = expression.strip().replace("^", "**")
    try:
        parsed = ast.parse(expr_clean, mode="eval")
        result = _safe_eval_node(parsed.body)
        
        # Round neatly if float is integer-valued
        if isinstance(result, float) and result.is_integer():
            formatted_result: Any = int(result)
        else:
            formatted_result = round(result, 6)

        return {
            "tool": "calculator",
            "expression": expression,
            "result": formatted_result,
            "status": "success",
        }
    except Exception as e:
        return {
            "tool": "calculator",
            "expression": expression,
            "error": f"Evaluation error: {str(e)}",
            "status": "error",
        }


# ---------------------------------------------------------------------------
# 2. Get Current Time Tool
# ---------------------------------------------------------------------------

_TIMEZONE_OFFSETS = {
    "utc": 0.0,
    "gmt": 0.0,
    "est": -5.0,
    "edt": -4.0,
    "cst": -6.0,
    "cdt": -5.0,
    "pst": -8.0,
    "pdt": -7.0,
    "ist": 5.5,
    "asia/kolkata": 5.5,
    "america/new_york": -4.0,
    "america/los_angeles": -7.0,
    "europe/london": 1.0,
    "asia/tokyo": 9.0,
    "australia/sydney": 10.0,
}


def get_current_time(timezone: str = "UTC") -> Dict[str, Any]:
    """
    Returns the current date and time in the specified timezone.
    
    Args:
        timezone: The target timezone string, e.g. 'UTC', 'IST', 'PST', 'EST', or 'Asia/Kolkata'.
    """
    tz_key = timezone.strip().lower()
    
    # Determine UTC offset
    offset_hours = _TIMEZONE_OFFSETS.get(tz_key, 0.0)
    
    # Get current UTC timestamp
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    target_time = now_utc + datetime.timedelta(hours=offset_hours)

    return {
        "tool": "get_current_time",
        "requested_timezone": timezone,
        "utc_offset_hours": offset_hours,
        "current_time_iso": target_time.isoformat(),
        "formatted_datetime": target_time.strftime("%A, %B %d, %Y - %I:%M:%S %p"),
        "timezone_label": timezone.upper(),
        "status": "success",
    }


# ---------------------------------------------------------------------------
# 3. Tool Registry & Dispatcher
# ---------------------------------------------------------------------------

TOOL_REGISTRY: Dict[str, Callable[..., Dict[str, Any]]] = {
    "calculator": calculator,
    "get_current_time": get_current_time,
}


def execute_tool(name: str, arguments: Dict[str, Any]) -> str:
    """
    Dispatches tool execution by looking up the tool name in the registry,
    running the function with arguments, and returning serialized JSON.
    """
    if name not in TOOL_REGISTRY:
        error_payload = {
            "tool": name,
            "status": "error",
            "error": f"Tool '{name}' is not registered in the local tool runtime.",
            "available_tools": list(TOOL_REGISTRY.keys()),
        }
        return json.dumps(error_payload)

    tool_fn = TOOL_REGISTRY[name]
    try:
        result_dict = tool_fn(**arguments)
        return json.dumps(result_dict)
    except Exception as e:
        error_payload = {
            "tool": name,
            "status": "error",
            "error": f"Exception raised during tool execution: {str(e)}",
        }
        return json.dumps(error_payload)


if __name__ == "__main__":
    print("=== Testing Tool Execution Locally ===")
    
    # Test Calculator
    calc_out = execute_tool("calculator", {"expression": "345 * 28"})
    print("Calculator ('345 * 28'):", calc_out)

    calc_sqrt = execute_tool("calculator", {"expression": "sqrt(144) + 15 * 3"})
    print("Calculator ('sqrt(144) + 15 * 3'):", calc_sqrt)

    # Test Current Time
    time_utc = execute_tool("get_current_time", {"timezone": "UTC"})
    print("Time (UTC):", time_utc)

    time_ist = execute_tool("get_current_time", {"timezone": "IST"})
    print("Time (IST):", time_ist)
