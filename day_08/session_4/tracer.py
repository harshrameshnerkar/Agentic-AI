"""
OpenTelemetry & LangSmith/Langfuse Compliant Tracing Engine.
Provides:
- Hierarchical Span structure (Trace -> Parent Span -> Child Spans).
- Full attribute capture (Inputs, Outputs, Tool Calls, Token counts, Latencies, Status).
- Error capture with stack trace extraction.
- JSONL persistence and trace querying.
- Visual span tree renderer for post-mortem debugging.
"""

import json
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional


class Span:
    """Represents an OpenTelemetry / Langfuse compliant execution span."""

    def __init__(
        self,
        name: str,
        trace_id: str,
        span_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        span_type: str = "chain",  # "chain", "llm", "tool", "agent"
        attributes: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.trace_id = trace_id
        self.span_id = span_id or str(uuid.uuid4())[:8]
        self.parent_span_id = parent_span_id
        self.span_type = span_type
        self.start_time = datetime.now(timezone.utc).isoformat()
        self.start_time_monotonic = time.monotonic()
        self.end_time: Optional[str] = None
        self.duration_ms: float = 0.0
        self.status: str = "RUNNING"  # "OK", "ERROR", "RUNNING"
        self.error_message: Optional[str] = None
        self.error_stack: Optional[str] = None
        self.attributes: Dict[str, Any] = attributes or {}
        self.events: List[Dict[str, Any]] = []

    def set_attribute(self, key: str, value: Any):
        self.attributes[key] = value

    def add_event(self, name: str, payload: Optional[Dict[str, Any]] = None):
        self.events.append({
            "name": name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload or {}
        })

    def end(self, status: str = "OK", error: Optional[Exception] = None):
        self.end_time = datetime.now(timezone.utc).isoformat()
        self.duration_ms = round((time.monotonic() - self.start_time_monotonic) * 1000, 2)
        self.status = status
        if error:
            self.status = "ERROR"
            self.error_message = str(error)
            import traceback
            self.error_stack = traceback.format_exc()
            self.set_attribute("error", str(error))
            self.set_attribute("error_type", type(error).__name__)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "span_type": self.span_type,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "error_message": self.error_message,
            "error_stack": self.error_stack,
            "attributes": self.attributes,
            "events": self.events,
        }


class Tracer:
    """Manages active spans, persistence to JSONL, and trace querying."""

    def __init__(self, log_path: Optional[Path] = None):
        self.log_path = log_path or (Path(__file__).resolve().parent / "traces.jsonl")
        self.active_spans: Dict[str, Span] = {}
        self.completed_spans: List[Span] = []

    @contextmanager
    def span(
        self,
        name: str,
        trace_id: str,
        parent_span_id: Optional[str] = None,
        span_type: str = "chain",
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Generator[Span, None, None]:
        span_obj = Span(
            name=name,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            span_type=span_type,
            attributes=attributes,
        )
        self.active_spans[span_obj.span_id] = span_obj
        try:
            yield span_obj
            if span_obj.status == "RUNNING":
                span_obj.end("OK")
        except Exception as e:
            span_obj.end("ERROR", error=e)
            raise e
        finally:
            self.active_spans.pop(span_obj.span_id, None)
            self.completed_spans.append(span_obj)
            self._persist_span(span_obj)

    def _persist_span(self, span: Span):
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(span.to_dict(), default=str) + "\n")
        except Exception as e:
            print(f"[Tracer Error] Failed to persist span: {e}")

    def load_traces(self) -> Dict[str, List[Dict[str, Any]]]:
        """Loads all traces grouped by trace_id."""
        traces: Dict[str, List[Dict[str, Any]]] = {}
        if not self.log_path.exists():
            return traces
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    span_data = json.loads(line)
                    t_id = span_data["trace_id"]
                    if t_id not in traces:
                        traces[t_id] = []
                    traces[t_id].append(span_data)
                except Exception:
                    pass
        return traces

    def get_trace(self, trace_id: str) -> List[Dict[str, Any]]:
        traces = self.load_traces()
        return traces.get(trace_id, [])

    def get_failed_traces(self) -> List[Dict[str, Any]]:
        """Returns metadata for all traces containing at least one ERROR span."""
        traces = self.load_traces()
        failed = []
        for t_id, spans in traces.items():
            err_spans = [s for s in spans if s["status"] == "ERROR"]
            if err_spans:
                root_span = next((s for s in spans if s["parent_span_id"] is None), spans[0])
                failed.append({
                    "trace_id": t_id,
                    "root_name": root_span["name"],
                    "total_spans": len(spans),
                    "failed_spans_count": len(err_spans),
                    "first_error_span": err_spans[0]["name"],
                    "error_message": err_spans[0]["error_message"],
                    "timestamp": root_span["start_time"],
                })
        return failed


def render_trace_tree(spans: List[Dict[str, Any]]) -> str:
    """Renders a hierarchical ASCII tree of spans for visual debugging."""
    if not spans:
        return "No spans found."

    # Build parent -> children mapping
    by_id = {s["span_id"]: s for s in spans}
    children: Dict[Optional[str], List[Dict[str, Any]]] = {}
    for s in spans:
        p_id = s.get("parent_span_id")
        if p_id not in children:
            children[p_id] = []
        children[p_id].append(s)

    lines: List[str] = []

    def _render(node_id: Optional[str], prefix: str = ""):
        for idx, child in enumerate(children.get(node_id, [])):
            is_last = idx == len(children[node_id]) - 1
            branch = "└── " if is_last else "├── "
            status_icon = "❌" if child["status"] == "ERROR" else "✅"
            dur_str = f"{child['duration_ms']:.1f}ms"
            
            # Format attributes snippet
            attrs = child.get("attributes", {})
            tokens_str = f" | {attrs['total_tokens']} tokens" if "total_tokens" in attrs else ""
            type_tag = f"[{child['span_type'].upper()}]"
            
            line = f"{prefix}{branch}{status_icon} {type_tag} {child['name']} ({dur_str}{tokens_str})"
            if child["status"] == "ERROR" and child.get("error_message"):
                line += f" -> ERROR: {child['error_message']}"
            lines.append(line)

            next_prefix = prefix + ("    " if is_last else "│   ")
            _render(child["span_id"], next_prefix)

    # Roots have parent_span_id == None
    _render(None)
    return "\n".join(lines)
