"""
Day 08 - Session 04: Observability & Tracing
Demonstrates capturing OpenTelemetry-style trace spans (LLM and tool calls),
diagnosing root-cause errors from traces, replaying failed runs with fixes,
and alerting on elevated failure rates.
"""

from __future__ import annotations
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from tracer import Tracer, render_trace_tree
from observed_agent import ObservedAgent
from debugger_and_replay import TraceDebugger, ReplayEngine
from metrics_and_alerts import FailureRateAlerter

LOG_FILE = Path(__file__).resolve().parent / "traces.jsonl"


def test_successful_run(tracer: Tracer) -> str:
    print("\n--- 1. Tracing Successful Agent Execution ---")
    agent = ObservedAgent(tracer=tracer, fail_fast_on_tool_error=False)
    prompt = "Query revenue reports for all regions in Q3-2026."
    res = agent.run(user_prompt=prompt, trace_id="trace_success_001")

    spans = tracer.get_trace("trace_success_001")
    print(f"Trace Tree (trace_success_001):\n{render_trace_tree(spans)}")

    llm_spans = [s for s in spans if s["span_type"] == "llm"]
    tool_spans = [s for s in spans if s["span_type"] == "tool"]
    assert len(llm_spans) >= 1 and len(tool_spans) >= 1
    print("Pass: Captured LLM calls, tool spans, and token counts.")
    return "trace_success_001"


def test_failed_run(tracer: Tracer) -> str:
    print("\n--- 2. Capturing Real Tool Failure in Trace ---")
    agent = ObservedAgent(tracer=tracer, fail_fast_on_tool_error=True)
    failing_prompt = "Select column 'revenue_cents' from table 'revenue_reports'."

    failed_trace_id = "trace_failed_002"
    try:
        agent.run(user_prompt=failing_prompt, trace_id=failed_trace_id)
    except Exception as exc:
        print(f"Agent failed as expected: {exc}")

    spans = tracer.get_trace(failed_trace_id)
    print(f"Trace Tree of Failed Run:\n{render_trace_tree(spans)}")

    failed_spans = [s for s in spans if s["status"] == "ERROR"]
    assert len(failed_spans) > 0
    print("Pass: Failure captured in trace tree.")
    return failed_trace_id


def test_diagnose_and_replay(tracer: Tracer, failed_trace_id: str):
    print("\n--- 3. Diagnosing and Replaying with Fix ---")
    debugger = TraceDebugger(tracer=tracer)
    diagnosis = debugger.diagnose_trace(failed_trace_id)
    print(f"Diagnosis: {diagnosis['failing_span_name']} failed with '{diagnosis['error_message']}'")

    replay_engine = ReplayEngine(tracer=tracer)
    fix = "The revenue column is 'gross_revenue_usd'. Do not query 'revenue_cents'."
    replay_res = replay_engine.replay_and_repair(
        failed_trace_id=failed_trace_id,
        corrective_instructions=fix,
        new_trace_id="trace_replayed_003"
    )
    assert replay_res["status"] == "SUCCESS"
    print("Pass: Replayed run succeeded with fix applied.")


def test_metrics_and_alerts(tracer: Tracer):
    print("\n--- 4. Metric Aggregation & Failure Rate Alerting ---")
    alerter = FailureRateAlerter(tracer=tracer, threshold_pct=15.0)
    metrics = alerter.compute_metrics()
    print(f"Total traces: {metrics['total_traces']}, Failure rate: {metrics['failure_rate_pct']:.1f}%")
    print("Pass: Telemetry and failure metrics computed.")


def main():
    if LOG_FILE.exists():
        LOG_FILE.unlink()

    tracer = Tracer(log_file_path=LOG_FILE)
    test_successful_run(tracer)
    failed_id = test_failed_run(tracer)
    test_diagnose_and_replay(tracer, failed_id)
    test_metrics_and_alerts(tracer)

    print("\nObservability and tracing verification complete.")


if __name__ == "__main__":
    main()
