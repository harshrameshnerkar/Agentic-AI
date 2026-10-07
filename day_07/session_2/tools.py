"""
Day 7 - Session 2: LangGraph
Module: tools.py

Defines standard LangChain tools using the @tool decorator:
1. search: Factual database lookup (Apollo 11, JWST, Curiosity rover).
2. calculate: Deterministic arithmetic expression evaluator.
"""

from __future__ import annotations
import re
from langchain_core.tools import tool


@tool
def search(query: str) -> str:
    """Search knowledge base for historical space mission milestones and dates."""
    kb = {
        "apollo 11": "Apollo 11 launched July 16, 1969; landed on the Moon July 20, 1969.",
        "james webb": "The James Webb Space Telescope (JWST) launched December 25, 2021.",
        "curiosity rover": "NASA's Curiosity rover landed on Mars on August 6, 2012."
    }
    query_lower = query.lower()
    for key, val in kb.items():
        if key in query_lower:
            return val
    return f"No direct entry found for '{query}'. Try 'Apollo 11' or 'James Webb'."


@tool
def calculate(expression: str) -> str:
    """Calculate and safely evaluate a mathematical expression (e.g. '2021 - 1969')."""
    try:
        sanitized = re.sub(r"[^0-9+\-*/(). ]", "", expression)
        result = eval(sanitized, {"__builtins__": {}}, {})
        return str(result)
    except Exception as err:
        return f"Calculation error: {err}"


ALL_TOOLS = [search, calculate]
