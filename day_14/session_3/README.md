# Day 14 - Session 3: Production Monitoring & Observability

## Overview

Deploying an agentic AI system into production is only half the battle. Unlike traditional microservices that fail with clear HTTP `500 Internal Server Error` status codes, agentic LLM systems frequently suffer from **Silent Quality Decay**:
- The agent continues returning HTTP `200 OK`, but its answers become ungrounded or hallucinated due to an outdated vector retrieval index.
- System prompt updates unintentionally cause **token inflation**, increasing inference cost by 40–80% for identical queries.
- A downstream dependency slows down, silently pushing **p95 latency** past acceptable human SLA thresholds.

This module implements a production-grade **Agentic Observability & Telemetry Hub** adhering to **OpenTelemetry**, **Langfuse**, and **LangSmith** industry standards:
1. **Multi-Span Tracing**: Capturing every agent run with full span hierarchy (`TRACE`, `LLM_CALL`, `TOOL_EXECUTION`, `RETRIEVAL`, `GUARDRAIL`).
2. **Cost & Latency Dashboards**: Real-time tracking of token volume, model pricing ($/1M tokens), and percentile distributions ($p50$, $p90$, $p95$, $p99$).
3. **Failure-Rate & SLA Alerts**: Automated alerting on pass-rate violations ($> 5\%$ errors), p95 latency spikes ($> 1,500\text{ms}$), and groundedness degradation.
4. **Hallucination & Groundedness Auditing**: Measuring token/entity overlap and claim support against retrieved documents.
5. **User Feedback Loops**: Capturing explicit ratings, thumbs up/down, and implicit signals (retries, copy-pastes, human escalations).
6. **Silent Quality Decay Detector**: Sliding-window statistical drift detector comparing historical baselines against active traffic to catch degradation before acute outages occur.
7. **Glassmorphic Dark Mode Web Dashboard**: Interactive real-time analytics UI with canvas charts, active alerts banner, and an interactive trace explorer table with slide-out span inspection drawers.

---

## Architecture & Telemetry Pipeline

```
              User Production Request (Incident Remediation / Chat)
                                      │
                                      ▼
                      ┌─────────────────────────────┐
                      │    ProductionTracer (SDK)   │
                      │  - Context Lifecycle        │
                      │  - Parent-Child Spans       │
                      │  - Token Usage & Cost       │
                      └──────────────┬──────────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        ▼                             ▼                             ▼
┌──────────────────┐        ┌──────────────────┐         ┌──────────────────┐
│ LLM Inference    │        │ Tool Execution   │         │ Groundedness     │
│ - Prompt Tokens  │        │ - Ingress Query  │         │ - Claim Support  │
│ - Compl. Tokens  │        │ - K8s Node Drain │         │ - Hallucination  │
│ - Pricing Engine │        │ - DB Trace Query │         │   Detection      │
└────────┬─────────┘        └────────┬─────────┘         └────────┬─────────┘
         │                           │                            │
         └───────────────────────────┼────────────────────────────┘
                                     │
                                     ▼
                      ┌─────────────────────────────┐
                      │    MetricsAggregator        │
                      │  - Daily / Hourly Buckets   │
                      │  - p50, p90, p95, p99 Lat.  │
                      │  - Failure Distribution     │
                      └──────────────┬──────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         ▼                           ▼                           ▼
┌──────────────────┐       ┌──────────────────┐        ┌──────────────────┐
│ AlertingEngine   │       │ Silent Decay     │        │ FastAPI Backend  │
│ - Failure SLA    │       │ Detector         │        │ & Web Dashboard  │
│ - P95 Violation  │       │ - Z-Score Drift  │        │ - Canvas Charts  │
│ - Groundedness   │       │ - Multi-Signal   │        │ - Trace Explorer │
└──────────────────┘       └──────────────────┘        └──────────────────┘
```

---

## Core Components

