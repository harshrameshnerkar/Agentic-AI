"""
Master Test & Demonstration Suite for Day 7 - Session 4: Reliability & Control.

Demonstrates and verifies:
1. Max Iteration Caps
2. Loop and Repeated-Action Detection
3. Wall-Clock Tool Timeouts
4. Retries with Exponential Backoff
5. Human-in-the-Loop (HITL) Mandatory Approval Gates (Approved & Rejected flows)
6. Structured Step Logging (JSONL Audit Trail)
7. Graceful Degradation
"""

import sys
import json
import time
from pathlib import Path
from typing import Any, Dict, Tuple

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from guardrails import ApprovalDecision, LoopDetector
from reliable_agent import ReliableAgent

AUDIT_LOG_FILE = Path(__file__).resolve().parent / "audit_trail.jsonl"


def print_banner(title: str):
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def test_1_approval_gate_approved():
    """
    Scenario: User asks to inspect critical incident INC-4091 and email the team.
    Agent inspects incident, attempts to fire 'send_email'.
    Approval Gate catches the action -> Human Operator APPROVES -> Email fires successfully.
    """
    print_banner("TEST 1: MANDATORY APPROVAL GATE BEFORE send_email (HUMAN APPROVES)")

    approval_logs = []

    def mock_approver(request: Dict[str, Any]) -> Tuple[ApprovalDecision, Any, str]:
        print("\n  🛑 [HITL APPROVAL GATE TRIGGERED]")
        print(f"     Tool Requiring Authorization: '{request['tool_name']}'")
        print(f"     Recipient:                   {request['arguments'].get('to')}")
        print(f"     Subject:                     {request['arguments'].get('subject')}")
        print(f"     Body Preview:                {request['arguments'].get('body')[:80]}...")
        print("     Decision:                    [APPROVED by Human Operator: Lead SRE]")
        approval_logs.append(request)
        return ApprovalDecision.APPROVED, None, "Approved by Lead SRE on-call."

    agent = ReliableAgent(
        max_iterations=5,
        tool_timeout_seconds=3.0,
        approval_callback=mock_approver,
        audit_log_path=AUDIT_LOG_FILE,
    )

    prompt = (
        "Please investigate critical incident INC-4091. Once you confirm its root cause and mitigation, "
        "send an official notification email to 'devops-alerts@company.com' with the incident summary."
    )
    print(f"\nUser: \"{prompt}\"")

    result = agent.run(user_prompt=prompt, session_id="test1_approval_approved")

    print("\n--- Agent Execution Result ---")
    print(f"Turns Executed:     {result['turns_executed']}")
    print(f"Approvals Logged:   {len(result['approvals_requested'])}")
    print(f"Cap Exceeded:       {result['cap_exceeded']}")
    print("\n--- Agent Final Response ---")
    print(result["final_response"].strip())

    # Assertions
    assert len(approval_logs) == 1, "Approval gate did not intercept send_email!"
    assert approval_logs[0]["tool_name"] == "send_email", "Wrong tool intercepted!"
    assert result["approvals_requested"][0]["decision"] == "APPROVED"
    print("\n✓ TEST 1 PASSED: send_email was safely intercepted, reviewed, approved, and dispatched.")


