"""
Day 6 - Session 1: How Tool Calling Works
Module: tool_loop.py

Description:
    Implements and deeply traces the full Request -> Execute -> Return tool calling lifecycle.
    Demonstrates:
    1. Single tool call execution tracing every step.
    2. Parallel tool calls (multiple tools called in a single model turn).
    3. tool_choice parameter controls ('auto', 'none', forced specific tool).
    4. Explicit explanation and telemetry showing why the model never executes code itself.
"""

from __future__ import annotations
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import os
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv
from openai import OpenAI

# Add directory to sys.path for direct imports
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tools import dispatch_tool_call
from schemas import get_tools_schema

# Load environment configuration
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gemini-3-flash-preview")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError(f"API key missing. Ensure OPENAI_API_KEY or GEMINI_API_KEY is in {env_path}")


@dataclass
class ToolExecutionStep:
    tool_call_id: str
    tool_name: str
    arguments: Dict[str, Any]
    observation: Dict[str, Any]
    execution_latency_ms: float


@dataclass
class LoopTraceReport:
    prompt: str
    tool_choice: Any
    initial_request_duration_sec: float
    total_duration_sec: float
    tool_calls_requested: int
    executed_steps: List[ToolExecutionStep]
    final_answer: str
    messages_history: List[Any]


