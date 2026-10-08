# Day 16 - Session 1: Stakeholder Discovery & Problem Scoping

## 📌 Syllabus & Session Objectives
- **Session:** Day 16 - Session 1: Stakeholder Discovery
- **Topic:** Scoping a Real Problem
- **What to Learn:** Meet the internal stakeholder or a mentor playing that role. Understand the actual workflow being replaced or assisted. Ask what a human does today, how long it takes, and what happens when they get it wrong.
- **Task:** A written problem statement in the stakeholder's words, plus the workflow it replaces.
- **Resources:** Intern (Harsh Ramesh Nerkar) + Stakeholder (Marcus Vance, VP Infrastructure) + Mentor (Dr. Elena Rostova, Principal AI Architect).

---

## 🏛️ Executive Problem Scoping Summary

In this session, we conducted a stakeholder discovery interview with **Marcus Vance (VP of Cloud Infrastructure & Reliability)** to scope a real-world enterprise problem: **Autonomous Production Cloud Incident Triage & Remediation**.

### 1. The Problem Statement (In the Stakeholder's Exact Words)
> *"Look, here is the brutal truth about our production operations:*
>
> *At 2:30 in the morning, an alert fires on PagerDuty. An on-call engineer gets woken up out of a deep sleep. Their heart rate spikes, their brain is foggy, and they have exactly 15 minutes before our SLA breach countdown begins.*
>
> *What does that engineer have to do today? They have to log into Okta, fight with VPN multi-factor auth, open six different browser windows — Datadog for CPU spikes, Grafana for latency curves, Splunk for log traces, ArgoCD for deployment status, AWS CloudWatch, and Confluence for some outdated runbook written eight months ago that nobody maintains.*
>
> *By the time they even correlate the logs with the pod crash and find out that a recent canary deployment ran out of memory, **45 to 60 minutes have evaporated**. That is 45 minutes of customers experiencing 504 errors on checkout.*
>
> *And that’s not even the worst part. The worst part is **when they get it wrong**.*
>
> *Six weeks ago, an engineer panicked during an incident, misread the Kubernetes cluster namespace, and issued a `kubectl scale --replicas=0` on our production payments service instead of the staging replica. That single human mistake caused a 38-minute total checkout outage, cost us $185,000 in direct contractual SLA refunds, and severely damaged customer trust.*
>
> *We don't need a novelty chatbot that spits out generic troubleshooting advice. We need an **autonomous, deterministic Agentic AI Copilot** that can ingest the alert, instantly execute read-only diagnostic telemetry across logs, metrics, and topology in parallel within 30 seconds, match the root cause against living runbooks, and present the on-call engineer with a verified, one-click remediation plan — while strictly locking any destructive action behind cryptographic human approval.*
>
> *If you can eliminate the 45 minutes of manual log-digging and prevent catastrophic fat-finger mistakes, that transforms our entire business."*
>
> — **Marcus Vance, VP of Infrastructure & Reliability Engineering**

---

## 🔄 The Workflow Being Replaced: As-Is vs. To-Be

```
CURRENT HUMAN BASELINE (As-Is: ~85.5 mins)
[Alert] ──> [VPN & MFA (7.5m)] ──> [Metrics Hunt (12m)] ──> [Log Grep (20m)] ──> [Git/ArgoCD (11m)] ──> [Runbook Search (15m)] ──> [Manual kubectl (8m)] ──> [Verification (12.5m)]

PROPOSED AGENTIC AI (To-Be: ~1.6 mins total)
[Alert] ──> [Sub-2ms Router] ──> [Parallel Diagnostics: Logs, Metrics, Topology (<30s)] ──> [RAG Runbook Match] ──> [HITL Cryptographic Gate] ──> [Self-Healing Execution]
```

### 7-Stage Granular Comparison

| Stage | Activity | Human Baseline (As-Is) | Agentic AI (To-Be) | Speedup |
|:---:|---|:---:|:---:|:---:|
| **1** | **Alert Ingestion & MFA Auth** | 5 – 10 mins (Manual VPN/Duo) | 1.2 secs (Webhook) | **375x** |
| **2** | **Metrics Dashboard Inspection** | 10 – 15 mins (Datadog/Grafana hunt) | 8.5 secs (Parallel API) | **85x** |
| **3** | **Log Harvesting & Stack Traces** | 15 – 25 mins (Splunk/Coralogix query) | 14.0 secs (Semantic regex) | **86x** |
| **4** | **Deployment & Git Correlation** | 10 – 15 mins (ArgoCD commit diffs) | 4.5 secs (Git API diff) | **147x** |
| **5** | **Runbook Lookup & Root Cause** | 10 – 20 mins (Confluence search) | 12.0 secs (Dynamic RAG SOP) | **75x** |
| **6** | **Remediation Execution** | 5 – 10 mins (Terminal kubectl) | 3.0 secs (HITL Token) | **160x** |
| **7** | **Post-Mortem Logging & Verify** | 10 – 15 mins (Jira/Statuspage) | 15.0 secs (Auto-brief) | **50x** |
| **Total** | **Mean Time to Triage / MTTR** | **65 – 110 minutes (Avg 85.5m)** | **< 60 sec triage (Avg 1.6m)** | **~88x** |

---

## 💥 What Happens When Humans Get It Wrong

1. **Fat-Finger Blast Radius Disasters**: Accidental execution against `prod` namespace rather than `canary` taking down core revenue systems ($185,000 SLA breach penalty).
2. **Misdiagnosis & Red Herring Pursuit**: Restarting frontend containers for 45 minutes while the actual root cause was a deadlocked Postgres query.
3. **Thundering Herd Crash**: Running destructive cache flushes (`FLUSHALL`) without realizing database cold-cache thundering herd will crash primary replicas.
4. **On-Call Burnout**: Repeated 2:00 AM awakenings leading to high senior SRE turnover ($150,000 recruiting cost per engineer).

---

## 📂 Deliverables & File Directory

- [STAKEHOLDER_PROBLEM_STATEMENT.md](STAKEHOLDER_PROBLEM_STATEMENT.md): Official problem statement in the stakeholder's words, organizational profile, and quantitative pain points.
- [WORKFLOW_REPLACEMENT_ANALYSIS.md](WORKFLOW_REPLACEMENT_ANALYSIS.md): Comprehensive stage-by-stage analysis of the human workflow being replaced, failure mode dissection, and To-Be architecture.
- [INTERVIEW_TRANSCRIPT.md](INTERVIEW_TRANSCRIPT.md): Verbatim discovery interview between AI Intern, VP Stakeholder, and Mentor Architect.
- [workflow_simulator.py](workflow_simulator.py): Analytical engine modeling human vs. agentic stochastic triage timings, error rates, and Monte Carlo ROI projections.
- [main.py](main.py): Interactive CLI to review problem statement, inspect workflow, run simulation, and export JSON summaries.
- [test_workflow.py](test_workflow.py): Test suite validating all 7 stages, single incident simulation, Monte Carlo aggregation, and artifact integrity.
- [requirements.txt](requirements.txt): Environment configuration.

---

## 🚀 Execution & Verification

### 1. Run Interactive Discovery CLI
```bash
python day_16/session_1/main.py
```

### 2. Run Monte Carlo Simulation & Export Report
```bash
python day_16/session_1/main.py --simulate --export day_16/session_1/executive_discovery_summary.json
```

### 3. Run Test Suite
```bash
python day_16/session_1/test_workflow.py
```
*Expected: 5 tests passing in < 0.05 seconds.*
