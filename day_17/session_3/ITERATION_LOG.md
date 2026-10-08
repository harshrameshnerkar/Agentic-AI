# Iteration Log: Scientific Step-by-Step Architecture Evolution

**Sprint:** Sprint 1 — Diagnostic Engine & Tool Resilience  
**Session:** Day 17 — Session 3: First Real Iteration  
**Author:** Harsh Ramesh Nerkar (Intern)  
**Mentor & Reviewer:** Dr. Elena Rostova (Principal AI Systems Architect)  
**Date:** October 8, 2026  
**Evaluation Set:** `eval_dataset.json` (20 Golden Enterprise SRE Cases)  
**Artifact ID:** `ITER-LOG-DAY17-S3-001`

---

## 1. The Core Scientific Discipline

> *"Never build an agent by throwing prompts, memory, tools, and routers into a blender all at once.*  
> *Apply strict hypothesis-driven engineering:*  
> *1. Add ONLY what the evaluation error log proves is missing.*  
> *2. Make ONE change at a time.*  
> *3. Score every change against the exact same golden evaluation set.*  
> *4. Log the measured delta and document the exact causal reason it worked or failed."*  
> — Dr. Elena Rostova

---

## 2. Iteration Timeline & Measured Deltas

```
+----------------------------------------------------------------------------------------------------------------+
|                                    ITERATIVE PROGRESSION SCORECARD                                             |
+----------------------------------------------------------------------------------------------------------------+
| Step | Architecture Added                   | Pass Rate | Static % | Ephemeral % | Latency   | Cost / Query    |
+------+--------------------------------------+-----------+----------+-------------+-----------+-----------------+
| S0   | Baseline: Vanilla RAG (Single Call)  |   30.0%   |  100.0%  |     0.0%    |  280.2 ms |  $0.000115      |
| S1   | +Enhanced Retrieval (Hybrid RRF)     |   30.0%   |  100.0%  |     0.0%    |  310.1 ms |  $0.000130      |
| S2   | +Cluster Telemetry Diagnostic Tool   |  100.0%   |  100.0%  |   100.0%    |  883.7 ms |  $0.000351      |
| S3   | +Conditional Intent Router           |  100.0%   |  100.0%  |   100.0%    |  762.8 ms |  $0.000329      |
+----------------------------------------------------------------------------------------------------------------+
```

---

## 3. Detailed Step Logs & Causal Analysis

### Step 0: The Baseline Starting Point (Vanilla RAG)
- **Architecture:** Single-step lexical retrieval against static runbooks, appended to standard zero-shot prompt.
- **Hypothesis:** Can a single retrieval call solve enterprise incident triage?
- **Result:** **30.0% Pass Rate** (6/20 pass).
  - Static Runbooks: 100.0% (6/6 pass).
  - Dynamic Incidents: 0.0% (0/14 pass).
  - Latency: 280.2 ms | Cost: $0.000115.
- **Error Analysis:** Static runbooks contain policy knowledge (Vault root tokens, S3 lifecycle, escalation timers), but contain **zero** information about real-time production failures (e.g. Exit Code 137 OOMKilled in `auth-service`, poison pill in Kafka partition 4).

---

### Step 1: Change #1 — Enhanced Retrieval (Hybrid BM25 + Dense RRF)
- **Hypothesis:** Perhaps the 14 failures occurred because single-step keyword matching failed to retrieve the right runbooks. Upgrading to Hybrid Reciprocal Rank Fusion (lexical + service-conditioned dense matching) will improve retrieval recall.
- **Implementation:** Added `HybridRunbookRetriever` with Reciprocal Rank Fusion (RRF top-2).
- **Result:** **30.0% Pass Rate** (6/20 pass — **NO DELTA IN OVERALL PASS RATE**).
  - Static Runbooks: 100.0% (6/6 pass, higher rank confidence).
  - Dynamic Incidents: 0.0% (0/14 pass).
  - Latency: 310.1 ms (+29.9 ms) | Cost: $0.000130.
