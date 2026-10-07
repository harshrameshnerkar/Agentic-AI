"""
Evaluated Agent Implementation.
Features:
- Complete tool-calling loop supporting all enterprise tool schemas.
- Full trajectory recording (turn index, tool choices, arguments, observations).
- Robust 429 rate-limit handling with exponential backoff.
- Configurable prompt modes for regression benchmark comparisons:
  * "optimized": Production-tuned system prompt with clear tool guidance.
  * "baseline": Naive unguided prompt (used to demonstrate failure taxonomy and regression detection).
"""

import os
import re
import time
import json
from typing import Any, Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

from tools import (
    AGENT_TOOL_SCHEMAS,
    tool_query_database,
    tool_search_docs,
    tool_calculate,
    tool_read_file,
    tool_list_dir,
    tool_send_alert,
)

load_dotenv(Path(__file__).resolve().parent / ".env")

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gemini-3.1-flash-lite")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")

OPTIMIZED_SYSTEM_PROMPT = """You are an efficient, accurate Enterprise Agent.
You have access to specialized tools:
- query_database: tables ('customers', 'orders', 'inventory').
- search_docs: internal SOPs, security guidelines, SLA tiers.
- calculate: mathematical formulas and metric computations.
- read_file & list_dir: filesystem and server log inspection.
- send_alert: escalation notifications to Slack/PagerDuty.

RULES:
1. Always pick the most specific tool for the task.
2. For multi-step tasks, execute prerequisite lookups before downstream calculations or alerts.
3. If a record or file is not found, report that clearly.
4. Only call send_alert when the user request explicitly instructs to send an alert.
5. Provide concise, direct answers based strictly on tool findings.
"""

BASELINE_SYSTEM_PROMPT = """You are an AI assistant.
Answer user questions. You have access to tools if needed.
"""


class EvaluatedAgent:
    """Agent under evaluation with full trajectory auditing."""

    def __init__(self, mode: str = "optimized"):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY or GEMINI_API_KEY must be configured in .env.")
        self.client = OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)
        self.model = OPENAI_MODEL
        self.mode = mode
        self.system_prompt = OPTIMIZED_SYSTEM_PROMPT if mode == "optimized" else BASELINE_SYSTEM_PROMPT

    def _call_llm_with_retry(self, messages: List[Dict[str, Any]], tools: Any, max_retries: int = 5) -> Any:
        delay = 10.0
        for attempt in range(max_retries):
            try:
                return self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=0.1,
                )
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    match = re.search(r"retryDelay':\s*'(\d+)s", err_str)
                    sleep_time = int(match.group(1)) + 2 if match else delay
                    print(f"      [Rate-Limit Notice] 429 quota hit. Sleeping {sleep_time}s before retry (attempt {attempt+1}/{max_retries})...", flush=True)
                    time.sleep(sleep_time)
                    delay = max(delay * 1.5, 30.0)
                else:
                    raise e
        return self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.1,
        )

    def execute_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches tool execution to the appropriate tool function."""
        if name == "query_database":
            return tool_query_database(**args)
        elif name == "search_docs":
            return tool_search_docs(**args)
        elif name == "calculate":
            return tool_calculate(**args)
        elif name == "read_file":
            return tool_read_file(**args)
        elif name == "list_dir":
            return tool_list_dir(**args)
        elif name == "send_alert":
            return tool_send_alert(**args)
        else:
            return {"status": "ERROR", "error": f"Unknown tool: '{name}'"}

    def run(self, user_prompt: str, max_turns: int = 5) -> Dict[str, Any]:
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        trajectory = []
        turn = 0
        final_answer = ""

        while turn < max_turns:
            turn += 1

            response = self._call_llm_with_retry(
                messages=messages,
                tools=AGENT_TOOL_SCHEMAS,
            )

            msg = response.choices[0].message
            # Append message directly to preserve Gemini thought signatures
            messages.append(msg)

            tool_calls = getattr(msg, "tool_calls", None) or []
            if not tool_calls:
                final_answer = msg.content or ""
                break

            for tc in tool_calls:
                fn_name = tc.function.name
                raw_args = tc.function.arguments
                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                except Exception:
                    args = {}

                # Execute tool
                obs = self.execute_tool(fn_name, args)

                # Record step in trajectory
                step_record = {
                    "step_number": turn,
                    "tool_name": fn_name,
                    "args": args,
                    "observation": obs,
                }
                trajectory.append(step_record)

                # Send observation back to model
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(obs, default=str),
                })

        if not final_answer:
            # Fallback final synthesis if max turns reached on tool calls
            final_resp = self._call_llm_with_retry(messages=messages, tools=None)
            final_answer = final_resp.choices[0].message.content or ""

        return {
            "prompt": user_prompt,
            "turns_taken": turn,
            "trajectory": trajectory,
            "tools_called": [s["tool_name"] for s in trajectory],
            "final_answer": final_answer,
        }
