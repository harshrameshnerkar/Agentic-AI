"""
Baseline Agent (Unoptimized Architecture).
Characteristics:
- Monolithic, bloated system prompt (~950 tokens).
- Zero caching: Redundant API calls even for repeated/identical queries.
- Raw, uncompressed JSON tool observations injected into context.
- High token consumption, higher costs, and variable latencies.
"""

import os
import re
import time
import json
from typing import Any, Dict, List
from dotenv import load_dotenv
from openai import OpenAI

from tools import (
    OPTIMIZED_TOOL_SCHEMAS,
    tool_query_database,
    tool_search_docs,
    tool_calculate,
    tool_read_log,
)
from prompt_optimizer import BASELINE_BLOATED_SYSTEM_PROMPT

load_dotenv()

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gemini-3.1-flash-lite")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")


class BaselineAgent:
    """Unoptimized baseline agent without caching or prompt compression."""

    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY or GEMINI_API_KEY must be configured in .env.")
        self.client = OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)
        self.model = OPENAI_MODEL

    def _call_llm_with_retry(self, messages: List[Dict[str, Any]], tools: Any, max_retries: int = 4) -> Any:
        delay = 10.0
        for attempt in range(max_retries):
            try:
                kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.1,
                }
                if tools:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = "auto"
                return self.client.chat.completions.create(**kwargs)
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    match = re.search(r"retryDelay':\s*'(\d+)s", err_str)
                    sleep_time = int(match.group(1)) + 2 if match else delay
                    print(f"      [Baseline 429 Notice] Sleeping {sleep_time}s before retry...", flush=True)
                    time.sleep(sleep_time)
                    delay = max(delay * 1.5, 30.0)
                else:
                    raise e
        kwargs = {"model": self.model, "messages": messages, "temperature": 0.1}
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        return self.client.chat.completions.create(**kwargs)

    def execute_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if name == "query_database":
            return tool_query_database(**args)
        elif name == "search_docs":
            return tool_search_docs(**args)
        elif name == "calculate":
            return tool_calculate(**args)
        elif name == "read_log":
            return tool_read_log(**args)
        return {"error": f"Unknown tool: {name}"}

    def run(self, prompt: str, max_turns: int = 3) -> Dict[str, Any]:
        t0 = time.time()
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": BASELINE_BLOATED_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        total_prompt_tokens = 0
        total_completion_tokens = 0
        final_answer = ""
        tools_called = []

        turn = 0
        while turn < max_turns:
            turn += 1

            res = self._call_llm_with_retry(messages, OPTIMIZED_TOOL_SCHEMAS)
            msg = res.choices[0].message
            messages.append(msg)

            usage = getattr(res, "usage", None)
            if usage:
                total_prompt_tokens += getattr(usage, "prompt_tokens", 0)
                total_completion_tokens += getattr(usage, "completion_tokens", 0)

            tool_calls = getattr(msg, "tool_calls", None) or []
            if not tool_calls:
                final_answer = msg.content or ""
                break

            for tc in tool_calls:
                fn_name = tc.function.name
                tools_called.append(fn_name)
                try:
                    args = json.loads(tc.function.arguments)
                except Exception:
                    args = {}

                obs = self.execute_tool(fn_name, args)

                # Unoptimized: Dumps raw indented JSON string into context
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(obs, indent=2),
                })

        if not final_answer:
            res_final = self._call_llm_with_retry(messages, tools=None)
            final_answer = res_final.choices[0].message.content or ""
            usage = getattr(res_final, "usage", None)
            if usage:
                total_prompt_tokens += getattr(usage, "prompt_tokens", 0)
                total_completion_tokens += getattr(usage, "completion_tokens", 0)

        latency_ms = (time.time() - t0) * 1000.0

        return {
            "prompt": prompt,
            "final_answer": final_answer,
            "tools_called": tools_called,
            "prompt_tokens": total_prompt_tokens,
            "completion_tokens": total_completion_tokens,
            "total_tokens": total_prompt_tokens + total_completion_tokens,
            "latency_ms": latency_ms,
            "is_cache_hit": False,
            "cache_type": None,
            "model_used": self.model,
        }
