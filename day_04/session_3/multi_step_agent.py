"""
multi_step_agent.py
===================
Autonomous Multi-Step Tool Chaining Agent (Day 4 - Session 3)

Features:
1. Multi-Step Loop: Repeatedly calls tools until the problem is fully resolved.
2. Result Passing: Serializes observations and passes them back into conversation history.
3. Detailed Step Logging: Captures every reasoning step, tool invocation, observation, and token metric.
4. Token Growth & History Compaction: Dynamically tracks context growth and supports compaction.
5. Error Resilience: Automatic exponential backoff for API rate limits and robust observation routing.
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import os
import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv
from openai import OpenAI

from tools import dispatch_tool_call
from schemas import TOOLS_SCHEMA
from history_manager import ConversationHistoryManager

load_dotenv()

SYSTEM_PROMPT = """You are an autonomous enterprise AI agent equipped with tools to query databases, read project files, perform mathematical calculations, and send notification emails.

Guidelines:
1. Break down complex user requests into discrete, logical tool calls in sequence.
2. When the user asks for information from multiple sources, first retrieve the data before performing calculations or sending notifications.
3. Never guess arithmetic or financial calculations—always use the 'calculator' tool for mathematical accuracy.
4. When a tool returns an observation, inspect it carefully and use its fields (e.g. salary, policy rules) to determine your next action.
5. Once all steps (data retrieval, policy checking, calculation, and notification) are completed, synthesize a clear, comprehensive final answer for the user."""


@dataclass
class StepLog:
    step_number: int
    turn_type: str  # "TOOL_REQUEST", "TOOL_OBSERVATION", "FINAL_ANSWER"
    tool_name: Optional[str] = None
    arguments: Optional[Dict[str, Any]] = None
    observation_snippet: Optional[str] = None
    tokens_at_step: int = 0
    duration_sec: float = 0.0


@dataclass
class ExecutionTelemetry:
    user_query: str
    total_steps: int
    tools_executed: List[str]
    step_logs: List[StepLog]
    token_growth_curve: List[Dict[str, Any]]
    final_answer: str
    execution_time_sec: float
    compaction_applied: bool = False


class MultiStepToolAgent:
    """
    Orchestrates multi-turn tool execution with full audit logging and token tracking.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        max_turns: int = 8,
        enable_compaction: bool = False,
        compaction_threshold: int = 1800,
    ):
        self.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
        self.model_name = model_name or os.getenv("OPENAI_MODEL", "gemini-flash-latest")
        self.max_turns = max_turns
        self.enable_compaction = enable_compaction
        self.compaction_threshold = compaction_threshold

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=45.0,
        )

    def _call_api_with_retry(self, messages: List[Dict[str, Any]]) -> Any:
        """Invokes Chat Completions API with exponential backoff on 429 rate limits."""
        backoff = 8.0
        for attempt in range(1, 5):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    tools=TOOLS_SCHEMA,
                    tool_choice="auto",
                    temperature=0.0,
                )
                return response
            except Exception as e:
                err_str = str(e)
                is_transient = (
                    "429" in err_str
                    or "503" in err_str
                    or "quota" in err_str.lower()
                    or "timeout" in err_str.lower()
                    or "unavailable" in err_str.lower()
                    or "demand" in err_str.lower()
                )
                if is_transient:
                    if attempt == 4:
                        raise e
                    print(f"  [Notice] Transient API status. Pausing {backoff:.1f}s before retry ({attempt}/3)...")
                    time.sleep(backoff)
                    backoff *= 1.5
                else:
                    raise e

    def run(self, query: str) -> ExecutionTelemetry:
        """
        Executes the autonomous multi-step loop over the given query.
        Logs every step, handles tool results, and tracks token growth.
        """
        start_time = time.time()
        history = ConversationHistoryManager(
            system_prompt=SYSTEM_PROMPT,
            token_compaction_threshold=self.compaction_threshold
        )
        history.add_user_message(query)

        step_logs: List[StepLog] = []
        tools_executed: List[str] = []
        step_counter = 0
        compaction_done = False

        print("\n" + "=" * 80)
        print(">>> INITIATING MULTI-STEP AGENT LOOP")
        print(f"User Task: {query}")
        print("=" * 80)

        for turn in range(1, self.max_turns + 1):
            # Check for history summarization / compaction policy
            if self.enable_compaction and not compaction_done and history.should_compact():
                print("\n[!] Context Compaction threshold reached. Compacting older history...")
                compaction_result = history.compact_history()
                compaction_done = True
                print(f"   -> Reduced tokens by {compaction_result['reduction_percentage']}% "
                      f"({compaction_result['initial_tokens']} -> {compaction_result['final_tokens']})")

            current_tokens = history.get_total_tokens()
            print(f"\n[Turn {turn}] Sending context to LLM ({len(history.messages)} messages, ~{current_tokens} tokens)...")
            call_start = time.time()

            response = self._call_api_with_retry(history.get_messages())
            call_duration = time.time() - call_start

            choice = response.choices[0]
            message = choice.message
            tool_calls = message.tool_calls

            # Case A: Model requests one or more tool calls
            if tool_calls:
                history.add_assistant_message(message)

                for tc in tool_calls:
                    step_counter += 1
                    tool_name = tc.function.name
                    raw_args = tc.function.arguments
                    try:
                        args_dict = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                    except Exception:
                        args_dict = {"raw": raw_args}

                    tools_executed.append(tool_name)
                    print(f"  [Step {step_counter}] Requesting Tool -> '{tool_name}'")
                    print(f"     Arguments: {json.dumps(args_dict)}")

                    step_logs.append(StepLog(
                        step_number=step_counter,
                        turn_type="TOOL_REQUEST",
                        tool_name=tool_name,
                        arguments=args_dict,
                        tokens_at_step=history.get_total_tokens(),
                        duration_sec=round(call_duration, 2)
                    ))

                    # Execute the tool locally
                    exec_start = time.time()
                    obs_str = dispatch_tool_call(tool_name, args_dict)
                    exec_duration = time.time() - exec_start

                    # Pass result back into context
                    history.add_tool_result(
                        tool_call_id=tc.id,
                        tool_name=tool_name,
                        result_json_str=obs_str
                    )

                    # Log the observation step
                    step_counter += 1
                    obs_snippet = obs_str[:220] + ("..." if len(obs_str) > 220 else "")
                    print(f"  [Step {step_counter}] Observation ({tool_name}) -> {obs_snippet}")

                    step_logs.append(StepLog(
                        step_number=step_counter,
                        turn_type="TOOL_OBSERVATION",
                        tool_name=tool_name,
                        observation_snippet=obs_snippet,
                        tokens_at_step=history.get_total_tokens(),
                        duration_sec=round(exec_duration, 3)
                    ))

                # Pacing pause to stay within free-tier RPM limits
                time.sleep(1.5)

            # Case B: Model completes the loop and produces final answer
            else:
                final_text = message.content or ""
                history.add_assistant_message(message)
                step_counter += 1

                step_logs.append(StepLog(
                    step_number=step_counter,
                    turn_type="FINAL_ANSWER",
                    observation_snippet=final_text[:200] + ("..." if len(final_text) > 200 else ""),
                    tokens_at_step=history.get_total_tokens(),
                    duration_sec=round(call_duration, 2)
                ))

                total_elapsed = time.time() - start_time
                print("\n" + "=" * 80)
                print("FINAL ANSWER SYNTHESIZED BY AGENT")
                print("=" * 80)
                print(final_text)
                print("=" * 80)

                return ExecutionTelemetry(
                    user_query=query,
                    total_steps=step_counter,
                    tools_executed=tools_executed,
                    step_logs=step_logs,
                    token_growth_curve=history.token_history,
                    final_answer=final_text,
                    execution_time_sec=round(total_elapsed, 2),
                    compaction_applied=compaction_done,
                )

        raise RuntimeError(f"Agent exceeded maximum allowed turns ({self.max_turns}) without completing the task.")
