# Sprint 1 Backlog: Foundation & Riskiest Task Tracker

**Sprint Name:** Sprint 1 — Diagnostic Telemetry & Tool Resilience  
**Sprint Window:** Day 17 to Day 18  
**Sprint Goal:** De-risk and build the resilient, parallel diagnostic tool foundation before constructing high-level agent reasoning loops.  
**Scrum Master / Mentor:** Dr. Elena Rostova  
**Lead Engineer:** Harsh Ramesh Nerkar  

---

## 📋 Sprint 1 Kanban Board State

```
+--------------------------+------------------------------+---------------------------+
|          TO DO           |         IN PROGRESS          |           DONE            |
+--------------------------+------------------------------+---------------------------+
| [TASK-1.2] Metrics Tool  | [TASK-1.1] De-Risk Dynamic   | [DAY-16] Stakeholder      |
| [TASK-1.3] Kube Inspector|   Tool Integration & Log     |   Discovery & Feasibility |
| [TASK-1.4] Git Tracker   |   Anomaly Extraction         |   Spike                   |
| [TASK-1.5] Benchmarking  |   (Riskiest Task)            |                           |
+--------------------------+------------------------------+---------------------------+
```

---

## 🎯 Deep Dive: TASK-1.1 (The Riskiest Task)

### Why is this the riskiest task?
In Day 16 Session 3, we discovered that **static knowledge retrieval alone cannot solve live incidents** because it cannot query live, ephemeral cluster states (dying pods, connection locks, noisy logs).
However, querying live cloud APIs introduces catastrophic runtime risks:
1. **Network Latency & Timeouts:** If a log aggregator API takes 15 seconds to reply, our sub-60s triage SLA is broken.
2. **Context Blowup:** 50,000 raw log lines equal ~400,000 tokens, which breaks our $\$0.15$ cost ceiling and crashes LLM context windows.
3. **Cascading Failure:** If one tool throws an unhandled `ConnectionResetError`, the entire triage pipeline crashes.

### Task Specifications
- **Identifier:** `TASK-1.1`
- **Owner:** Harsh Ramesh Nerkar
- **Status:** **`IN PROGRESS`**
- **Priority:** P0 (Highest)
- **Target Completion:** Day 17 Session 1

### Acceptance Criteria & Verification Matrix
1. **Async Concurrency:** Executes `get_pod_status`, `query_metrics`, `get_git_diff`, and `fetch_logs` in parallel via `asyncio.gather`. Total wall-clock time $\le 2.5\text{ seconds}$.
2. **Circuit-Breaker Timeouts:** Every tool is wrapped in an `asyncio.wait_for(..., timeout=2.0s)` guard. If a tool times out, it yields a structured fallback error without killing sibling tools.
3. **High-Noise Log Compaction:** Simulates 50,000 raw log lines (99.8% info/debug noise), extracts the fatal stack traces, deduplicates occurrences, and produces a $< 350\text{-token}$ high-signal diagnostic snippet.
4. **Resilient Data Bundle:** Produces a standardized, JSON-serializable `DiagnosticBundle` containing CPU/memory metrics, pod exit codes, git commit info, and log anomalies.
