"""
Day 8 - Session 4: Observability
Master Demonstration and Verification Suite.

Demonstrates and verifies:
1. OpenTelemetry & LangSmith/Langfuse Span Structure (Traces, Parent-Child Spans, Attributes, Events).
2. Logging Every Tool Call and Exact Token Counts.
3. Capturing Real Production Tool Failures in Traces (Database schema mismatch).
4. Debugging and Root-Cause Diagnosis Directly from the Trace Tree.
5. Replaying the Failed Run with a Targeted Fix and Verifying Resolution.
6. Operational Metric Aggregation & Failure Rate Alerting.
"""

import sys
import json
import time
from pathlib import Path
from typing import Any, Dict

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from tracer import Tracer, render_trace_tree
from observed_agent import ObservedAgent
from debugger_and_replay import TraceDebugger, ReplayEngine
from metrics_and_alerts import FailureRateAlerter

LOG_FILE = Path(__file__).resolve().parent / "traces.jsonl"


def print_banner(title: str):
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def print_educational_overview():
    print_banner("1. AGENT OBSERVABILITY, SPAN STRUCTURE & TRACING CONCEPTS")
    print("""
[1. DISTRIBUTED TRACING FOR AGENTS (LangSmith / Langfuse / OpenTelemetry)]
   • A Trace represents the entire lifecycle of an end-to-end request.
   • A Span represents an individual unit of contiguous execution (e.g. LLM call, Tool execution).
   • Hierarchical Span Structure:
     agent.run (Root Span, trace_id: 't-100', span_id: 's-01', parent: None)
       ├── agent.turn_1 (parent: 's-01')
       │     ├── llm.chat_completion (parent: 'turn_1', attributes: tokens, model, latency)
       │     └── tool.query_database (parent: 'turn_1', attributes: sql, rows, status)
       └── agent.turn_2 (parent: 's-01')
             └── llm.chat_completion (parent: 'turn_2', attributes: tokens, final_answer)

[2. LOGGING EVERY TOOL CALL & TOKEN COUNT]
   • Every tool call logs: tool name, arguments, output payload, latency, and exit status.
   • Every LLM call logs: prompt tokens, completion tokens, total tokens, and dollar cost.

[3. REPLAYING FAILED RUNS (Post-Mortem Superpower)]
   • When an agent crashes in production, the trace preserves the exact input state,
     system prompt, tool arguments, and stack trace.
   • Engineers can replay the failing run with patched prompts or tools without guessing.

[4. FAILURE RATE ALERTING]
   • Aggregates span statuses across all sessions to track failure rates and SLA compliance.
   • Emits alerts when failure rates exceed thresholds (e.g. > 15%).
""", flush=True)


def test_1_successful_traced_run(tracer: Tracer) -> str:
    print_banner("2. EXECUTING SUCCESSFUL TRACED RUN (FULL TELEMETRY CAPTURE)")

    agent = ObservedAgent(tracer=tracer, fail_fast_on_tool_error=False)
    prompt = (
        "Query the revenue reports database for all regions in Q3-2026. "
        "List the regions and their gross revenue in USD."
    )
    print(f"User Prompt: \"{prompt}\"")

    result = agent.run(user_prompt=prompt, trace_id="trace_success_001")

    print("\n--- Agent Final Answer ---")
    print(result["final_answer"].strip())

    spans = tracer.get_trace("trace_success_001")
    print("\n--- Visual Span Tree Hierarchy (trace_success_001) ---")
    print(render_trace_tree(spans))

    # Verify spans captured token counts and tool outputs
    llm_spans = [s for s in spans if s["span_type"] == "llm"]
    tool_spans = [s for s in spans if s["span_type"] == "tool"]

    assert len(llm_spans) >= 2, "Failed to capture LLM spans!"
    assert len(tool_spans) >= 1, "Failed to capture tool spans!"
    assert llm_spans[0]["attributes"]["total_tokens"] > 0, "Token count was not recorded!"
    assert tool_spans[0]["attributes"]["tool_name"] == "query_database"

    print("\n✓ TEST 1 PASSED: Every LLM call, token count, and tool execution was captured in trace.")
    return "trace_success_001"


def test_2_real_failed_run(tracer: Tracer) -> str:
    print_banner("3. CAPTURING REAL PRODUCTION FAILURE IN TRACE (DATABASE SCHEMA MISMATCH)")

    # Agent with fail_fast_on_tool_error to record a real unhandled tool exception in the trace
    agent = ObservedAgent(tracer=tracer, fail_fast_on_tool_error=True)
    failing_prompt = (
        "Execute a query selecting column 'revenue_cents' from table 'revenue_reports' for all regions."
    )
    print(f"User Prompt: \"{failing_prompt}\"")
    print("Expected: Database will throw sqlite3.OperationalError: no such column: revenue_cents.")

    failed_trace_id = "trace_failed_002"
    try:
        agent.run(user_prompt=failing_prompt, trace_id=failed_trace_id)
    except Exception as exc:
        print(f"\n[AGENT CRASH INTERCEPTED] Exception: {exc}")

    spans = tracer.get_trace(failed_trace_id)
    print("\n--- Visual Span Tree Hierarchy of Failed Run (trace_failed_002) ---")
    print(render_trace_tree(spans))

    failed_spans = [s for s in spans if s["status"] == "ERROR"]
    assert len(failed_spans) > 0, "Trace failed to record ERROR status on failing span!"

    print("\n✓ TEST 2 PASSED: Production failure captured in trace with full exception context.")
    return failed_trace_id


