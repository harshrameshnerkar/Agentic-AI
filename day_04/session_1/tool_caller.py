"""
tool_caller.py
==============
The Request -> Execute -> Return Result Loop (Day 4 - Session 1)

Responsibilities:
1. Implements the complete 3-turn Tool Calling Execution Loop:
   - Turn 1: Client sends user prompt + JSON schemas with tool_choice.
   - Turn 2: Client detects `tool_calls`, dispatches local Python execution, and serializes results.
   - Turn 3: Client injects tool message with `tool_call_id` back to the model for final answer synthesis.
2. Captures full observability telemetry (tool name, parsed arguments, local execution result, latencies).
3. Handles both tool-augmented questions and conversational direct responses seamlessly.

Why the Model Never Runs Code Itself:
- The model is a text predictor, NOT an operating system.
- When it encounters a query requiring outside data or computation, it pauses text generation,
  outputs an instruction containing the function name and arguments, and sets finish_reason="tool_calls".
- The HOST RUNTIME (this script) executes the real Python code and passes the result back.
"""

import os
import time
import json
from typing import List, Dict, Any, Optional, Union
from openai import OpenAI
from dotenv import load_dotenv

from schemas import get_available_tools
from tools import execute_tool

load_dotenv()

BASE_URL = os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gemini-3.5-flash-lite")


class ToolCallTelemetry:
    """
    Observability container tracking the entire tool execution lifecycle.
    """
    def __init__(
        self,
        query: str,
        tool_called: Optional[str],
        tool_arguments: Optional[Dict[str, Any]],
        tool_raw_output: Optional[str],
        final_answer: str,
        turn_count: int,
        tool_choice: Union[str, Dict[str, Any]],
        latency_ms: float,
        messages_history: List[Dict[str, Any]],
    ):
        self.query = query
        self.tool_called = tool_called
        self.tool_arguments = tool_arguments or {}
        self.tool_raw_output = tool_raw_output
        self.final_answer = final_answer
        self.turn_count = turn_count
        self.tool_choice = tool_choice
        self.latency_ms = latency_ms
        self.messages_history = messages_history

    def __repr__(self) -> str:
        tool_status = f"called '{self.tool_called}'" if self.tool_called else "no tool called (direct response)"
        return f"<ToolCallTelemetry: {tool_status} | turns={self.turn_count} | {self.latency_ms:.1f}ms>"


