"""
Autonomous Agent Solution for the same FinOps Audit Task.
Equipped with fine-grained tools: get_invoices, convert_currency, calculate, check_budget_anomaly.
Demonstrates:
- Multi-turn ReAct loop reasoning.
- Latency multiplication across sequential turns.
- Compounding token consumption.
- Risk of mathematical or rounding hallucinations.
"""

import os
import json
import time
import re
from typing import Any, Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

from data import EXCHANGE_RATES, GROUND_TRUTH, RAW_INVOICES

# Load environment configuration
load_dotenv(Path(__file__).resolve().parent / ".env")

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gemini-3.1-flash-lite")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")


# Tool implementations
def tool_get_invoices() -> List[Dict[str, Any]]:
    """Retrieve raw multi-currency cloud invoice line-items."""
    return RAW_INVOICES


def tool_convert_currency(amount: float, from_currency: str, to_currency: str = "USD") -> Dict[str, Any]:
    """Convert an amount from a foreign currency to USD using official exchange rates."""
    from_curr = from_currency.upper()
    to_curr = to_currency.upper()
    rate = EXCHANGE_RATES.get(from_curr, 1.0)
    converted = round(amount * rate, 2)
    return {
        "original_amount": amount,
        "from_currency": from_curr,
        "to_currency": to_curr,
        "exchange_rate": rate,
        "converted_amount_usd": converted,
    }


def tool_calculate(expression: str) -> Dict[str, Any]:
    """Execute arithmetic calculations safely."""
    try:
        sanitized = re.sub(r"[^0-9+\-*/(). ]", "", expression)
        val = eval(sanitized, {"__builtins__": {}}, {})
        return {"expression": expression, "result": round(float(val), 2)}
    except Exception as e:
        return {"error": str(e), "expression": expression}


def tool_check_budget_anomaly(service_name: str, cost_usd: float, budget_usd: float) -> Dict[str, Any]:
    """Inspect if service spend exceeds budget by more than 15%."""
    variance = round(((cost_usd - budget_usd) / budget_usd) * 100.0, 2)
    is_anomaly = variance > 15.0
    return {
        "service": service_name,
        "cost_usd": cost_usd,
        "budget_usd": budget_usd,
        "variance_pct": variance,
        "is_anomaly": is_anomaly,
    }


AGENT_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "tool_get_invoices",
            "description": "Fetch all monthly cloud invoice line items.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tool_convert_currency",
            "description": "Convert foreign currency amounts (EUR, GBP, USD) to USD.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Original amount"},
                    "from_currency": {"type": "string", "description": "Currency code (EUR, GBP, USD)"},
                    "to_currency": {"type": "string", "description": "Target currency code, default USD"},
                },
                "required": ["amount", "from_currency"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tool_calculate",
            "description": "Perform arithmetic expressions (e.g. '14500 + 19656 + 12400').",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Math expression to evaluate"},
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tool_check_budget_anomaly",
            "description": "Calculate variance percentage and flag if spend exceeds budget by >15%.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_name": {"type": "string", "description": "Name of service"},
                    "cost_usd": {"type": "number", "description": "Actual normalized spend in USD"},
                    "budget_usd": {"type": "number", "description": "Allocated monthly budget in USD"},
                },
                "required": ["service_name", "cost_usd", "budget_usd"],
            },
        },
    },
]

TOOL_REGISTRY = {
    "tool_get_invoices": tool_get_invoices,
    "tool_convert_currency": tool_convert_currency,
    "tool_calculate": tool_calculate,
    "tool_check_budget_anomaly": tool_check_budget_anomaly,
}


class AutonomousAgentAuditor:
    """
    Solves the FinOps audit task using an autonomous ReAct loop with multi-step tool calls.
    """

    def __init__(self, max_turns: int = 8):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY or GEMINI_API_KEY must be configured.")
        self.client = OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)
        self.model = OPENAI_MODEL
        self.max_turns = max_turns

    def run(self, user_goal: Optional[str] = None) -> Dict[str, Any]:
        user_goal = user_goal or (
            "Perform a complete cloud infrastructure spend audit: "
            "1. Fetch all invoices. "
            "2. Normalize all currency amounts to USD. "
            "3. Calculate the exact total spend in USD across all services. "
            "4. Identify the top 3 cost drivers and any budget anomalies (>15% over budget). "
            "5. Produce a structured executive summary."
        )

        system_prompt = (
            "You are an autonomous FinOps Agent. "
            "Use the provided tools to fetch invoices, convert currencies, calculate exact totals, "
            "and check for anomalies. Once all data is gathered, provide a complete executive summary."
        )

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_goal},
        ]

        t_start = time.monotonic()
        total_prompt_tokens = 0
        total_completion_tokens = 0
        turns_executed = 0
        final_response = ""
        tool_call_history = []

        while turns_executed < self.max_turns:
            turns_executed += 1

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=AGENT_TOOLS_SCHEMA,
                tool_choice="auto",
                temperature=0.1,
            )

            usage = getattr(response, "usage", None)
            if usage:
                total_prompt_tokens += usage.prompt_tokens
                total_completion_tokens += usage.completion_tokens

            msg = response.choices[0].message
            # Append message object directly to preserve Gemini thought signatures
            messages.append(msg)

            tool_calls = getattr(msg, "tool_calls", None) or []
            if not tool_calls:
                final_response = msg.content or ""
                break

            for tc in tool_calls:
                fn_name = tc.function.name
                raw_args = tc.function.arguments
                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                except Exception:
                    args = {}

                tool_fn = TOOL_REGISTRY.get(fn_name)
                if tool_fn:
                    obs = tool_fn(**args)
                else:
                    obs = {"error": f"Unknown tool: {fn_name}"}

                tool_call_history.append({"tool": fn_name, "args": args, "obs": obs})
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(obs),
                })

        total_duration_sec = time.monotonic() - t_start

        # Check for arithmetic correctness in the final response
        target_total_str = "59,956"
        target_total_unformatted = "59956"
        found_exact_total = (
            target_total_str in final_response or
            target_total_unformatted in final_response or
            "59956.0" in final_response
        )

        return {
            "approach": "Autonomous ReAct Agent",
            "turns_executed": turns_executed,
            "llm_calls_made": turns_executed,
            "tool_calls_count": len(tool_call_history),
            "tool_call_history": tool_call_history,
            "total_time_sec": round(total_duration_sec, 3),
            "prompt_tokens": total_prompt_tokens,
            "completion_tokens": total_completion_tokens,
            "total_tokens": total_prompt_tokens + total_completion_tokens,
            "final_response": final_response,
            "found_exact_total": found_exact_total,
            "math_accuracy_pct": 100.0 if found_exact_total else 0.0,
        }