- **Why It Failed to Improve Overall Score:**
  > *"You cannot retrieve what was never written down."*  
  The failure on live incidents was not a retrieval ranking defect. No matter how sophisticated your vector search or RRF reranking is, static documentation does not contain ephemeral container exit codes or live Prometheus metrics. **More retrieval cannot solve a missing data problem.**

---

### Step 2: Change #2 — Single Diagnostic Tool (Live Ephemeral Pod & Metric Inspector)
- **Hypothesis:** If we provide a single targeted tool that queries the Kubernetes API and Prometheus (`query_live_telemetry`) to extract live pod exit codes, memory graphs, commit SHAs, and fatal log snippets, the model can synthesize accurate root causes for live outages.
- **Implementation:** Integrated `EphemeralClusterInspector` providing direct cluster facts to the diagnostic context.
- **Result:** **100.0% Pass Rate** (20/20 pass — **+70.0% ABSOLUTE IMPROVEMENT**).
  - Static Runbooks: 100.0% (6/6 pass).
  - Dynamic Incidents: 100.0% (14/14 pass).
  - Latency: 883.7 ms (+573.6 ms) | Cost: $0.000351 (+0.000221).
- **Why It Worked:**
  - `auth-service` CrashLoopBackOff: Tool instantly surfaced `exit_code: 137` and `OutOfMemoryError` in commit `7f8b9a2d`.
  - `payment-gateway` 504: Tool surfaced `db_connections_active: 30/30` HikariCP pool exhaustion.
  - `user-profile` 502: Tool surfaced readiness probe failure due to missing `REDIS_PORT` in ConfigMap.
  - Real-world telemetry facts transformed ambiguous alerts into deterministic root causes.
- **Trade-off Incurred:** Average latency rose from 310 ms to 884 ms because every query invoked the cluster inspector.

---

### Step 3: Change #3 — Conditional Intent Routing
- **Hypothesis:** Querying Kubernetes and Prometheus for static runbook queries (e.g. *"What is the PagerDuty escalation SLA?"*) is wasteful. It adds 600ms of unnecessary latency, increases cluster API load, and expands blast radius. A fast sub-5ms Intent Classifier can route queries:
  - `STATIC_POLICY` -> Direct fast-path Hybrid RAG (sub-250ms).
  - `EPHEMERAL_INCIDENT` -> Deep-path Cluster Telemetry Inspector.
- **Implementation:** Built `IntentRouter` using pattern matching and keyword semantics to classify incoming queries.
- **Result:** **100.0% Pass Rate Maintained** (20/20 pass).
  - Mean Latency: **762.8 ms** (**-120.9 ms speedup / 13.7% latency reduction**).
  - Mean Cost: **$0.000329** (cost reduction per query).
  - Zero cluster API calls made for static policy queries.
- **Why It Worked:**
  Routing achieved the "Pareto Frontier": maximum accuracy (100%) with minimum necessary resource expenditure. Documentation lookups returned in 220 ms, while active cluster outages received deep diagnostic investigation.

---

## 4. Final Comparison vs. Project Targets

| Success Metric Target (Day 16 Charter) | Day 16 Baseline | Day 17 Step 0 (Vanilla RAG) | Day 17 Step 3 (Final Iteration) | Target Status |
|:---|:---:|:---:|:---:|:---:|
| **Root Cause Accuracy** | 82.4% | 30.0% | **100.0%** ($\ge 95\%$ target) | **EXCEEDED (PASS)** |
| **p95 Latency SLA** | 85.5 min | 280 ms | **762.8 ms** ($\le 90\text{s}$ target) | **EXCEEDED (PASS)** |
| **Cost per Query Ceiling** | $107.50 | $0.000115 | **$0.000329** ($\le \$0.15$ ceiling) | **EXCEEDED (PASS)** |
| **Cluster API Load** | Uncontrolled | 0 calls | **0 calls on static queries** | **OPTIMIZED** |

---

## 5. Next Steps for Session 4
Present the 5-line executive progress update to Dr. Elena Rostova summarizing what shipped, pass rate, cost, risks, and required decision.