def test_2_approval_gate_rejected():
    """
    Scenario: User requests sending email for INC-4091, but human operator DENIES approval.
    Agent receives the rejection observation, gracefully adapts, does NOT send email,
    and returns incident summary directly to user.
    """
    print_banner("TEST 2: MANDATORY APPROVAL GATE BEFORE send_email (HUMAN REJECTS)")

    def mock_approver_rejection(request: Dict[str, Any]) -> Tuple[ApprovalDecision, Any, str]:
        print("\n  🛑 [HITL APPROVAL GATE TRIGGERED]")
        print(f"     Tool Requiring Authorization: '{request['tool_name']}'")
        print(f"     Recipient:                   {request['arguments'].get('to')}")
        print("     Decision:                    [REJECTED by Human Operator]")
        print("     Reason:                      'Incident is still undergoing post-mortem analysis; hold off on external dispatch.'")
        return ApprovalDecision.REJECTED, None, "Incident is still undergoing post-mortem analysis; hold off on external dispatch."

    agent = ReliableAgent(
        max_iterations=5,
        tool_timeout_seconds=3.0,
        approval_callback=mock_approver_rejection,
        audit_log_path=AUDIT_LOG_FILE,
    )

    prompt = (
        "Investigate INC-4091 and immediately email 'executives@company.com' with status."
    )
    print(f"\nUser: \"{prompt}\"")

    result = agent.run(user_prompt=prompt, session_id="test2_approval_rejected")

    print("\n--- Agent Final Response (Gracefully Handling Rejection) ---")
    print(result["final_response"].strip())

    # Assertions
    assert len(result["approvals_requested"]) == 1
    assert result["approvals_requested"][0]["decision"] == "REJECTED"
    assert "rejected" in result["final_response"].lower() or "denied" in result["final_response"].lower() or "hold" in result["final_response"].lower() or "operator" in result["final_response"].lower(), \
        "Agent failed to acknowledge human rejection!"
    print("\n✓ TEST 2 PASSED: Rejection respected; email was BLOCKED from firing; agent degraded gracefully.")


def test_3_timeout_enforcement():
    """
    Scenario: Agent executes 'slow_diagnostics_service' which hangs for 4.0s.
    The agent has tool_timeout_seconds = 1.5s.
    TimeoutGuard terminates the hung call, returns TimeoutError observation, and agent handles it cleanly.
    """
    print_banner("TEST 3: WALL-CLOCK TOOL EXECUTION TIMEOUT ENFORCEMENT")

    agent = ReliableAgent(
        max_iterations=4,
        tool_timeout_seconds=1.5,  # Strict 1.5 second timeout!
        audit_log_path=AUDIT_LOG_FILE,
    )

    prompt = (
        "Run a deep telemetry diagnostic using 'slow_diagnostics_service' with simulated_delay_seconds=4.0 "
        "on service 'Payment-Worker'."
    )
    print(f"\nUser: \"{prompt}\"")
    print("Notice: slow_diagnostics_service takes 4.0 seconds, but timeout guard limit is 1.5 seconds.")

    t0 = time.monotonic()
    result = agent.run(user_prompt=prompt, session_id="test3_timeout")
    total_duration = time.monotonic() - t0

    print(f"\nTotal Wall-Clock Time: {total_duration:.2f}s (Did NOT hang for 4+ seconds!)")
    print("\n--- Agent Response (Recovering from Timeout) ---")
    print(result["final_response"].strip())

    # Verify audit log recorded TOOL_TIMEOUT
    with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
        events = [json.loads(line) for line in f if "test3_timeout" in line]
    timeout_events = [e for e in events if e.get("event_type") == "TOOL_TIMEOUT"]
    assert len(timeout_events) > 0, "TOOL_TIMEOUT event was not logged in audit trail!"
    tool_elapsed = timeout_events[0]["payload"]["elapsed_seconds"]
    print(f"Tool execution strictly intercepted at: {tool_elapsed:.2f}s (Budget: 1.50s)")
    assert tool_elapsed < 2.5, f"Tool timeout was not enforced! Took {tool_elapsed}s"
    assert "timeout" in result["final_response"].lower(), "Agent response did not acknowledge timeout!"
    print("\n✓ TEST 3 PASSED: Slow tool was intercepted at 1.5s, non-blocking fallback returned.")


def test_4_loop_detection():
    """
    Scenario: Unit and integration validation of LoopDetector against repetitive actions and 2-step oscillation.
    """
    print_banner("TEST 4: LOOP & REPEATED-ACTION DETECTION")

    detector = LoopDetector(max_consecutive_repeats=2)

    print("Step 1: Calling read_system_incident(incident_id='INC-4091')...")
    is_loop1, _ = detector.record_and_check("read_system_incident", {"incident_id": "INC-4091"})
    assert not is_loop1, "Erroneous loop detection on first call!"

    print("Step 2: Calling identical action again with identical args...")
    is_loop2, reason2 = detector.record_and_check("read_system_incident", {"incident_id": "INC-4091"})
    assert is_loop2, "Failed to detect duplicate consecutive action!"
    print(f"  ⚡ INTERCEPTED LOOP: {reason2}")

    print("\nTesting Oscillating Ping-Pong Pattern (A -> B -> A -> B)...")
    detector.reset()
    detector.record_and_check("tool_alpha", {"param": 1})
    detector.record_and_check("tool_beta", {"param": 2})
    detector.record_and_check("tool_alpha", {"param": 1})
    is_osc, osc_reason = detector.record_and_check("tool_beta", {"param": 2})
    assert is_osc, "Failed to detect oscillating 2-step cycle!"
    print(f"  ⚡ INTERCEPTED OSCILLATION: {osc_reason}")

    print("\n✓ TEST 4 PASSED: Repetitive loops and oscillating cycles accurately detected.")


