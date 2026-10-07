"""
Reliable Agent Implementation with Comprehensive Safety Controls.
Integrates:
- Max Iteration Caps
- Loop & Repeated-Action Detection
- Wall-Clock Tool Execution Timeouts
- Retries with Exponential Backoff
- Human-in-the-Loop (HITL) Mandatory Approval Gates
- Structured Audit Logging (JSONL)
- Graceful Degradation
"""

import os
import json
import time
import uuid
from typing import Any, Callable, Dict, List, Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

from guardrails import (
    ApprovalDecision,
    ApprovalGate,
    IterationCapGuard,
    LoopDetector,
    RetryHandler,
    StructuredAuditLogger,
    TimeoutGuard,
)
from tools import TOOL_FUNCTIONS, TOOL_SCHEMAS

# Load environment configuration
load_dotenv(Path(__file__).resolve().parent / ".env")

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gemini-3.1-flash-lite")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")


SYSTEM_PROMPT = """You are a highly reliable Incident Response Agent for production cloud services.
Your duties:
1. Inspect incidents using available tools.
2. Analyze root-causes and system states.
3. If an incident requires stakeholder notification, prepare an email using 'send_email'.
   NOTE: 'send_email' is a high-consequence action that will be paused for human approval.
4. If a tool fails, times out, or is denied by the human operator, adapt gracefully and provide the best possible operational assessment.
5. Always be concise, factual, and professional.
"""


