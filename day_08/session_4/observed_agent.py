"""
Instrumented ReAct Agent with Full OpenTelemetry & Langfuse Span Tracing.
Captures:
- Root Agent Spans
- Turn Spans
- LLM Spans with exact token accounting
- Tool Execution Spans with arguments, latency, and exceptions
"""

import os
import json
import time
import uuid
from typing import Any, Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

from tracer import Tracer
from tools import OBSERVABILITY_TOOL_REGISTRY, OBSERVABILITY_TOOL_SCHEMAS

load_dotenv(Path(__file__).resolve().parent / ".env")

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gemini-3.1-flash-lite")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")

INPUT_COST_PER_M = 0.075
OUTPUT_COST_PER_M = 0.30


class ObservedAgent:
    """Agent fully instrumented with hierarchical span tracing."""

    def __init__(self, tracer: Optional[Tracer] = None, fail_fast_on_tool_error: bool = False):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY or GEMINI_API_KEY must be configured.")
        self.client = OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)
        self.model = OPENAI_MODEL
        self.tracer = tracer or Tracer()
        self.fail_fast_on_tool_error = fail_fast_on_tool_error

    def run(
        self,
        user_prompt: str,
        trace_id: Optional[str] = None,
        max_turns: int = 5,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        trace_id = trace_id or f"trace_{str(uuid.uuid4())[:12]}"
        system_prompt = system_prompt or (
            "You are a Financial Operations Agent. "
            "Use the provided tools to query quarterly revenue reports from the 'revenue_reports' table, "
            "convert currencies when needed, and report your findings clearly."
        )

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        total_tokens_used = 0
        final_answer = ""
        run_status = "OK"
        run_error = None

        # 1. ROOT SPAN: agent.run
        with self.tracer.span(
            name="agent.run",
            trace_id=trace_id,
            parent_span_id=None,
            span_type="agent",
            attributes={"user_prompt": user_prompt, "model": self.model},
        ) as root_span:
            turn = 0
            while turn < max_turns:
                turn += 1

                # 2. TURN SPAN: agent.turn_N
                with self.tracer.span(
                    name=f"agent.turn_{turn}",
                    trace_id=trace_id,
                    parent_span_id=root_span.span_id,
                    span_type="chain",
                    attributes={"turn_number": turn},
                ) as turn_span:

                    # 3. LLM SPAN: llm.chat_completion
                    t_llm_start = time.monotonic()
                    with self.tracer.span(
                        name="llm.chat_completion",
                        trace_id=trace_id,
                        parent_span_id=turn_span.span_id,
                        span_type="llm",
                        attributes={"model": self.model, "temperature": 0.1},
                    ) as llm_span:
                        response = self.client.chat.completions.create(
                            model=self.model,
                            messages=messages,
                            tools=OBSERVABILITY_TOOL_SCHEMAS,
                            tool_choice="auto",
                            temperature=0.1,
                        )

                        usage = getattr(response, "usage", None)
                        p_tokens = usage.prompt_tokens if usage else 0
                        c_tokens = usage.completion_tokens if usage else 0
                        t_tokens = p_tokens + c_tokens
                        cost = (p_tokens / 1_000_000 * INPUT_COST_PER_M) + (c_tokens / 1_000_000 * OUTPUT_COST_PER_M)

                        total_tokens_used += t_tokens
                        llm_span.set_attribute("prompt_tokens", p_tokens)
                        llm_span.set_attribute("completion_tokens", c_tokens)
                        llm_span.set_attribute("total_tokens", t_tokens)
                        llm_span.set_attribute("cost_usd", round(cost, 6))

                        msg = response.choices[0].message
                        # Append message directly to preserve Gemini thought signatures
                        messages.append(msg)
                        tool_calls = getattr(msg, "tool_calls", None) or []

                    # If no tool calls, model provided final text!
                    if not tool_calls:
                        final_answer = msg.content or ""
                        turn_span.set_attribute("outcome", "final_response_generated")
                        break

                    # 4. TOOL SPANS: tool.<name>
                    for tc in tool_calls:
                        fn_name = tc.function.name
                        raw_args = tc.function.arguments
                        try:
                            args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                        except Exception:
                            args = {}

                        with self.tracer.span(
                            name=f"tool.{fn_name}",
                            trace_id=trace_id,
                            parent_span_id=turn_span.span_id,
                            span_type="tool",
                            attributes={"tool_name": fn_name, "arguments": args},
                        ) as tool_span:
                            tool_fn = OBSERVABILITY_TOOL_REGISTRY.get(fn_name)
                            if not tool_fn:
                                err = ValueError(f"Unknown tool: '{fn_name}'")
                                tool_span.end("ERROR", error=err)
                                obs = {"error": str(err)}
                            else:
                                try:
                                    obs = tool_fn(**args)
                                    tool_span.set_attribute("output", obs)
                                    tool_span.end("OK")
                                except Exception as e:
                                    tool_span.end("ERROR", error=e)
                                    obs = {"error": type(e).__name__, "message": str(e)}
                                    if self.fail_fast_on_tool_error:
                                        run_status = "ERROR"
                                        run_error = e
                                        turn_span.end("ERROR", error=e)
                                        root_span.end("ERROR", error=e)
                                        raise e

                            messages.append({
                                "role": "tool",
                                "tool_call_id": tc.id,
                                "content": json.dumps(obs, default=str),
                            })

            root_span.set_attribute("total_tokens", total_tokens_used)
            root_span.set_attribute("final_answer", final_answer[:200])

        return {
            "trace_id": trace_id,
            "status": run_status,
            "error": str(run_error) if run_error else None,
            "final_answer": final_answer,
            "total_tokens": total_tokens_used,
        }