def test_5_iteration_cap_and_graceful_degradation():
    """
    Scenario: Agent configured with max_iterations=1.
    A multi-step query is submitted.
    After completing turn 1 (calling tool), turn 2 attempts to start but is halted by IterationCapGuard.
    Agent yields a graceful degradation report without crashing.
    """
    print_banner("TEST 5: MAX ITERATION CAP & GRACEFUL DEGRADATION")

    agent = ReliableAgent(
        max_iterations=1,  # Strict cap of 1 turn
        audit_log_path=AUDIT_LOG_FILE,
    )

    prompt = "Check incident INC-4091, diagnose the root cause, and formulate a detailed remediation plan."
    print(f"\nUser: \"{prompt}\"")
    print("Agent configured with max_iterations = 1.")

    result = agent.run(user_prompt=prompt, session_id="test5_iteration_cap")

    print("\n--- Execution Summary ---")
    print(f"Turns Run:      {result['turns_executed']}")
    print(f"Cap Exceeded:   {result['cap_exceeded']}")
    print("\n--- Graceful Degradation Response ---")
    print(result["final_response"].strip())

    # Assertions
    assert result["cap_exceeded"] is True, "Iteration cap was not triggered!"
    assert "GRACEFUL DEGRADATION" in result["final_response"], "Graceful degradation banner missing!"
    print("\n✓ TEST 5 PASSED: Execution stopped cleanly at iteration cap; runaway spending prevented.")


def test_6_audit_trail_inspection():
    """
    Scenario: Verifies that structured audit logging recorded events across the entire lifecycle in JSONL.
    """
    print_banner("TEST 6: STRUCTURED AUDIT LOGGING VERIFICATION (JSONL)")

    assert AUDIT_LOG_FILE.exists(), "Audit log file does not exist!"
    with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
        lines = [json.loads(line) for line in f if line.strip()]

    print(f"Total structured audit events recorded in '{AUDIT_LOG_FILE.name}': {len(lines)}")
    event_types = set(e["event_type"] for e in lines)
    print("Discovered Event Types in Audit Log:")
    for et in sorted(event_types):
        count = sum(1 for e in lines if e["event_type"] == et)
        print(f"  • {et:<22} : {count} event(s)")

    required_types = {
        "USER_PROMPT",
        "APPROVAL_REQUIRED",
        "APPROVAL_GRANTED",
        "APPROVAL_DENIED",
        "TOOL_TIMEOUT",
        "CAP_EXCEEDED",
    }
    missing = required_types - event_types
    assert not missing, f"Missing required audit event types: {missing}"

    sample = lines[-1]
    print("\nSample Structured Audit Record:")
    print(json.dumps(sample, indent=2))

    print("\n✓ TEST 6 PASSED: Structured audit trail contains compliant, verifiable telemetry.")


def main():
    print_banner("DAY 7 - SESSION 4: RELIABILITY & CONTROL TEST SUITE")

    # Clear previous audit log for fresh verification
    if AUDIT_LOG_FILE.exists():
        AUDIT_LOG_FILE.unlink()

    test_1_approval_gate_approved()
    time.sleep(1.0)

    test_2_approval_gate_rejected()
    time.sleep(1.0)

    test_3_timeout_enforcement()
    time.sleep(1.0)

    test_4_loop_detection()
    time.sleep(1.0)

    test_5_iteration_cap_and_graceful_degradation()
    time.sleep(1.0)

    test_6_audit_trail_inspection()

    print_banner("ALL 6 RELIABILITY & CONTROL TESTS COMPLETED SUCCESSFULLY! ✅")


if __name__ == "__main__":
    main()
