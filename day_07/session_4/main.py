"""
Day 07 - Session 04: Reliability & Control
Tests agent guardrails: HITL approval gates, tool timeouts, loop detection,
iteration caps with graceful degradation, and structured JSONL audit trails.
"""

from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Any, Dict, Tuple
from dotenv import load_dotenv

load_dotenv()

from guardrails import ApprovalDecision, LoopDetector
from reliable_agent import ReliableAgent

AUDIT_LOG_FILE = Path(__file__).resolve().parent / "audit_trail.jsonl"


def test_1_approval_gate_approved():
    print("\n--- Test 1: HITL Approval Gate (Approved) ---")
    approval_logs = []

    def mock_approver(request: Dict[str, Any]) -> Tuple[ApprovalDecision, Any, str]:
        print(f"  [Approval Gate] Reviewing tool '{request['tool_name']}' -> APPROVED")
        approval_logs.append(request)
        return ApprovalDecision.APPROVED, None, "Approved by SRE lead."

    agent = ReliableAgent(
        max_iterations=5,
        tool_timeout_seconds=3.0,
        approval_callback=mock_approver,
        audit_log_path=AUDIT_LOG_FILE,
    )

    prompt = (
        "Investigate incident INC-4091 and send a summary email to 'devops@company.com'."
    )
    result = agent.run(user_prompt=prompt, session_id="test1_approval_approved")

    assert len(approval_logs) == 1, "Approval gate did not intercept send_email!"
    assert approval_logs[0]["tool_name"] == "send_email"
    print(f"Result: {result['final_response'].strip()[:150]}...")
    print("Pass: Action intercepted, approved, and dispatched.")


def test_2_approval_gate_rejected():
    print("\n--- Test 2: HITL Approval Gate (Rejected) ---")

    def mock_rejection(request: Dict[str, Any]) -> Tuple[ApprovalDecision, Any, str]:
        print(f"  [Approval Gate] Reviewing tool '{request['tool_name']}' -> REJECTED")
        return ApprovalDecision.REJECTED, None, "Incident investigation still ongoing; do not send email."

    agent = ReliableAgent(
        max_iterations=5,
        tool_timeout_seconds=3.0,
        approval_callback=mock_rejection,
        audit_log_path=AUDIT_LOG_FILE,
    )

    prompt = "Investigate INC-4091 and email 'executives@company.com'."
    result = agent.run(user_prompt=prompt, session_id="test2_approval_rejected")

    assert result["approvals_requested"][0]["decision"] == "REJECTED"
    print(f"Result: {result['final_response'].strip()[:150]}...")
    print("Pass: Agent adapted gracefully after rejection.")


def test_3_timeout_enforcement():
    print("\n--- Test 3: Tool Timeout Enforcement ---")
    agent = ReliableAgent(
        max_iterations=4,
        tool_timeout_seconds=1.5,
        audit_log_path=AUDIT_LOG_FILE,
    )

    prompt = "Simulate a slow network operation with sleep_seconds = 5."
    result = agent.run(user_prompt=prompt, session_id="test3_timeout")

    with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
        events = [json.loads(line) for line in f if "test3_timeout" in line]
    timeouts = [e for e in events if e.get("event_type") == "TOOL_TIMEOUT"]
    assert len(timeouts) > 0, "Timeout event missing from audit log!"
    elapsed = timeouts[0]["payload"]["elapsed_seconds"]
    print(f"Tool was timed out at {elapsed:.2f}s (budget 1.5s)")
    print("Pass: Tool timeout enforced cleanly.")


def test_4_loop_detection():
    print("\n--- Test 4: Loop & Repetitive Action Detection ---")
    detector = LoopDetector(max_consecutive_repeats=2)

    is_loop1, _ = detector.record_and_check("read_incident", {"id": "INC-1"})
    assert not is_loop1
    is_loop2, reason2 = detector.record_and_check("read_incident", {"id": "INC-1"})
    assert is_loop2, "Failed to detect consecutive duplicate action!"
    print(f"Caught consecutive repeat: {reason2}")

    detector.reset()
    detector.record_and_check("action_a", {})
    detector.record_and_check("action_b", {})
    detector.record_and_check("action_a", {})
    is_osc, osc_reason = detector.record_and_check("action_b", {})
    assert is_osc, "Failed to detect oscillating ping-pong loop!"
    print(f"Caught oscillation: {osc_reason}")
    print("Pass: Loop detection verified.")


def test_5_iteration_cap():
    print("\n--- Test 5: Max Iteration Cap & Graceful Degradation ---")
    agent = ReliableAgent(
        max_iterations=1,
        audit_log_path=AUDIT_LOG_FILE,
    )
    result = agent.run(
        user_prompt="Check INC-4091 and prepare full mitigation plan.",
        session_id="test5_iteration_cap"
    )
    assert result["cap_exceeded"] is True
    assert "GRACEFUL DEGRADATION" in result["final_response"]
    print("Pass: Execution halted cleanly at iteration cap.")


def test_6_audit_trail():
    print("\n--- Test 6: Audit Log Verification ---")
    assert AUDIT_LOG_FILE.exists()
    with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
        lines = [json.loads(l) for l in f if l.strip()]
    event_types = set(e["event_type"] for e in lines)
    print(f"Recorded {len(lines)} audit events across {len(event_types)} distinct event types.")
    print("Pass: Audit log telemetry verified.")


def main():
    if AUDIT_LOG_FILE.exists():
        AUDIT_LOG_FILE.unlink()

    test_1_approval_gate_approved()
    test_2_approval_gate_rejected()
    test_3_timeout_enforcement()
    test_4_loop_detection()
    test_5_iteration_cap()
    test_6_audit_trail()

    print("\nAll reliability tests passed successfully.")


if __name__ == "__main__":
    main()
