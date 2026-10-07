"""
agent.py
========
Tool-Augmented Autonomous Agent (Day 4 - Session 2)

Responsibilities:
1. Multi-Step Execution Loop:
   - Capable of executing multi-turn tool chains (e.g. Query Database ➔ Extract Email ➔ Send Email).
2. Autonomous Error Self-Correction:
   - When a tool returns an error observation (e.g. SQL syntax error, bad column name, invalid email),
     the agent reads the error, self-corrects its query or arguments, and re-executes!
3. Rate-Limit Resiliency:
   - Includes backoff pacing for free-tier Gemini API quotas.
"""

import os
import time
import json
import re
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

from schemas import get_all_tools
from tool_runtime import dispatch_tool

load_dotenv()

BASE_URL = os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gemini-3.5-flash-lite")


class AgentStepTelemetry:
    """Telemetry capturing a single action step in the agent's execution."""
    def __init__(self, step_number: int, tool_name: str, arguments: Dict[str, Any], observation: Dict[str, Any]):
        self.step_number = step_number
        self.tool_name = tool_name
        self.arguments = arguments
        self.observation = observation


class AgentRunResult:
    """Comprehensive container summarizing the multi-step agent execution."""
    def __init__(
        self,
        query: str,
        final_answer: str,
        steps: List[AgentStepTelemetry],
        turn_count: int,
        latency_ms: float,
        self_corrected: bool = False,
    ):
        self.query = query
        self.final_answer = final_answer
        self.steps = steps
        self.turn_count = turn_count
        self.latency_ms = latency_ms
        self.self_corrected = self_corrected


class EnterpriseToolAgent:
    """
    Autonomous agent equipped with the 4 production tools:
    - web_search
    - read_file
    - query_database
    - send_email
    """
    def __init__(
        self,
        model: str = MODEL,
        base_url: str = BASE_URL,
        api_key: Optional[str] = API_KEY,
        max_iterations: int = 5,
    ):
        self.model = model
        self.tools = get_all_tools()
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.max_iterations = max_iterations

    def _call_with_retry(self, **kwargs) -> Any:
        """Executes chat completion with automatic backoff for 429 rate limits."""
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
                    print(f"\n  [Rate Limit 429] Pacing {sleep_sec:.1f}s before retry (Attempt {attempt}/{max_retries})...")
                    time.sleep(sleep_sec)
                    delay *= 1.5
                else:
                    raise

    def run(self, user_prompt: str) -> AgentRunResult:
        """
        Executes the agent loop:
        Repeatedly prompts the model until it finishes with a final text answer
        or reaches max_iterations.
        """
        t_start = time.perf_counter()
        messages: List[Dict[str, Any]] = [
            {
                "role": "system",
                "content": (
                    "You are an enterprise AI assistant with access to 4 production tools: "
                    "web_search, read_file, query_database, and send_email. "
                    "When answering user requests, call the appropriate tools. "
                    "If a tool returns an error observation (e.g. bad column name or invalid email format), "
                    "read the error observation, correct your query or parameters, and call the tool again. "
                    "Never invent or hallucinate data that can be queried from the database or files."
                ),
            },
            {"role": "user", "content": user_prompt},
        ]

        steps: List[AgentStepTelemetry] = []
        turn_count = 0
        has_self_corrected = False

        for iteration in range(1, self.max_iterations + 1):
            turn_count += 1
            response = self._call_with_retry(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                temperature=0.0,
            )

            assistant_msg = response.choices[0].message
            tool_calls = assistant_msg.tool_calls

            # Case A: Model finished thinking and provided final conversational answer
            if not tool_calls:
                final_text = assistant_msg.content or ""
                latency_ms = (time.perf_counter() - t_start) * 1000
                return AgentRunResult(
                    query=user_prompt,
                    final_answer=final_text,
                    steps=steps,
                    turn_count=turn_count,
                    latency_ms=round(latency_ms, 1),
                    self_corrected=has_self_corrected,
                )

            # Case B: Model requested one or more tool calls
            messages.append(assistant_msg)

            for tool_call in tool_calls:
                fn_name = tool_call.function.name
                raw_args = tool_call.function.arguments

                try:
                    parsed_args = json.loads(raw_args)
                except json.JSONDecodeError:
                    parsed_args = {"raw": raw_args}

                # Dispatch local tool
                tool_result_str = dispatch_tool(fn_name, parsed_args)
                tool_result_dict = json.loads(tool_result_str)

                # Check if this step was an error observation that required correction
                if tool_result_dict.get("status") == "error":
                    has_self_corrected = True

                steps.append(
                    AgentStepTelemetry(
                        step_number=len(steps) + 1,
                        tool_name=fn_name,
                        arguments=parsed_args,
                        observation=tool_result_dict,
                    )
                )

                # Send tool observation back to conversation history
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result_str,
                })

        # Max iterations reached fallback
        latency_ms = (time.perf_counter() - t_start) * 1000
        return AgentRunResult(
            query=user_prompt,
            final_answer="Agent reached maximum iteration limit before completing the task.",
            steps=steps,
            turn_count=turn_count,
            latency_ms=round(latency_ms, 1),
            self_corrected=has_self_corrected,
        )


if __name__ == "__main__":
    agent = EnterpriseToolAgent()
    print("=== Testing EnterpriseToolAgent on Multi-Step Prompt ===")
    prompt = "Who is the Lead AI Researcher in the database, and what is their salary?"
    res = agent.run(prompt)
    print(f"\nFinal Answer:\n{res.final_answer}")
    print(f"\nSteps Executed: {len(res.steps)}")
    for s in res.steps:
        print(f"  Step #{s.step_number}: Tool '{s.tool_name}' with {s.arguments}")
