"""
Day 6 - Session 1: How Tool Calling Works
Module: schemas.py

Description:
    Defines the standard OpenAI/Gemini JSON Schema specifications for:
    1. calculator: Evaluates arithmetic expressions safely.
    2. get_time: Retrieves the current real-world date and time for any timezone.

    Also provides Pydantic v2 model definitions to demonstrate how JSON schemas
    can be auto-generated programmatically.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# ============================================================================
# 1. Pydantic Argument Models (For Type Validation & Auto-Schema Generation)
# ============================================================================

class CalculatorInput(BaseModel):
    """Schema model for calculator tool arguments."""
    expression: str = Field(
        ...,
        description="The mathematical expression string to evaluate (e.g. '125 * 45 + 320' or '(15000 - 3200) * 0.15')."
    )


class GetTimeInput(BaseModel):
    """Schema model for get_time tool arguments."""
    timezone: str = Field(
        default="UTC",
        description="The IANA timezone identifier (e.g. 'UTC', 'Asia/Kolkata', 'America/New_York', 'Europe/London', 'Asia/Tokyo')."
    )


# ============================================================================
# 2. Standard JSON Schemas for LLM Tool Calling (OpenAI / Gemini Format)
# ============================================================================

CALCULATOR_SCHEMA: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": (
            "Evaluates a mathematical expression safely using an Abstract Syntax Tree (AST). "
            "Supports addition (+), subtraction (-), multiplication (*), division (/), "
            "integer floor division (//), modulo (%), exponentiation (**), and parentheses. "
            "Never guess arithmetic—always use this tool for accurate financial or scientific calculations."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The mathematical expression to evaluate, e.g. '450 * 18 + 1200 / 4' or '(2500 - 450) * 1.08'."
                }
            },
            "required": ["expression"]
        }
    }
}

GET_TIME_SCHEMA: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_time",
        "description": (
            "Retrieves the current date and time for a specified timezone. "
            "Always call this tool when the user asks for the current time, today's date, "
            "day of the week, or time differences between regions."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": (
                        "The IANA timezone identifier (e.g. 'UTC', 'Asia/Kolkata', 'America/New_York', "
                        "'Europe/London', 'Asia/Tokyo'). Defaults to 'UTC' if not specified."
                    ),
                    "default": "UTC"
                }
            },
            "required": []
        }
    }
}

ALL_TOOLS: List[Dict[str, Any]] = [
    CALCULATOR_SCHEMA,
    GET_TIME_SCHEMA
]


def get_tools_schema() -> List[Dict[str, Any]]:
    """Returns the full list of tool definitions ready for chat completions API."""
    return ALL_TOOLS
