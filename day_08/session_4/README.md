# Day 8 — Session 4: Observability

Observability is the foundation of production-grade agent engineering. Autonomous agents are non-deterministic, multi-step, and stateful—making traditional monolithic application logging insufficient. This session instruments an agent with **OpenTelemetry / LangSmith / Langfuse compliant distributed tracing**, captures a real production tool failure in the trace graph, and demonstrates debugging and replaying the failed run with zero guesswork.

---

## 1. Span Hierarchy & Anatomy

A **Trace** represents the complete lifecycle of a single user request. A **Span** represents a contiguous unit of work. Spans form a directed acyclic tree with explicit parent-child relationships:

```
agent.run (Root Span, trace_id: "trace_001", span_id: "s_root", parent: None)
  │
  ├── agent.turn_1 (span_id: "s_turn_1", parent: "s_root")
  │     ├── llm.chat_completion (span_id: "s_llm_1", parent: "s_turn_1")
  │     │     Attributes: model="gemini-3.1-flash-lite", tokens=1,420, cost=$0.00018
  │     │
  │     └── tool.query_database (span_id: "s_tool_1", parent: "s_turn_1")
  │           Attributes: query_sql="SELECT ...", rows=4, duration=2.1ms
  │
  └── agent.turn_2 (span_id: "s_turn_2", parent: "s_root")
        └── llm.chat_completion (span_id: "s_llm_2", parent: "s_turn_2")
              Attributes: model="gemini-3.1-flash-lite", tokens=890, finish="stop"
```

### Essential Span Attributes Captured:
1. **Identifiers**: `trace_id`, `span_id`, `parent_span_id`.
2. **Metadata**: `name`, `span_type` (`agent`, `chain`, `llm`, `tool`).
3. **Execution Timing**: `start_time`, `end_time`, `duration_ms`.
4. **Token Telemetry**: `prompt_tokens`, `completion_tokens`, `total_tokens`, `cost_usd`.
5. **Tool Telemetry**: `tool_name`, input `arguments`, output payload / `error`.
6. **Error Context**: `status` (`OK` / `ERROR`), `error_message`, `error_stack`.

---

## 2. Debugging Real Failures from Traces

When an agent encounters an unhandled exception or hallucinated SQL column in production:

```
└── ❌ [AGENT] agent.run (1842.1ms) -> ERROR: no such column: revenue_cents
    └── ❌ [CHAIN] agent.turn_1 (1840.4ms) -> ERROR: no such column: revenue_cents
        ├── ✅ [LLM] llm.chat_completion (1820.2ms | 1450 tokens)
        └── ❌ [TOOL] tool.query_database (15.2ms) -> ERROR: no such column: revenue_cents
```

### The Post-Mortem Diagnosis:
- **Root Cause**: The model generated `SELECT region, revenue_cents FROM revenue_reports`.
- **Database Schema**: The actual column is named `gross_revenue_usd`.
- **Actionable Fix**: Inject the exact column specification into the system prompt or tool description.

---

## 3. Replaying Failed Runs

The trace preserves the exact input state, user prompt, and tool parameters. The [`ReplayEngine`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_08/session_4/debugger_and_replay.py#L55-L103):
1. Loads the original failed trace (`trace_failed_002`).
2. Applies the corrective schema guidance (`gross_revenue_usd`).
3. Executes a replayed trace linked to the original incident (`replay_trace_failed`).
4. Verifies all spans transition to `✅ OK` with zero errors.

---

## 4. Failure Rate Alerting

The [`FailureRateAlerter`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_08/session_4/metrics_and_alerts.py#L11-L76) scans all completed traces from `traces.jsonl` and computes key Service Level Indicators (SLIs):
$$\text{Failure Rate} = \frac{\text{Failed Traces}}{\text{Total Traces}} \times 100\%$$
- If $\text{Failure Rate} \ge 20\%$ (SLA Threshold): Triggers a `CRITICAL` alert with recommended remediation actions.
- Automatically transitions back to `NORMAL` once fixes are deployed.

---

## 5. File Index

- [`tracer.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_08/session_4/tracer.py): OpenTelemetry / LangSmith / Langfuse compliant Tracer with Span hierarchy and visual tree renderer.
- [`tools.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_08/session_4/tools.py): Live SQLite database tools with real query execution and error capture.
- [`observed_agent.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_08/session_4/observed_agent.py): ReAct agent instrumented with full hierarchical span tracing and token accounting.
- [`debugger_and_replay.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_08/session_4/debugger_and_replay.py): TraceDebugger for isolating failed spans and ReplayEngine for verifying fixes.
- [`metrics_and_alerts.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_08/session_4/metrics_and_alerts.py): Operational SLI metrics and failure rate alerting engine.
- [`main.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_08/session_4/main.py): Master test runner asserting all 5 verification phases.

---

## 6. Execution

Run the master verification suite:

```bash
.venv\Scripts\python.exe day_08\session_4\main.py
```