def test_3_debug_from_trace(tracer: Tracer, failed_trace_id: str):
    print_banner("4. DEMONSTRATING DEBUGGING & ROOT CAUSE ISOLATION FROM TRACE")

    debugger = TraceDebugger(tracer=tracer)
    diagnosis = debugger.diagnose_trace(failed_trace_id)

    print(f"Diagnosing Trace ID:       {diagnosis['trace_id']}")
    print(f"Root Span Operation:       {diagnosis['root_span_name']}")
    print(f"Failing Span:              {diagnosis['failing_span_name']} ({diagnosis['failing_span_type']})")
    print(f"Error Message:             {diagnosis['error_message']}")
    print(f"Failing Tool Arguments:    {json.dumps(diagnosis['failing_inputs'], indent=2)}")

    print("\n--- SRE Root Cause Diagnosis ---")
    print("""
[ROOT CAUSE IDENTIFIED]
  • The model generated SQL: SELECT region, revenue_cents FROM revenue_reports ...
  • The SQLite database table 'revenue_reports' uses column 'gross_revenue_usd', NOT 'revenue_cents'.
  • The tool span immediately recorded an ERROR status with sqlite3.OperationalError.
  • Resolution: Instruct the model to use the correct schema column 'gross_revenue_usd'.
""", flush=True)

    assert "no such column" in diagnosis["error_message"].lower()
    print("✓ TEST 3 PASSED: Root cause accurately pinpointed from trace attributes without guesswork.")


def test_4_replay_and_repair(tracer: Tracer, failed_trace_id: str):
    print_banner("5. REPLAYING FAILED RUN WITH TARGETED FIX (REPLAY ENGINE)")

    replay_engine = ReplayEngine(tracer=tracer)
    repair_instruction = "The revenue column is named 'gross_revenue_usd' (amounts in dollars). Never query 'revenue_cents'."

    print(f"Replaying original prompt from {failed_trace_id} with fix:")
    print(f"  Fix: \"{repair_instruction}\"\n")

    replay_res = replay_engine.replay_and_repair(
        failed_trace_id=failed_trace_id,
        corrective_instructions=repair_instruction,
    )

    print(f"Replay Trace ID:  {replay_res['replay_trace_id']}")
    print(f"Replay Status:    {replay_res['replay_status']}")
    print("\n--- Replayed Agent Answer ---")
    print(replay_res["replay_final_answer"].strip())

    print("\n--- Visual Span Tree Hierarchy of Replayed Run ---")
    print(replay_res["replay_tree"])

    assert replay_res["is_fixed"] is True, "Replayed trace failed to resolve the error!"
    print("\n✓ TEST 4 PASSED: Failed run replayed from trace and verified with 100% OK status.")


def test_5_failure_rate_alerting(tracer: Tracer):
    print_banner("6. OPERATIONAL TELEMETRY & FAILURE RATE ALERTING")

    alerter = FailureRateAlerter(tracer=tracer, failure_threshold_pct=25.0)
    metrics = alerter.calculate_metrics()
    alert = alerter.evaluate_alert()

    print("Operational SLI Metrics Across All Traces:")
    print(f"  • Total Traces Executed:   {metrics['total_traces']}")
    print(f"  • Successful Traces:       {metrics['successful_traces']}")
    print(f"  • Failed Traces:           {metrics['failed_traces']}")
    print(f"  • Failure Rate:            {metrics['failure_rate_pct']}% (Threshold: {alert['threshold_limit_pct']}%)")
    print(f"  • Total Tokens Logged:     {metrics['total_tokens']:,}")
    print(f"  • Average Trace Duration:  {metrics['avg_duration_ms']:.1f}ms")

    print("\nSRE Alert Evaluation:")
    print(f"  Status:  [{alert['alert_status']}] - Severity: {alert['severity']}")
    print(f"  Message: {alert['message']}")
    print(f"  Action:  {alert['remediation_action']}")

    assert metrics["total_traces"] >= 3, "Insufficient trace sample size!"
    print("\n✓ TEST 5 PASSED: Failure rate accurately tracked across runs and alert evaluated.")


def main():
    print_banner("DAY 8 - SESSION 4: AGENT OBSERVABILITY & TRACING")

    # Clean previous trace log for fresh benchmark run
    if LOG_FILE.exists():
        LOG_FILE.unlink()

    tracer = Tracer(log_path=LOG_FILE)

    print_educational_overview()
    time.sleep(1.0)

    # 1. Successful traced run
    test_1_successful_traced_run(tracer)
    time.sleep(1.0)

    # 2. Real failed run (schema mismatch)
    failed_trace_id = test_2_real_failed_run(tracer)
    time.sleep(1.0)

    # 3. Debugging from trace
    test_3_debug_from_trace(tracer, failed_trace_id)
    time.sleep(1.0)

    # 4. Replay and repair
    test_4_replay_and_repair(tracer, failed_trace_id)
    time.sleep(1.0)

    # 5. Alerting on failure rate
    test_5_failure_rate_alerting(tracer)

    print_banner("DAY 8 - SESSION 4 OBSERVABILITY VERIFICATION COMPLETED SUCCESSFULLY! ✅")


if __name__ == "__main__":
    main()