class ReliableAgent:
    """
    Production-grade agent wrapping ReAct logic with 7 core reliability guardrails.
    """

    def __init__(
        self,
        max_iterations: int = 5,
        tool_timeout_seconds: float = 2.0,
        max_repeated_calls: int = 2,
        approval_callback: Optional[Callable[[Dict[str, Any]], Tuple[ApprovalDecision, Optional[Dict[str, Any]], str]]] = None,
        auto_interactive_cli: bool = False,
        audit_log_path: Optional[Path] = None,
    ):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY or GEMINI_API_KEY must be configured in environment or .env file.")

        self.client = OpenAI(
            base_url=OPENAI_BASE_URL,
            api_key=OPENAI_API_KEY,
        )
        self.model = OPENAI_MODEL
        self.max_iterations = max_iterations
        self.tool_timeout_seconds = tool_timeout_seconds

        # Initialize Guardrails
        self.iteration_guard = IterationCapGuard(max_iterations=max_iterations)
        self.loop_detector = LoopDetector(max_consecutive_repeats=max_repeated_calls)
        self.timeout_guard = TimeoutGuard(default_timeout_seconds=tool_timeout_seconds)
        self.retry_handler = RetryHandler(max_retries=3, initial_delay=1.0)
        self.approval_gate = ApprovalGate(
            approval_callback=approval_callback,
            auto_interactive_cli=auto_interactive_cli,
        )
        self.audit_logger = StructuredAuditLogger(log_path=audit_log_path)

    def run(self, user_prompt: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes the agent loop against user_prompt with full reliability controls.
        Returns a structured dictionary containing final response, execution metrics,
        and guardrail intervention logs.
        """
        session_id = session_id or f"sess_{str(uuid.uuid4())[:8]}"
        self.iteration_guard.reset()
        self.loop_detector.reset()

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        self.audit_logger.log_event(
            event_type="USER_PROMPT",
            session_id=session_id,
            turn_index=0,
            payload={"prompt": user_prompt, "max_iterations": self.max_iterations},
        )

        turn_index = 0
        final_text = ""
        loop_interrupted = False
        cap_exceeded = False
        approvals_requested: List[Dict[str, Any]] = []

        while True:
            turn_index += 1

            # 1. ENFORCE ITERATION CAP
            if not self.iteration_guard.start_turn():
                cap_exceeded = True
                self.audit_logger.log_event(
                    event_type="CAP_EXCEEDED",
                    session_id=session_id,
                    turn_index=turn_index,
                    payload={
                        "max_iterations": self.max_iterations,
                        "message": f"Execution halted: Agent exceeded hard cap of {self.max_iterations} iterations.",
                    },
                )
                final_text = (
                    f"⚠️ [GRACEFUL DEGRADATION: Iteration Cap Reached]\n"
                    f"The agent reached the maximum limit of {self.max_iterations} execution cycles. "
                    f"Partial work completed. Aborting further automated reasoning to prevent runaway execution."
                )
                break

            # 2. CALL LLM WITH EXPONENTIAL BACKOFF RETRY
            start_llm = time.monotonic()
            try:
                response = self.retry_handler.execute(
                    self.client.chat.completions.create,
                    model=self.model,
                    messages=messages,
                    tools=TOOL_SCHEMAS,
                    tool_choice="auto",
                    temperature=0.1,
                )
            except Exception as e:
                self.audit_logger.log_event(
                    event_type="LLM_FAILURE",
                    session_id=session_id,
                    turn_index=turn_index,
                    payload={"error": str(e)},
                )
                final_text = f"⚠️ [GRACEFUL DEGRADATION: LLM Service Error] Failed to generate response after retries: {e}"
                break

            llm_latency_ms = (time.monotonic() - start_llm) * 1000
            msg = response.choices[0].message
            content = msg.content or ""
            tool_calls = getattr(msg, "tool_calls", None) or []

            # Append the original message object directly to preserve provider-specific metadata (such as Gemini thought_signature)
            messages.append(msg)

            # If no tool calls, the model has arrived at its final answer!
            if not tool_calls:
                final_text = content
                self.audit_logger.log_event(
                    event_type="AGENT_RESPONSE",
                    session_id=session_id,
                    turn_index=turn_index,
                    payload={"response": final_text},
                    latency_ms=llm_latency_ms,
                )
                break

            # 3. EXECUTE REQUESTED TOOLS WITH GUARDRAILS
            for tc in tool_calls:
                tool_name = tc.function.name
                raw_args = tc.function.arguments

                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                except Exception:
                    args = {"raw": raw_args}

                # --- 3a. LOOP & REPEATED-ACTION DETECTION ---
                is_loop, loop_reason = self.loop_detector.record_and_check(tool_name, args)
                if is_loop:
                    loop_interrupted = True
                    self.audit_logger.log_event(
                        event_type="LOOP_DETECTED",
                        session_id=session_id,
                        turn_index=turn_index,
                        payload={"tool": tool_name, "args": args, "reason": loop_reason},
                    )
                    observation = {
                        "error": "LoopDetected",
                        "message": loop_reason,
                        "directive": "You have repeated this action. Do NOT call this tool again with these parameters. Summarize your findings now.",
                    }
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": json.dumps(observation),
                        }
                    )
                    continue

                # --- 3b. HUMAN-IN-THE-LOOP (HITL) APPROVAL GATE ---
                if self.approval_gate.is_critical(tool_name):
                    self.audit_logger.log_event(
                        event_type="APPROVAL_REQUIRED",
                        session_id=session_id,
                        turn_index=turn_index,
                        payload={"tool": tool_name, "arguments": args},
                    )

                    decision, effective_args, note = self.approval_gate.request_approval(
                        tool_name=tool_name,
                        arguments=args,
                        context_summary=f"Incident resolution workflow turn {turn_index}",
                    )
                    approvals_requested.append(
                        {
                            "tool": tool_name,
                            "decision": decision.value,
                            "note": note,
                            "arguments": effective_args,
                        }
                    )

                    if decision == ApprovalDecision.REJECTED:
                        self.audit_logger.log_event(
                            event_type="APPROVAL_DENIED",
                            session_id=session_id,
                            turn_index=turn_index,
                            payload={"tool": tool_name, "decision": decision.value, "reason": note},
                        )
                        observation = {
                            "status": "APPROVAL_REJECTED",
                            "message": f"MANDATORY HUMAN APPROVAL REJECTED: Operator denied permission to execute '{tool_name}'. Reason: {note}",
                            "directive": "Do NOT attempt to call this tool again. Inform the user that the action was rejected by the operator and provide the incident status in chat.",
                        }
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tc.id,
                                "content": json.dumps(observation),
                            }
                        )
                        continue

                    # If approved or modified:
                    self.audit_logger.log_event(
                        event_type="APPROVAL_GRANTED",
                        session_id=session_id,
                        turn_index=turn_index,
                        payload={"tool": tool_name, "decision": decision.value, "effective_arguments": effective_args, "note": note},
                    )
                    args = effective_args

                # --- 3c. TIMEOUT GUARD & TOOL EXECUTION ---
                func = TOOL_FUNCTIONS.get(tool_name)
                if not func:
                    observation = {"error": f"Tool '{tool_name}' not implemented in registry."}
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": json.dumps(observation),
                        }
                    )
                    continue

                success, tool_result, elapsed_sec = self.timeout_guard.execute_with_timeout(
                    func=func,
                    kwargs=args,
                    timeout_seconds=self.tool_timeout_seconds,
                )

                if not success:
                    # Tool timed out or raised unhandled exception
                    self.audit_logger.log_event(
                        event_type="TOOL_TIMEOUT" if tool_result.get("error") == "TimeoutError" else "TOOL_ERROR",
                        session_id=session_id,
                        turn_index=turn_index,
                        payload={"tool": tool_name, "error": tool_result, "elapsed_seconds": elapsed_sec},
                        latency_ms=elapsed_sec * 1000,
                    )
                    observation = tool_result
                else:
                    self.audit_logger.log_event(
                        event_type="TOOL_EXECUTION",
                        session_id=session_id,
                        turn_index=turn_index,
                        payload={"tool": tool_name, "result": tool_result, "elapsed_seconds": elapsed_sec},
                        latency_ms=elapsed_sec * 1000,
                    )
                    observation = tool_result

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(observation),
                    }
                )

        return {
            "session_id": session_id,
            "turns_executed": turn_index,
            "final_response": final_text,
            "cap_exceeded": cap_exceeded,
            "loop_interrupted": loop_interrupted,
            "approvals_requested": approvals_requested,
            "audit_events_count": len(self.audit_logger.events),
        }
