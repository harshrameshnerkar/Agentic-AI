"""
Day 6 - Session 3: Multi-Step Tool Use
Module: multi_step_agent.py

Autonomous multi-step agent orchestrating a 4-tool chain:
1. Chaining calls: Output of step N feeds into step N+1.
2. Feeding results back into context with role="tool".
3. Conversation history growth & token metrics logged per turn.
4. Intelligent truncation & compaction when history expands.
5. ReAct pattern telemetry: Logs every Thought, Action, and Observation explicitly.
"""

from __future__ import annotations
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import os
import re
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from openai import OpenAI

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tools import dispatch_tool
from schemas import get_incident_resolution_tools
from history_manager import HistoryGrowthTracker

# Load local .env
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gemini-3.1-flash-lite")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")


class MultiStepIncidentAgent:
    """
    Orchestrates sequential multi-step tool calls with full ReAct logging and context telemetry.
    """

    def __init__(self, model: str = OPENAI_MODEL):
        self.model = model
        self.llm = OpenAI(
            base_url=OPENAI_BASE_URL,
            api_key=OPENAI_API_KEY
        )
        self.tools = get_incident_resolution_tools()
        self.history_tracker = HistoryGrowthTracker(token_compaction_threshold=1800)

    def _call_llm_with_retry(self, **kwargs) -> Any:
        """Calls LLM with backoff for rate limits and server availability."""
        from openai import RateLimitError, InternalServerError, APIConnectionError
        max_retries = 5
        base_delay = 5.0
        for attempt in range(1, max_retries + 1):
            try:
                return self.llm.chat.completions.create(**kwargs)
            except (RateLimitError, InternalServerError, APIConnectionError) as err:
                err_text = str(err)
                if "daily" in err_text.lower() or ("quota exceeded" in err_text.lower() and "h" in err_text):
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

                print(f"  [RateLimit Notice] Cooling down for {sleep_time:.1f}s (Attempt {attempt}/{max_retries})...", flush=True)
                time.sleep(sleep_time)

    def execute_multi_step_workflow(
        self,
        user_prompt: str,
        max_turns: int = 6
    ) -> Dict[str, Any]:
        """
        Executes a 4-step tool chain logging:
        - THOUGHT: Model reasoning & plan
        - ACTION: Tool name & validated arguments
        - OBSERVATION: Tool output fed back into context
        - CONTEXT METRICS: Conversation history size & token growth
        """
        system_instruction = (
            "You are an enterprise incident resolution autonomous AI agent. "
            "When given a customer incident ticket, you MUST execute a strict 4-step sequential workflow:\n"
            "1. Call 'lookup_incident_ticket' to find the customer ID, tier, affected service, and downtime minutes.\n"
            "2. Call 'fetch_service_policy' using the discovered SLA tier and service name to get policy thresholds and rates.\n"
            "3. Call 'compute_financial_adjustment' using the downtime minutes and policy rates to calculate the audited credit.\n"
            "4. Call 'record_credit_memo' with a deterministic idempotency key (format: 'IDEM-<ticket_id>-<customer_id>'), "
            "the customer ID, ticket ID, calculated credit, and manager email to post the credit to the ledger.\n"
            "5. Finally, synthesize a comprehensive executive incident and financial settlement summary.\n"
            "Do NOT skip steps or perform manual arithmetic calculations. Use the tools in exact sequence."
        )

        messages: List[Any] = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt}
        ]

        chain_log: List[Dict[str, Any]] = []
        start_time = time.time()

        print("\n" + "=" * 80, flush=True)
        print(" [MULTI-STEP TOOL EXECUTION TRACE] 4 SEQUENTIAL TOOLS WITH REACT TELEMETRY", flush=True)
        print("=" * 80, flush=True)
        print(f"Goal: \"{user_prompt}\"", flush=True)

        for turn in range(1, max_turns + 1):
            print(f"\n{'='*30} TURN {turn} / {max_turns} {'='*30}", flush=True)

            # Measure & log conversation history metrics before calling LLM
            metrics = self.history_tracker.measure_history(messages)
            print(f"  [Context Metrics] Messages: {metrics['message_count']} | Chars: {metrics['total_chars']} | Est. Tokens: {metrics['estimated_tokens']}", flush=True)

            t0 = time.time()
            response = self._call_llm_with_retry(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto"
            )
            llm_latency = time.time() - t0

            response_msg = response.choices[0].message
            messages.append(response_msg)

            # Extract THOUGHT
            thought_text = response_msg.content or ""
            tool_calls = response_msg.tool_calls or []

            print(f"  [LLM Latency] {llm_latency:.2f}s", flush=True)
            if thought_text:
                print(f"  🧠 [THOUGHT]: {thought_text.strip()}", flush=True)
            else:
                if tool_calls:
                    print(f"  🧠 [THOUGHT]: Model reasoned to invoke {len(tool_calls)} tool(s) to progress the workflow.", flush=True)

            # If no tools called, the model has completed the resolution
            if not tool_calls:
                final_answer = thought_text
                print(f"\n  🎯 [GOAL COMPLETED] All sequential steps fulfilled on Turn {turn}!", flush=True)
                total_duration = time.time() - start_time
                return {
                    "status": "SUCCESS",
                    "turns_taken": turn,
                    "total_duration_sec": total_duration,
                    "tools_executed": [entry["tool"] for entry in chain_log],
                    "chain_log": chain_log,
                    "final_answer": final_answer,
                    "history_growth": self.history_tracker.growth_log
                }

            # Process ACTION(S) and OBSERVATION(S)
            for call in tool_calls:
                fn_name = call.function.name
                raw_args = call.function.arguments

                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                except json.JSONDecodeError:
                    args = {}

                print(f"\n  ⚡ [ACTION]: Call Tool '{fn_name}'", flush=True)
                print(f"     Arguments: {json.dumps(args, indent=2)}", flush=True)

                # Execute Tool (HOST EXECUTION)
                exec_t0 = time.perf_counter()
                observation = dispatch_tool(fn_name, args)
                exec_duration_ms = (time.perf_counter() - exec_t0) * 1000.0

                # Formatted OBSERVATION
                print(f"  👁️ [OBSERVATION] (Latency: {exec_duration_ms:.2f}ms):", flush=True)
                obs_summary = json.dumps(observation, indent=2)
                # Print clean observation snippet
                if len(obs_summary) > 350:
                    print(f"{obs_summary[:350]}\n     ... [Observation Continues] ...", flush=True)
                else:
                    print(f"{obs_summary}", flush=True)

                # Record in telemetry chain log
                chain_log.append({
                    "turn": turn,
                    "step": len(chain_log) + 1,
                    "tool": fn_name,
                    "arguments": args,
                    "observation": observation,
                    "latency_ms": exec_duration_ms
                })

                # FEEDING RESULTS BACK INTO CONTEXT
                # Crucial step: The output of Tool N is serialized as JSON in a message with role="tool"
                # so the LLM can consume it in Turn N+1 to call Tool N+1
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "name": fn_name,
                    "content": json.dumps(observation)
                })

            # Check if compaction should be triggered to prevent explosive context growth
            messages, was_compacted = self.history_tracker.compact_completed_tools(messages)
            if was_compacted:
                print("  📦 [CONTEXT COMPACTION]: Older completed observations summarized into milestone.", flush=True)

            # Gentle pause between turns to respect free-tier RPM ceilings
            time.sleep(2.0)

        return {
            "status": "MAX_TURNS_EXCEEDED",
            "turns_taken": max_turns,
            "total_duration_sec": time.time() - start_time,
            "tools_executed": [entry["tool"] for entry in chain_log],
            "chain_log": chain_log,
            "final_answer": "Workflow reached maximum permitted turns.",
            "history_growth": self.history_tracker.growth_log
        }
