# Day 17 - Session 1: Standup & Riskiest Task First

## 📌 Syllabus & Session Objectives
- **Session:** Day 17 - Session 1: Standup & Riskiest Task First
- **Topic:** Build Sprint 1 — Foundation & Risk De-Risking
- **What to Learn:** 15-minute standup: done, next, blocked. Then attack the riskiest assumption — usually retrieval quality or a tool integration, not the agent logic.
- **Task:** Standup notes; the riskiest task moved to In Progress.
- **Resources:** Intern (Harsh Ramesh Nerkar) + Mentor (Dr. Elena Rostova, Principal AI Systems Architect).

---

## ⏱️ The 15-Minute Daily Standup

```
================================================================================
             SPRINT 1 DAILY STANDUP (15-MIN TIMEBOXED SUMMARY)
================================================================================
```

### 1. What Was Done (Day 16 Recap):
- **Stakeholder Discovery (Session 1):** Scoped the authentic on-call SRE triage problem with VP Marcus Vance; documented the 7-stage baseline workflow (avg 85.5 min MTTR, 17.6% error rate under fatigue).
- **Constraints & Success Metrics (Session 2):** Formalized the 6 signed-off target metrics ($\ge 95\%$ accuracy, p95 $\le 90\text{s}$, cost $\le \$0.15$), established the 3-Tier blast radius matrix, the 5 "Never Automate" Red Lines, and the cryptographic HMAC-SHA256 HITL approval gateway.
- **Data & Feasibility Spike (Session 3):** Audited enterprise document stores; proved that Hybrid RRF retrieval achieves 100% Hit@3 on runbooks, but identified the fundamental ~7-10% static ceiling due to ephemeral live cluster state.

### 2. What Is Next (Sprint 1 Focus):
- Attack the **single riskiest technical assumption** first before writing any high-level agent logic.
- Build and benchmark the **Async Diagnostic Tool Dispatcher** (`query_metrics`, `fetch_logs`, `get_pod_status`, `get_git_diff`).
- Validate noise rejection on high-throughput log streams (50,000 lines/min down to high-signal anomaly snippets in $< 2\text{s}$).
- Implement circuit-breaker resilience and timeout fallbacks so no single failing tool can hang the triage loop.

### 3. Blockers & Risks Identified:
- **Potential Blocker:** Live log streams from Splunk/Coralogix contain extreme noise (96% info/debug telemetry). Sending raw logs to an LLM will blow up context windows, exceed our $\$0.15$ cost ceiling, and inflate latency past 60s.
- **Resolution:** Build an in-process **Log Anomaly Compaction Engine** that extracts fatal stack traces and error bursts before context assembly.

---

## 🎯 Attacking the Riskiest Assumption First

> *"Junior engineers always start by writing prompt templates and agent loops. That is a rookie mistake.*
> *Prompt templates and ReAct loops are trivial. The hardest, highest-risk failure mode in production autonomous systems is **Tool Integration & Telemetry Extraction under Chaos**:*
> *1. Can your tools concurrently query Kubernetes, metrics, and logs in under 3 seconds without blocking?*
> *2. What happens when the logging API drops packets or times out? Does your agent crash, or do you have circuit breakers?*
> *3. Can you extract the signal from 50,000 log lines without hallucinating or running out of context?*
> *Attack that tool integration risk TODAY. Move it to In Progress and de-risk it immediately."*
>
> — **Dr. Elena Rostova, Principal AI Systems Architect (Mentor)**

---

## 📋 Sprint 1 Kanban Tracker: Moving to IN PROGRESS

```text
+--------------------------+------------------------------+---------------------------+
|          TO DO           |         IN PROGRESS          |           DONE            |
+--------------------------+------------------------------+---------------------------+
| [TASK-1.2] Metrics Tool  | [TASK-1.1] De-Risk Dynamic   | [DAY-16] Stakeholder      |
| [TASK-1.3] Kube Inspector|   Tool Integration & Log     |   Discovery & Feasibility |
| [TASK-1.4] Git Tracker   |   Anomaly Extraction         |   Spike                   |
| [TASK-1.5] Benchmarking  |   (Riskiest Task)            |                           |
+--------------------------+------------------------------+---------------------------+
```

| Task ID | Task Description | Priority | Risk Level | Status |
|:---:|---|:---:|:---:|:---:|
| **TASK-1.1** | **De-Risk Tool Integration & Log Anomaly Compactor** (Riskiest Task) | **P0 (Critical)** | **HIGH** | **`[IN PROGRESS]`** |
| **TASK-1.2** | Async Prometheus & Datadog Metrics Collector | P1 (High) | Medium | `[TO DO]` |
| **TASK-1.3** | Kubernetes Ephemeral Pod State & Exit Code Inspector | P1 (High) | Medium | `[TO DO]` |
| **TASK-1.4** | ArgoCD & GitHub Commit Diff Correlator | P2 (Medium) | Low | `[TO DO]` |
| **TASK-1.5** | End-to-End Concurrent Dispatch Benchmark Suite | P1 (High) | Medium | `[TO DO]` |

---

## ⚡ Empirical Validation of the Riskiest Task

Running the asynchronous tool dispatcher across live/mocked Kubernetes, Prometheus, Git, and 50,000 log lines:

- **Parallel Concurrency:** All 4 tools dispatch simultaneously via `asyncio.gather`. Total wall-clock time is **~965 ms** (well within our 2,500ms budget).
- **Log Noise Compaction:** 50,000 raw lines processed; 99.8% noise filtered; top 5 fatal stack traces isolated in **< 1.5s**.
- **Circuit-Breaker Resilience:** When a tool simulates a network hang, an isolated `CIRCUIT_BREAKER_TIMEOUT` triggers in 2.0s without interrupting sibling tools.

---

## 📂 Deliverables & File Directory

- [STANDUP_NOTES.md](STANDUP_NOTES.md): Official 15-minute standup notes (Done, Next, Blocked) and identification of the riskiest assumption.
- [SPRINT_BACKLOG.md](SPRINT_BACKLOG.md): Sprint 1 backlog and Kanban tracker moving TASK-1.1 to `IN PROGRESS`.
- [riskiest_task_derisker.py](riskiest_task_derisker.py): Python engine implementing concurrent tool dispatch, 50k log compaction, and circuit breakers.
- [main.py](main.py): Interactive CLI reviewing standup notes, Kanban board, and executing the tool de-risking suite with optional fault injection.
- [test_riskiest_task.py](test_riskiest_task.py): Unit and integration test suite validating latency, log extraction accuracy, circuit breakers, and artifacts.
- [requirements.txt](requirements.txt): Environment dependencies.

---

## 🚀 Execution & Verification

### 1. View Standup Notes & Kanban Board
```bash
python day_17/session_1/main.py
```

### 2. Execute Async Tool Dispatch (50k Log Compaction)
```bash
python day_17/session_1/main.py --attack-risk
```

### 3. Test Circuit Breaker Timeout Under Simulated Network Hang
```bash
python day_17/session_1/main.py --simulate-fault pod
```

### 4. Run Test Suite
```bash
python day_17/session_1/test_riskiest_task.py
```
*Expected: 4 tests passing in ~2.8 seconds with 100% assertions satisfied.*
