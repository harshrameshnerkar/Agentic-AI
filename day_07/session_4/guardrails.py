"""
Reliability and Control Guardrails for Autonomous Agents.
Implements:
1. Max iteration caps
2. Loop and repeated-action detection
3. Tool execution timeouts
4. Retries with exponential backoff & jitter
5. Human-in-the-loop (HITL) approval gates
6. Structured audit logging
7. Graceful degradation mechanisms
"""

import json
import time
import uuid
import hashlib
import random
import logging
from enum import Enum
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError


# Configure structured logging
logger = logging.getLogger("ReliabilityGuardrails")
logger.setLevel(logging.INFO)


class ApprovalDecision(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    MODIFIED = "MODIFIED"


class IterationCapGuard:
    """
    Prevents runaway agent loops and unbounded token expenditure by
    enforcing a strict hard limit on ReAct reasoning-action turns.
    """

    def __init__(self, max_iterations: int = 5):
        if max_iterations < 1:
            raise ValueError("max_iterations must be at least 1")
        self.max_iterations = max_iterations
        self.current_iteration = 0

    def start_turn(self) -> bool:
        """
        Advances the turn counter.
        Returns True if turn is within limit, False if iteration cap is breached.
        """
        self.current_iteration += 1
        return self.current_iteration <= self.max_iterations

    def is_exceeded(self) -> bool:
        return self.current_iteration > self.max_iterations

    def remaining_iterations(self) -> int:
        return max(0, self.max_iterations - self.current_iteration)

    def reset(self):
        self.current_iteration = 0


class LoopDetector:
    """
    Detects repeated actions, parameter flip-flopping, and circular cycles.
    Maintains a rolling signature history to prevent infinite ping-pong patterns.
    """

    def __init__(self, max_consecutive_repeats: int = 2, cycle_window_size: int = 6):
        self.max_consecutive_repeats = max_consecutive_repeats
        self.cycle_window_size = cycle_window_size
        self.history: List[str] = []

    @staticmethod
    def _compute_action_signature(tool_name: str, args: Dict[str, Any]) -> str:
        """Computes a deterministic hash of the action name and normalized arguments."""
        try:
            serialized_args = json.dumps(args, sort_keys=True, default=str)
        except Exception:
            serialized_args = str(args)
        raw_sig = f"{tool_name}:{serialized_args}"
        digest = hashlib.sha256(raw_sig.encode("utf-8")).hexdigest()[:12]
        return f"{tool_name}[{digest}]"

    def record_and_check(self, tool_name: str, args: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Records the candidate action and inspects for repetition or cycles.
        Returns: (is_loop_detected, reason)
        """
        signature = self._compute_action_signature(tool_name, args)
        self.history.append(signature)

        # Check 1: Identical consecutive actions
        if len(self.history) >= self.max_consecutive_repeats:
            recent_slice = self.history[-self.max_consecutive_repeats :]
            if all(sig == signature for sig in recent_slice):
                return True, (
                    f"Repetitive Action Loop Detected: Tool '{tool_name}' was requested {self.max_consecutive_repeats} "
                    f"times consecutively with identical arguments ({signature}). Halting repetition."
                )

        # Check 2: Cycle detection (e.g. A -> B -> A -> B)
        n = len(self.history)
        if n >= 4:
            # Check length-2 cycles (A, B, A, B)
            if self.history[-1] == self.history[-3] and self.history[-2] == self.history[-4]:
                return True, (
                    f"Oscillating 2-Step Cycle Detected: Alternate loop pattern between "
                    f"'{self.history[-1]}' and '{self.history[-2]}' detected. Halting oscillation."
                )

        return False, None

    def reset(self):
        self.history.clear()


class TimeoutGuard:
    """
    Executes tool operations under strict wall-clock time limits using
    worker thread pools. Ensures external hanging calls do not freeze the agent.
    """

    def __init__(self, default_timeout_seconds: float = 3.0):
        self.default_timeout_seconds = default_timeout_seconds

    def execute_with_timeout(
        self,
        func: Callable,
        kwargs: Dict[str, Any],
        timeout_seconds: Optional[float] = None,
    ) -> Tuple[bool, Any, float]:
        """
        Executes a callable with a strict timeout.
        Returns: (success, result_or_error_dict, elapsed_time_seconds)
        """
        effective_timeout = timeout_seconds or self.default_timeout_seconds
        start_time = time.monotonic()

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func, **kwargs)
            try:
                result = future.result(timeout=effective_timeout)
                elapsed = time.monotonic() - start_time
                return True, result, elapsed
            except FutureTimeoutError:
                elapsed = time.monotonic() - start_time
                error_payload = {
                    "error": "TimeoutError",
                    "message": f"Execution timed out after {effective_timeout:.2f} seconds (Elapsed: {elapsed:.2f}s).",
                    "recovered_via": "graceful_timeout_guard",
                }
                return False, error_payload, elapsed
            except Exception as e:
                elapsed = time.monotonic() - start_time
                error_payload = {
                    "error": type(e).__name__,
                    "message": str(e),
                }
                return False, error_payload, elapsed


class RetryHandler:
    """
    Implements robust exponential backoff with jitter for transient errors
    (RateLimit 429, Network dropped packets, 5xx server overloads).
    """

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_multiplier: float = 2.0,
        jitter: float = 0.5,
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.backoff_multiplier = backoff_multiplier
        self.jitter = jitter

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        last_error = None
        current_delay = self.initial_delay

        for attempt in range(1, self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                err_str = str(e).lower()
                is_transient = any(
                    x in err_str for x in ["rate", "429", "timeout", "connection", "overloaded", "503", "500"]
                )
                if not is_transient or attempt == self.max_retries:
                    raise e

                sleep_duration = current_delay + random.uniform(0, self.jitter)
                logger.warning(
                    f"[RetryHandler] Attempt {attempt}/{self.max_retries} failed ({type(e).__name__}). "
                    f"Backing off for {sleep_duration:.2f}s before retry..."
                )
                time.sleep(sleep_duration)
                current_delay *= self.backoff_multiplier

        raise last_error


class ApprovalGate:
    """
    Human-in-the-Loop (HITL) safety checkpoint.
    Intercepts sensitive, high-impact actions (e.g. sending emails, deleting data,
    running migrations) and pauses execution until approved by human operator.
    """

    CRITICAL_TOOLS = {"send_email", "delete_database", "execute_payment", "deploy_production"}

    def __init__(
        self,
        approval_callback: Optional[Callable[[Dict[str, Any]], Tuple[ApprovalDecision, Optional[Dict[str, Any]], str]]] = None,
        auto_interactive_cli: bool = False,
    ):
        self.approval_callback = approval_callback
        self.auto_interactive_cli = auto_interactive_cli

    def is_critical(self, tool_name: str) -> bool:
        return tool_name in self.CRITICAL_TOOLS

    def request_approval(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context_summary: str = "",
    ) -> Tuple[ApprovalDecision, Dict[str, Any], str]:
        """
        Pauses and evaluates whether the critical tool call may proceed.
        Returns: (decision, effective_arguments, reviewer_feedback_or_reason)
        """
        request_id = str(uuid.uuid4())[:8]
        approval_payload = {
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool_name": tool_name,
            "arguments": arguments,
            "context_summary": context_summary,
            "risk_level": "HIGH_SIDE_EFFECT (External Dispatch)",
        }

        # Case 1: Custom programmatic callback provided (e.g. for testing or Slack bot integration)
        if self.approval_callback:
            decision, modified_args, note = self.approval_callback(approval_payload)
            effective_args = modified_args if (decision == ApprovalDecision.MODIFIED and modified_args) else arguments
            return decision, effective_args, note

        # Case 2: Interactive CLI prompt
        if self.auto_interactive_cli:
            print("\n" + "=" * 60)
            print(f"🛑 [HITL APPROVAL GATE] Mandatory Approval Required for '{tool_name}'")
            print(f"Request ID: {request_id}")
            print(f"Arguments: {json.dumps(arguments, indent=2)}")
            print(f"Context: {context_summary}")
            print("=" * 60)
            ans = input("Approve execution? [y/N/reason]: ").strip()
            if ans.lower() in ("y", "yes"):
                return ApprovalDecision.APPROVED, arguments, "Approved interactively by console operator."
            else:
                reason = ans if ans and ans.lower() not in ("n", "no") else "Action denied by operator."
                return ApprovalDecision.REJECTED, arguments, reason

        # Default fallback: Deny by default for safety
        return ApprovalDecision.REJECTED, arguments, "Denied: No approval handler configured and action requires human sign-off."


class StructuredAuditLogger:
    """
    Maintains a deterministic, structured audit log of all agent lifecycle steps
    (Thoughts, Actions, Approvals, Tool Observations, Timeouts, Terminations).
    Outputs to both an in-memory trail and a JSONL file.
    """

    def __init__(self, log_path: Optional[Path] = None):
        self.log_path = log_path or (Path(__file__).resolve().parent / "audit_trail.jsonl")
        self.events: List[Dict[str, Any]] = []

    def log_event(
        self,
        event_type: str,
        session_id: str,
        turn_index: int,
        payload: Dict[str, Any],
        latency_ms: Optional[float] = None,
    ):
        record = {
            "event_id": str(uuid.uuid4())[:8],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "turn_index": turn_index,
            "event_type": event_type,
            "latency_ms": round(latency_ms, 2) if latency_ms is not None else None,
            "payload": payload,
        }
        self.events.append(record)

        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, default=str) + "\n")
        except Exception as e:
            logger.error(f"Failed to write structured log: {e}")

    def clear(self):
        self.events.clear()
        if self.log_path.exists():
            try:
                self.log_path.unlink()
            except Exception:
                pass
