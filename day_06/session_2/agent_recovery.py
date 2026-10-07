"""
Day 6 - Session 2: Designing Good Tools
Module: agent_recovery.py

Description:
    Demonstrates the Self-Correction & Error Recovery Loop:
    1. The agent makes an imperfect first request (e.g. querying a non-existent table or file).
    2. Instead of crashing the Python process with an unhandled exception,
       the tool catches the error and returns it as a structured OBSERVATION with schema hints.
    3. The LLM reads the error observation, understands what went wrong, and self-corrects
       by issuing the correct call in the next turn!
"""

from __future__ import annotations
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import os
import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tools import dispatch_tool
from schemas import get_designed_tools

# Load environment with override=True to ensure session_2 .env is prioritized
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gemini-3.1-flash-lite")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")


class SelfCorrectingAgent:
    """
    Autonomous agent designed to demonstrate error recovery through informative tool observations.
    """

    def __init__(self, model: str = OPENAI_MODEL):
        self.model = model
        self.llm = OpenAI(
            base_url=OPENAI_BASE_URL,
            api_key=OPENAI_API_KEY
        )
        self.tools = get_designed_tools()

    def _call_llm_with_retry(self, **kwargs) -> Any:
        """Invokes chat completion with backoff for rate limit and server busy protection."""
        from openai import RateLimitError, InternalServerError, APIConnectionError
        max_retries = 5
        base_delay = 6.0
        for attempt in range(1, max_retries + 1):
            try:
                return self.llm.chat.completions.create(**kwargs)
            except (RateLimitError, InternalServerError, APIConnectionError) as err:
                err_text = str(err)
                
                # If daily quota is exhausted (retry in hours), do not sleep hours, raise immediately
                if "daily" in err_text.lower() or "quota exceeded" in err_text.lower() and "h" in err_text:
                    print(f"\n[FATAL QUOTA ERROR] Model daily quota exhausted: {err_text}", flush=True)
                    raise err

                if attempt == max_retries:
                    raise err
                
                sleep_time = base_delay * attempt
                if "retry in " in err_text:
                    try:
                        match = re.search(r"retry in ([0-9.]+)s", err_text)
                        if match:
                            parsed_s = float(match.group(1))
                            if parsed_s < 60.0:
                                sleep_time = parsed_s + 1.0
                    except Exception:
                        pass
                
                print(f"  [API Notice: {type(err).__name__}] Cooling down for {sleep_time:.1f}s (Attempt {attempt}/{max_retries})...", flush=True)
                time.sleep(sleep_time)

    def run_recovery_demo(self, prompt: str, max_turns: int = 4) -> Dict[str, Any]:
        """
        Executes an agent loop where tool errors are returned as observations,
        allowing the model to inspect the feedback, self-correct, and succeed.
        """
        system_prompt = (
            "You are an enterprise AI assistant with access to 5 tools: 'web_search', 'read_file', "
            "'query_sqlite', 'call_external_api', and 'send_email'. "
            "If a tool returns an error observation, analyze the error message and hints carefully, "
            "correct your arguments, and retry until you fulfill the user's objective."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        turn_logs = []
        errors_encountered = 0
        self_corrections = 0

        print("\n" + "=" * 80, flush=True)
        print(" [SELF-CORRECTION DEMO] AGENT RUNNING WITH 'ERRORS AS OBSERVATIONS'", flush=True)
        print("=" * 80, flush=True)
        print(f"Goal: \"{prompt}\"", flush=True)
        print(f"Available Tools: {[t['function']['name'] for t in self.tools]}", flush=True)

        for turn in range(1, max_turns + 1):
            print(f"\n>>> TURN {turn} / {max_turns} <<<", flush=True)

            response = self._call_llm_with_retry(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto"
            )

            response_msg = response.choices[0].message
            # Append message directly to preserve Gemini thought signatures
            messages.append(response_msg)

            tool_calls = response_msg.tool_calls or []

            # If no tools called, model has completed the resolution
            if not tool_calls:
                final_answer = response_msg.content or ""
                print(f"\n[Agent Finished] Final answer synthesized on Turn {turn}.", flush=True)
                return {
                    "status": "SUCCESS",
                    "turns": turn,
                    "errors_encountered": errors_encountered,
                    "self_corrections": self_corrections,
                    "final_answer": final_answer,
                    "turn_logs": turn_logs
                }

            # Execute tool calls
            for call in tool_calls:
                fn_name = call.function.name
                raw_args = call.function.arguments

                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                except json.JSONDecodeError:
                    args = {}

                print(f"  -> Model Requested Tool: {fn_name}({json.dumps(args)})", flush=True)

                # Execute local tool safely (never throws unhandled exceptions!)
                observation = dispatch_tool(fn_name, args)

                is_error = observation.get("status") == "error"
                if is_error:
                    errors_encountered += 1
                    print(f"  ⚠️ TOOL RETURNED ERROR OBSERVATION: {observation.get('error_type')}", flush=True)
                    print(f"     Feedback Sent to Model: {observation.get('message')}", flush=True)
                else:
                    if errors_encountered > 0 and self_corrections < errors_encountered:
                        self_corrections += 1
                        print(f"  ✅ MODEL SUCCESSFULLY SELF-CORRECTED on Turn {turn}!", flush=True)
                    print(f"  ✓ Tool Execution Succeeded.", flush=True)

                turn_logs.append({
                    "turn": turn,
                    "tool": fn_name,
                    "args": args,
                    "status": observation.get("status"),
                    "observation_preview": str(observation)[:150]
                })

                # Append tool observation to conversation history
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "name": fn_name,
                    "content": json.dumps(observation)
                })

        return {
            "status": "MAX_TURNS_EXCEEDED",
            "turns": max_turns,
            "errors_encountered": errors_encountered,
            "self_corrections": self_corrections,
            "final_answer": "Loop limit reached.",
            "turn_logs": turn_logs
        }
