"""
Context-Engineered Agent.
Applies:
1. Context Budgeting: Lean, static, prompt-cache aligned system prompt (< 100 words).
2. Filtered Tool Outputs: Strips infrastructure metadata and noise before context injection.
3. Sub-Agent Context Isolation: Heavy raw log streams processed in isolated scratchpad.
4. History & Observation Compaction: Compacts older intermediate payloads.
"""

import os
import json
import time
from typing import Any, Dict, List
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

from cost_tracker import SessionTokenTracker
from tools import OPTIMIZED_TOOL_REGISTRY, OPTIMIZED_TOOL_SCHEMAS

load_dotenv(Path(__file__).resolve().parent / ".env")

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gemini-3.1-flash-lite")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")


# Lean, static, cache-aligned system prompt (90 tokens vs 1,200 tokens in baseline)
LEAN_SYSTEM_PROMPT = """You are an SRE Diagnostic Agent.
Investigate infrastructure incidents using available tools.
Analyze anomalous telemetry, inspect the isolated root-cause diagnosis,
and synthesize a concise Root Cause Analysis (RCA) report with mitigation actions.
Be direct, factual, and concise. Avoid conversational preamble.
"""


class ContextEngineeredAgent:
    """Agent running with strict context window budgeting and optimization."""

    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY or GEMINI_API_KEY must be configured.")
        self.client = OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)
        self.model = OPENAI_MODEL
        self.tracker = SessionTokenTracker("Context_Engineered_Agent")

    def run(self, user_prompt: str, max_turns: int = 5) -> Dict[str, Any]:
        # Context Engineering: Static system prompt placed strictly at prefix for prompt caching
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": LEAN_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        t_start = time.monotonic()
        turn = 0
        final_answer = ""
        tool_call_history = []

        while turn < max_turns:
            turn += 1

            # Compaction & Observation Pruning:
            # If history grows beyond 4 messages, compact older verbose tool messages
            if len(messages) > 4:
                for idx in range(2, len(messages) - 2):
                    msg_item = messages[idx]
                    if isinstance(msg_item, dict) and msg_item.get("role") == "tool":
                        try:
                            parsed = json.loads(msg_item["content"])
                            # If older tool content has redundant details, compact to salient reference
                            if isinstance(parsed, dict) and len(msg_item["content"]) > 180:
                                compacted = {
                                    "status": "compacted_reference",
                                    "key_entity": parsed.get("incident_id") or parsed.get("service") or parsed.get("pod"),
                                    "salient_finding": parsed.get("reported_symptom") or parsed.get("diagnostic_summary") or "observed",
                                }
                                messages[idx]["content"] = json.dumps(compacted)
                        except Exception:
                            pass

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=OPTIMIZED_TOOL_SCHEMAS,
                tool_choice="auto",
                temperature=0.1,
            )

            usage = getattr(response, "usage", None)
            if usage:
                self.tracker.record_turn(
                    turn_number=turn,
                    prompt_tokens=usage.prompt_tokens,
                    completion_tokens=usage.completion_tokens,
                    context_type="main"
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

                tool_fn = OPTIMIZED_TOOL_REGISTRY.get(fn_name)
                obs = tool_fn(**args) if tool_fn else {"error": f"Tool '{fn_name}' not found"}

                tool_call_history.append({"tool": fn_name, "args": args})

                # High-entropy observation feeding
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(obs, default=str),
                })

        total_duration = time.monotonic() - t_start

        return {
            "approach": "Context-Engineered (Optimized)",
            "turns_executed": turn,
            "total_duration_sec": round(total_duration, 2),
            "token_summary": self.tracker.summary(),
            "final_answer": final_answer,
            "tool_calls_count": len(tool_call_history),
        }