| Component | File | Description |
| :--- | :--- | :--- |
| **Data Models** | [`models.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_14/session_3/models.py) | OpenTelemetry / Langfuse style schemas for traces, spans, feedback, metrics, and alerts. |
| **Pricing Engine** | [`pricing_engine.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_14/session_3/pricing_engine.py) | Model pricing table ($/1M tokens) for Claude 3.5 Sonnet, Claude 3 Haiku, GPT-4o, and GPT-4o-mini. |
| **Production Tracer** | [`tracer.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_14/session_3/tracer.py) | Full trace/span lifecycle manager, groundedness evaluation, and user feedback attachment. |
| **Metrics Aggregator** | [`metrics_aggregator.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_14/session_3/metrics_aggregator.py) | Time-series bucketing, percentile calculations ($p50, p90, p95, p99$), failure categories, and Silent Quality Decay detector. |
| **Alerting Engine** | [`alerting_engine.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_14/session_3/alerting_engine.py) | Evaluates operational SLOs (failure rate $> 5\%$, p95 $> 1500\text{ms}$, groundedness $< 0.85$, decay alarms). |
| **Trace Simulator** | [`trace_simulator.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_14/session_3/trace_simulator.py) | Generates 14 days of realistic production telemetry traces demonstrating health, decay, incident spike, and recovery. |
| **FastAPI Backend** | [`app.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_14/session_3/app.py) | Production REST API serving metrics, alerts, time-series, traces, and the web UI. |
| **Web Dashboard UI** | [`static/index.html`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_14/session_3/static/index.html), [`style.css`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_14/session_3/static/style.css), [`dashboard.js`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_14/session_3/static/dashboard.js) | Dark glassmorphic dashboard with live KPI cards, interactive Canvas charts, active alerts, and a trace explorer drawer. |
| **Master CLI** | [`main.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_14/session_3/main.py) | Command-line tool to run simulations, view ASCII terminal dashboards, run decay audits, or start the web server. |
| **Test Suite** | [`test_session_3.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_14/session_3/test_session_3.py) | Comprehensive test suite covering span hierarchy, pricing, percentiles, groundedness, decay detection, and alerts. |

---

## Verification & Execution Guide

### 1. Run Automated Unit Test Suite
Executes all 7 test cases covering the entire telemetry pipeline:
```powershell
.venv\Scripts\python.exe day_14\session_3\test_session_3.py
```

### 2. View Terminal Monitoring Dashboard & Silent Decay Audit
Renders the complete 14-day production telemetry breakdown directly in the terminal:
```powershell
.venv\Scripts\python.exe day_14\session_3\main.py --dashboard-terminal
```

### 3. Launch the Live Web Dashboard
Starts the FastAPI application and serves the modern glassmorphic dashboard:
```powershell
.venv\Scripts\python.exe day_14\session_3\main.py --serve --port 8000
```
Open **`http://127.0.0.1:8000/`** in your browser to view:
- **KPI Metrics Ribbon**: Live overall pass rate, p95 latency, total cost, groundedness score, CSAT %, and silent decay badge.
- **Active Alerts Drawer**: Real-time alerts with severity badges and acknowledge actions.
- **Interactive Canvas Charts**:
  - Pass Rate & SLA Trend Chart with 95% SLA Target Line
  - Latency Percentiles ($p50$, $p90$, $p95$) multi-line chart
  - Daily Token Cost & Volume bar chart
  - Failure Categories breakdown (Timeout, Tool Failure, Hallucination, Rate Limit)
- **Live Trace Explorer Table**: Search, filter by failure category, and click **Inspect** to examine complete multi-span execution trees.

---

## Mathematical Formulations

### 1. Latency Percentiles ($p50, p90, p95, p99$)
For an ordered set of latency observations $L = [l_1, l_2, \dots, l_n]$ sorted in ascending order:
$$k = (n - 1) \times \frac{P}{100}$$
$$f = \lfloor k \rfloor, \quad c = \min(f + 1, n - 1), \quad d = k - f$$
$$\text{Percentile}(P) = l_f + d \times (l_c - l_f)$$

### 2. Groundedness Score & Hallucination Threshold
Given a retrieved context token set $C$ and generated response claim token set $R$:
$$\text{Overlap} = \frac{|R \cap C|}{|R|}$$
If $\text{Overlap} < 0.65$, the trace is flagged with $\text{hallucination\_detected} = \text{True}$ and assigned `FailureCategory.HALLUCINATION`.

### 3. Silent Quality Decay Multi-Signal Detector
Detects subtle unprompted degradation across four signals:
1. **Groundedness Drop**: $\Delta_{\text{grounded}} < -8.0\%$
2. **Pass Rate Drop**: $\Delta_{\text{pass}} < -3.5\%$
3. **Token Cost Inflation**: $\Delta_{\text{cost}} > +25.0\%$
4. **P95 Latency Creep**: $\Delta_{p95} > +30.0\%$

$$\text{Decay Signals} = \sum \mathbf{1}(\text{Signal Triggered})$$
$$\text{Decay Score} = \min(1.0, \text{Decay Signals} \times 0.35)$$
If $\text{Decay Signals} \ge 2$, `is_decaying = True` and a `CRITICAL` alert is dispatched.