class ToolCallingAgent:
    """
    Manages the end-to-end tool-calling lifecycle using the OpenAI/Gemini chat completion API.
    """
    def __init__(
        self,
        model: str = MODEL,
        base_url: str = BASE_URL,
        api_key: Optional[str] = API_KEY,
    ):
        self.model = model
        self.tools = get_available_tools()
        self.client = OpenAI(base_url=base_url, api_key=api_key)

    def _call_with_retry(self, **kwargs) -> Any:
        """Executes chat completion with automatic backoff for 429 rate limits."""
        import re
        max_retries = 4
        delay = 8.0
        for attempt in range(1, max_retries + 1):
            try:
                return self.client.chat.completions.create(**kwargs)
            except Exception as e:
                err_str = str(e)
                is_rate_limit = (
                    "429" in err_str
                    or "RESOURCE_EXHAUSTED" in err_str
                    or "RateLimitError" in type(e).__name__
                    or "Quota exceeded" in err_str
                )
                if is_rate_limit and attempt < max_retries:
                    match = re.search(r"retry in (\d+(?:\.\d+)?)s", err_str)
                    sleep_sec = float(match.group(1)) + 1.5 if match else delay
                    print(f"\n  [Rate Limit 429] Free-tier RPM threshold reached. Pacing {sleep_sec:.1f}s before retry (Attempt {attempt}/{max_retries})...")
                    time.sleep(sleep_sec)
                    delay *= 1.5
                else:
                    raise

    def run(
        self,
        user_prompt: str,
        tool_choice: Union[str, Dict[str, Any]] = "auto",
        system_instruction: Optional[str] = None,
    ) -> ToolCallTelemetry:
        """
        Executes the Request -> Execute -> Return cycle.
        
        Args:
            user_prompt: The prompt from the user.
            tool_choice: Tool selection behavior ('auto', 'none', 'required', or forced function dict).
            system_instruction: Optional system instruction prompt.
        """
        t_start = time.perf_counter()
        messages: List[Dict[str, Any]] = []

        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})

        messages.append({"role": "user", "content": user_prompt})

        # -------------------------------------------------------------------
        # TURN 1: Initial Request (Prompt + Tool Schemas -> Model)
        # -------------------------------------------------------------------
        response = self._call_with_retry(
            model=self.model,
            messages=messages,
            tools=self.tools,
            tool_choice=tool_choice,
            temperature=0.0,
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        # Case A: Model answered directly without invoking any tool
        if not tool_calls:
            direct_answer = response_message.content or ""
            latency_ms = (time.perf_counter() - t_start) * 1000
            messages.append({"role": "assistant", "content": direct_answer})

            return ToolCallTelemetry(
                query=user_prompt,
                tool_called=None,
                tool_arguments=None,
                tool_raw_output=None,
                final_answer=direct_answer,
                turn_count=1,
                tool_choice=tool_choice,
                latency_ms=round(latency_ms, 1),
                messages_history=messages,
            )

        # -------------------------------------------------------------------
        # TURN 2: Local Code Execution (Model Requested Tool -> Python Runs It)
        # -------------------------------------------------------------------
        # Append the assistant's message (which includes tool_calls) into history
        messages.append(response_message)

        tool_called_name: Optional[str] = None
        tool_arguments_parsed: Dict[str, Any] = {}
        tool_raw_output_str: str = ""

        # Process each tool call requested by the model
        for tool_call in tool_calls:
            tool_called_name = tool_call.function.name
            raw_args = tool_call.function.arguments

            # Safely parse JSON arguments string generated by the model
            try:
                tool_arguments_parsed = json.loads(raw_args)
            except json.JSONDecodeError:
                tool_arguments_parsed = {"raw": raw_args}

            # Execute the pure Python function locally
            tool_raw_output_str = execute_tool(tool_called_name, tool_arguments_parsed)

            # Append the tool execution response with the matching tool_call_id
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_raw_output_str,
            })

        # -------------------------------------------------------------------
        # TURN 3: Final Synthesis (Tool Results -> Model -> Conversational Answer)
        # -------------------------------------------------------------------
        follow_up_response = self._call_with_retry(
            model=self.model,
            messages=messages,
            tools=self.tools,
            temperature=0.0,
        )

        final_answer = follow_up_response.choices[0].message.content or ""
        messages.append({"role": "assistant", "content": final_answer})
        latency_ms = (time.perf_counter() - t_start) * 1000

        return ToolCallTelemetry(
            query=user_prompt,
            tool_called=tool_called_name,
            tool_arguments=tool_arguments_parsed,
            tool_raw_output=tool_raw_output_str,
            final_answer=final_answer,
            turn_count=3,
            tool_choice=tool_choice,
            latency_ms=round(latency_ms, 1),
            messages_history=messages,
        )


if __name__ == "__main__":
    print("=" * 80)
    print(" TOOL CALLING AGENT: DEMO OF THE 3-TURN EXECUTION LOOP")
    print("=" * 80)

    agent = ToolCallingAgent()

    test_queries = [
        "What is 345 multiplied by 28?",
        "What is the current time in UTC right now?",
        "What is the time in IST (Indian Standard Time)?",
        "Hello there! Can you explain what a prime number is in one sentence?",
    ]

    for q in test_queries:
        print(f"\n--- [USER QUERY]: '{q}' ---")
        telemetry = agent.run(q, tool_choice="auto")
        
        if telemetry.tool_called:
            print(f"  [Turn 1] Model Requested Tool: '{telemetry.tool_called}'")
            print(f"  [Turn 2] Parsed Arguments:     {telemetry.tool_arguments}")
            print(f"  [Turn 2] Local Python Output:  {telemetry.tool_raw_output}")
            print(f"  [Turn 3] Final Synthesized Answer:\n{telemetry.final_answer}")
        else:
            print(f"  [Direct Response - No Tool Needed]:\n{telemetry.final_answer}")
            
        print(f"  [Telemetry]: {telemetry.turn_count} turns | {telemetry.latency_ms:.1f}ms")
        time.sleep(2.0)
