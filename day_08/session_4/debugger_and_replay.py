"""
Trace Debugger and Replay Engine for Day 8 Session 4.
Demonstrates:
- Inspecting a failed execution trace to locate the exact failing span.
- Root cause diagnosis from span attributes and stack traces.
- Replaying the failed run with a corrective fix and validating success.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path
from tracer import Tracer, render_trace_tree
from observed_agent import ObservedAgent


class TraceDebugger:
    """Diagnoses failures by walking hierarchical span traces."""

    def __init__(self, tracer: Optional[Tracer] = None):
        self.tracer = tracer or Tracer()

    def diagnose_trace(self, trace_id: str) -> Dict[str, Any]:
        """Loads trace spans, builds tree, and pinpoints root-cause failure."""
        spans = self.tracer.get_trace(trace_id)
        if not spans:
            return {"error": f"Trace '{trace_id}' not found."}

        tree_view = render_trace_tree(spans)
        failed_spans = [s for s in spans if s["status"] == "ERROR"]

        if not failed_spans:
            return {
                "trace_id": trace_id,
                "status": "ALL_SPANS_OK",
                "tree_view": tree_view,
                "failed_spans_count": 0,
            }

        # The earliest error in the tree is typically the root cause
        root_error_span = failed_spans[0]
        root_span = next((s for s in spans if s["parent_span_id"] is None), spans[0])

        diagnosis = {
            "trace_id": trace_id,
            "status": "FAILURE_DETECTED",
            "root_span_name": root_span["name"],
            "user_prompt": root_span.get("attributes", {}).get("user_prompt"),
            "failing_span_name": root_error_span["name"],
            "failing_span_type": root_error_span["span_type"],
            "error_message": root_error_span.get("error_message"),
            "failing_inputs": root_error_span.get("attributes", {}).get("arguments") or root_error_span.get("attributes", {}).get("input"),
            "duration_before_failure_ms": root_error_span["duration_ms"],
            "tree_view": tree_view,
        }

        return diagnosis


class ReplayEngine:
    """
    Replays a failed run by loading its initial trace context,
    applying a repair strategy, and verifying that the replayed execution succeeds.
    """

    def __init__(self, tracer: Optional[Tracer] = None):
        self.tracer = tracer or Tracer()

    def replay_and_repair(
        self,
        failed_trace_id: str,
        corrective_instructions: str,
    ) -> Dict[str, Any]:
        """
        Replays the original failed user request with corrective prompt guidance,
        recording a brand new trace linked to the original failure.
        """
        spans = self.tracer.get_trace(failed_trace_id)
        if not spans:
            raise ValueError(f"Trace {failed_trace_id} not found.")

        root_span = next((s for s in spans if s["parent_span_id"] is None), spans[0])
        original_prompt = root_span.get("attributes", {}).get("user_prompt", "")

        replay_trace_id = f"replay_{failed_trace_id[:8]}"
        repaired_agent = ObservedAgent(tracer=self.tracer, fail_fast_on_tool_error=False)

        # Inject corrective system guidance derived from trace post-mortem
        repaired_system_prompt = (
            "You are a Financial Operations Agent. "
            "IMPORTANT RECOVERY INSTRUCTION: In the 'revenue_reports' table, "
            f"{corrective_instructions}"
        )

        replay_result = repaired_agent.run(
            user_prompt=original_prompt,
            trace_id=replay_trace_id,
            system_prompt=repaired_system_prompt,
        )

        replay_spans = self.tracer.get_trace(replay_trace_id)
        replay_tree = render_trace_tree(replay_spans)

        return {
            "failed_trace_id": failed_trace_id,
            "replay_trace_id": replay_trace_id,
            "original_prompt": original_prompt,
            "replay_status": replay_result["status"],
            "replay_final_answer": replay_result["final_answer"],
            "replay_tree": replay_tree,
            "is_fixed": replay_result["status"] == "OK" and not any(s["status"] == "ERROR" for s in replay_spans),
        }
