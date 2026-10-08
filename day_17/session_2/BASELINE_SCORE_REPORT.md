# Baseline Score Report: The Simplest Thing That Works

**Session:** Day 17 — Build Sprint 1 | Session 2: Simplest Thing That Works  
**Author:** Harsh Ramesh Nerkar (Intern)  
**Evaluator:** Dr. Elena Rostova (Principal AI Systems Architect / Mentor)  
**Date:** October 8, 2026  
**Artifact ID:** `BSR-DAY17-S2-001`  
**Evaluation Dataset:** `eval_dataset.json` (20 Golden Enterprise Incidents)

---

## 1. Executive Summary & Core Engineering Principle

> *"Always build the simplest thing that could possibly work first. Score it ruthlessly against a golden evaluation set.*  
> *Do not build an autonomous multi-step agent loop until your evaluation set proves beyond doubt that a single prompt or single retrieval call is fundamentally insufficient."*  
> — Dr. Elena Rostova

In Session 2, we resisted the premature urge to build an agent. We implemented and benchmarked the two simplest non-agent architectures against our 20-case golden evaluation dataset:
1. **Baseline 1 — Plain Prompt (Zero-Shot Completion):** Direct LLM inference with no external data or tools.
2. **Baseline 2 — Single Retrieval Call (Vanilla RAG):** Single-step vector/lexical retrieval from enterprise runbooks appended to context.

Both baselines were evaluated across exact root cause accuracy, indicator recall, latency, cost per query, and generic hallucination rates.

---

## 2. Empirical Benchmark Scorecard

| Architecture | Overall Pass Rate | Static Runbook Pass Rate (6 Cases) | Dynamic Incident Pass Rate (14 Cases) | Key Indicator Recall | Generic Guess Rate | Mean Latency (ms) | Cost / Query ($) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Human SRE Baseline (Day 16)** | **82.4%** | **94.0%** | **78.0%** | **88.2%** | **17.6%** | **5,130,000 ms** (85.5m) | **$107.50** (human labor) |
| **Baseline 1: Plain Prompt (Zero-Shot)** | **0.0%** | **0.0%** | **0.0%** | **3.8%** | **100.0%** | **120.0 ms** | **$0.000045** |
| **Baseline 2: Single Retrieval Call (Vanilla RAG)** | **30.0%** | **100.0%** | **0.0%** | **30.0%** | **50.0%** | **280.2 ms** | **$0.000115** |

---

## 3. Deep-Dive Error Analysis

### Why Baseline 1 (Plain Prompt) Failed Completely (0.0% Pass Rate)
- **Zero Factual Precision for Enterprise Policy:** When asked about Vault root token rotation (`INC-102`) or PagerDuty escalation timeouts (`INC-108`), the plain prompt produced vague generalities (*"Use the Vault CLI"*, *"Escalate to your team lead"*). It missed exact compliance requirements like SEC-DR-401, 3-key quorum, and 5/10/15-minute SLA ladders.
- **Hallucinated Recommendations on Outages:** On CrashLoopBackOff incidents (`INC-101`), the plain prompt repeatedly recommended *"Restart the pod"*. In reality, the pod had an Exit Code 137 (OOMKilled) caused by an unbounded session cache introduced in commit `7f8b9a2d`. Restarting the pod immediately crashed again.

### Why Baseline 2 (Vanilla RAG) Reached a Hard 30% Ceiling
- **Perfect on Static Knowledge (100% on 6/6 cases):** When a runbook existed for the exact query (e.g., Vault token rotation, Twilio SMS circuit breaker, S3 lifecycle, emergency break-glass bastion access), Vanilla RAG retrieved the document and answered with 100% factual fidelity.
- **Complete Collapse on Dynamic Incidents (0% on 14/14 cases):**
  - **The Ephemeral Gap:** Static markdown runbooks cannot tell you why `auth-service` is crashing right now at 09:30 UTC. The answer does not exist in documentation.
  - The answer exists exclusively in **ephemeral cluster state**:
    - Kubernetes pod exit codes (`exit_code: 137`)
    - Prometheus live memory curves (`utilization: 99.8%`)
    - Git commit diffs (`commit: 7f8b9a2d - Add unbounded session cache`)
    - Real-time container logs (`FATAL java.lang.OutOfMemoryError`)
  - Because Vanilla RAG has zero access to cluster telemetry tools, it hallucinates or emits generic *"No matching runbook found"* fallbacks on 100% of live outages.

---

## 4. The Decision: Proving That an Agentic / Tool-Equipped Chain is Required

Before this session, building an agent was a hypothesis. Now, it is an **empirically proven necessity**:

```
+--------------------------------------------------------------------------+
|                        EMPIRICAL PROOF CASCADE                          |
+--------------------------------------------------------------------------+
| 1. Can a plain prompt solve the problem?                                |
|    --> NO (0% accuracy). Zero-shot LLMs hallucinate enterprise details. |
|                                                                          |
| 2. Can a single retrieval call (Vanilla RAG) solve the problem?          |
|    --> PARTIALLY (30% accuracy). Perfect on runbooks, 0% on incidents.   |
|                                                                          |
| 3. What is the fundamental missing component?                            |
|    --> LIVE TELEMETRY TOOLS. Live pod inspection, metric queries,       |
|        and log compaction must be added in Session 3.                    |
+--------------------------------------------------------------------------+
```

---

## 5. Recorded Baseline Sign-Off

- **Recorded Baseline Score:** **30.0% Overall Pass Rate** (Vanilla RAG)
- **Cost per Query:** **$0.000115** (Well within $0.15 ceiling)
- **Mean Latency:** **280.2 ms** (Well within 90s SLA)
- **Approved Next Step for Session 3:** Add **one change at a time** guided by the failure log:
  1. Iteration 1: Hybrid BM25 + Dense RRF retrieval for runbooks.
  2. Iteration 2: Add single telemetry tool (`get_pod_status` & metrics).
  3. Iteration 3: Add conditional routing to prevent invoking expensive tools for simple runbook queries.