class ToolLoopTracer:
    """
    Orchestrates and logs every phase of the LLM tool calling lifecycle.
    """

    def __init__(self, model: str = OPENAI_MODEL):
        self.model = model
        self.llm = OpenAI(
            base_url=OPENAI_BASE_URL,
            api_key=OPENAI_API_KEY
        )
        self.tools = get_tools_schema()

    def _create_completion_with_backoff(self, **kwargs) -> Any:
        """Executes chat completion with automatic exponential backoff on RPM limits."""
        from openai import RateLimitError
        max_retries = 4
        base_delay = 5.0
        for attempt in range(1, max_retries + 1):
            try:
                return self.llm.chat.completions.create(**kwargs)
            except RateLimitError as rle:
                if attempt == max_retries:
                    raise rle
                sleep_time = base_delay * attempt
                print(f"  [RateLimit Notice] 5 RPM ceiling reached. Cooling down for {sleep_time:.1f}s (Attempt {attempt}/{max_retries})...", flush=True)
                time.sleep(sleep_time)

    def run_trace(
        self,
        user_prompt: str,
        tool_choice: Any = "auto",
        system_prompt: Optional[str] = None
    ) -> LoopTraceReport:
        """
        Executes a complete Request -> Execute -> Return cycle with comprehensive telemetry logging.

        Args:
            user_prompt: The instruction or query to send to the model.
            tool_choice: 'auto', 'none', 'required', or a specific tool dict.
            system_prompt: Optional custom system instruction.

        Returns:
            LoopTraceReport containing the complete audit trace.
        """
        start_overall = time.time()

        if system_prompt is None:
            system_prompt = (
                "You are an accurate, helpful AI assistant equipped with real-world tools: "
                "'calculator' for all arithmetic and 'get_time' for date and timezone queries. "
                "Always call the appropriate tool when calculation or real-world time is needed."
            )

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        print("\n" + "=" * 80, flush=True)
        print(" PHASE 1: USER REQUEST & TOOL SCHEMA INJECTION", flush=True)
        print("=" * 80, flush=True)
        print(f"User Prompt: \"{user_prompt}\"", flush=True)
        print(f"Configured tool_choice: {tool_choice}", flush=True)
        print(f"Registered Tools ({len(self.tools)}):", flush=True)
        for t in self.tools:
            fn = t["function"]
            print(f"  • Tool Name: {fn['name']:<12} | Parameters: {list(fn['parameters']['properties'].keys())}", flush=True)

        print("\n" + "-" * 80, flush=True)
        print(" PHASE 2: DISPATCHING FIRST LLM REQUEST (Awaiting Model Decision)", flush=True)
        print("-" * 80, flush=True)

        t0 = time.time()
        # Call model with tool definitions using backoff protection
        response = self._create_completion_with_backoff(
            model=self.model,
            messages=messages,
            tools=self.tools,
            tool_choice=tool_choice
        )
        t1 = time.time()
        initial_request_duration = t1 - t0

        response_message = response.choices[0].message
        # Preserve Gemini thought signatures by appending response_message directly
        messages.append(response_message)

        tool_calls = response_message.tool_calls or []
        print(f"First Turn Latency: {initial_request_duration:.2f} seconds", flush=True)
        print(f"Model Tool Calls Emitted: {len(tool_calls)}", flush=True)

        # Did the model generate direct text instead of tools?
        if not tool_calls:
            print("[INFO] Model responded directly with natural language without requesting tools.", flush=True)
            print(f"Direct Response Content:\n{response_message.content}", flush=True)
            return LoopTraceReport(
                prompt=user_prompt,
                tool_choice=tool_choice,
                initial_request_duration_sec=initial_request_duration,
                total_duration_sec=time.time() - start_overall,
                tool_calls_requested=0,
                executed_steps=[],
                final_answer=response_message.content or "",
                messages_history=messages
            )

        print("\n" + "=" * 80, flush=True)
        print(f" PHASE 3: MODEL REQUESTED {len(tool_calls)} TOOL CALL(S) (Why the Model Never Runs Code)", flush=True)
        print("=" * 80, flush=True)
        print("""
[CORE CONCEPT: WHY THE MODEL NEVER RUNS CODE ITSELF]
  1. The LLM is a pure mathematical token predictor (weights & activations).
  2. It has NO runtime execution environment, NO CPU access, NO network sockets.
  3. Instead of executing code, the model outputs structured JSON describing its INTENT.
  4. Notice below: The model only gave us string tokens ('name' and 'arguments').
  5. The HOST APPLICATION (our Python script) is 100% responsible for actual execution!
""", flush=True)

        executed_steps: List[ToolExecutionStep] = []

        # Execute each requested tool call
        for idx, call in enumerate(tool_calls, 1):
            fn_name = call.function.name
            raw_args = call.function.arguments

            print(f"--- [Tool Call {idx}/{len(tool_calls)}] ID: {call.id} ---", flush=True)
            print(f"  Target Function: {fn_name}", flush=True)
            print(f"  Raw Arguments JSON from Model: {raw_args}", flush=True)

            try:
                parsed_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
            except json.JSONDecodeError as jde:
                print(f"  [ERROR] Failed to parse arguments JSON: {jde}", flush=True)
                parsed_args = {}

            print(f"\n  -> HOST EXECUTION: Executing local function '{fn_name}' safely...", flush=True)
            exec_t0 = time.perf_counter()
            observation = dispatch_tool_call(fn_name, parsed_args)
            exec_t1 = time.perf_counter()
            exec_latency_ms = (exec_t1 - exec_t0) * 1000.0

            print(f"  <- HOST EXECUTION COMPLETE ({exec_latency_ms:.2f} ms)", flush=True)
            print(f"  Observation Output: {json.dumps(observation, indent=2)}", flush=True)

            step_record = ToolExecutionStep(
                tool_call_id=call.id,
                tool_name=fn_name,
                arguments=parsed_args,
                observation=observation,
                execution_latency_ms=exec_latency_ms
            )
            executed_steps.append(step_record)

            # PHASE 4: Inject observation back into message context with role="tool"
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "name": fn_name,
                "content": json.dumps(observation)
            })

        print("\n" + "=" * 80, flush=True)
        print(" PHASE 4: PASSING OBSERVATIONS BACK TO MODEL (Second Turn Synthesis)", flush=True)
        print("=" * 80, flush=True)
        print(f"Updated Conversation Messages Length: {len(messages)} items", flush=True)
        print("Injected Tool Observations:")
        for step in executed_steps:
            print(f"  • Tool ID {step.tool_call_id} ({step.tool_name}) -> Status: {step.observation.get('status')}", flush=True)

        print("\nDispatching second API call with observations...", flush=True)
        t2 = time.time()
        second_response = self._create_completion_with_backoff(
            model=self.model,
            messages=messages,
            tools=self.tools
        )
        t3 = time.time()
        second_turn_duration = t3 - t2

        final_content = second_response.choices[0].message.content or ""
        messages.append(second_response.choices[0].message)

        total_elapsed = time.time() - start_overall

        print(f"Second Turn Latency: {second_turn_duration:.2f} seconds", flush=True)
        print("\n" + "=" * 80, flush=True)
        print(" PHASE 5: FINAL MODEL SYNTHESIS", flush=True)
        print("=" * 80, flush=True)
        print(f"Final Answer:\n{final_content.strip()}", flush=True)

        return LoopTraceReport(
            prompt=user_prompt,
            tool_choice=tool_choice,
            initial_request_duration_sec=initial_request_duration,
            total_duration_sec=total_elapsed,
            tool_calls_requested=len(tool_calls),
            executed_steps=executed_steps,
            final_answer=final_content,
            messages_history=messages
        )
