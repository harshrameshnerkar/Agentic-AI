# Day 15 Capstone: OpsSentinel AI Enterprise Edition
## Hardened Production SRE Copilot Platform: Async, Durable State, HITL, Deployed, Monitored & CI-Gated

[![Pass Rate](https://img.shields.io/badge/CI%20Pass%20Rate-100.0%25-brightgreen.svg)](session_1/eval_ci_runner.py)
[![p50 Latency](https://img.shields.io/badge/p50%20Latency-54.3ms-blue.svg)](session_3/BENCHMARK_REPORT.md)
[![p95 Latency](https://img.shields.io/badge/p95%20Latency-181.8ms-blue.svg)](session_3/BENCHMARK_REPORT.md)
[![Unit Cost](https://img.shields.io/badge/Cost%2FQuery-%240.000018-success.svg)](session_3/BENCHMARK_REPORT.md)
[![Audit Integrity](https://img.shields.io/badge/Audit%20Chain-SHA--256%20Verified-purple.svg)](session_1/hitl_gateway.py)
[![Docker Ready](https://img.shields.io/badge/Docker-Multi--Stage%20Compose-orange.svg)](docker-compose.yml)
[![Design Doc](https://img.shields.io/badge/Design%20Doc-4--Page%20TDD%20Reviewed-red.svg)](session_2/TECHNICAL_DESIGN_DOCUMENT.md)

---

## 1. Executive Summary & Curriculum Scope

**OpsSentinel AI Enterprise** represents the ultimate capstone of the **15-Day Agentic AI Master Curriculum**. It hardens the Week 2 autonomous agent architecture into a mission-critical, enterprise-grade operations control center for Site Reliability Engineering (SRE) and cloud infrastructure.

### Complete Session Directory:

| Session | Focus Area | Deliverables & Artifacts |
|---|---|---|
| **[Session 1: Production Capstone Build](session_1/)** | Hardened Agent Engine | • [`query_router.py`](session_1/query_router.py): Sub-2ms regex & semantic intent triage.<br>• [`async_engine.py`](session_1/async_engine.py): Parallel async tool dispatch via `asyncio.gather`.<br>• [`durable_state.py`](session_1/durable_state.py): Transactional SQLite WAL checkpointer.<br>• [`hitl_gateway.py`](session_1/hitl_gateway.py): Cryptographic approval gate & SHA-256 audit logger.<br>• [`api_server.py`](session_1/api_server.py): FastAPI microservice with REST & HITL endpoints.<br>• [`dashboard.py`](session_1/dashboard.py): Streamlit real-time operations dashboard.<br>• [`eval_ci_runner.py`](session_1/eval_ci_runner.py): Golden evaluation harness & CI regression gate.<br>• [`Dockerfile`](Dockerfile) & [`docker-compose.yml`](docker-compose.yml): Production container specs. |
| **[Session 2: Technical Design Document](session_2/)** | Architecture & Engineering Defense | • [`TECHNICAL_DESIGN_DOCUMENT.md`](session_2/TECHNICAL_DESIGN_DOCUMENT.md): 4-Page publication-grade TDD covering Problem, Constraints, ASCII Topology, 4 Rejected Alternatives, Failure Modes, Security Posture, and 10x Cost Model.<br>• [`ARCHITECTURE_SPEC.md`](session_2/ARCHITECTURE_SPEC.md): OpenAPI schemas and SQLite index definitions. |
| **[Session 3: Results & Cost Package](session_3/)** | Empirical Telemetry & Scorecards | • [`eval_and_cost_package.py`](session_3/eval_and_cost_package.py): Stratified pass rate & 10x cost package runner.<br>• [`EVAL_AND_COST_PACKAGE.md`](session_3/EVAL_AND_COST_PACKAGE.md): Itemized monthly bills, ASCII bar charts & honest limitations.<br>• [`cost_and_eval_package.json`](session_3/cost_and_eval_package.json): Machine-readable telemetry data.<br>• [`benchmark_runner.py`](session_3/benchmark_runner.py): Empirical concurrency engine & [`BENCHMARK_REPORT.md`](session_3/BENCHMARK_REPORT.md). |
| **[Session 4: Final Assessment](session_4/)** | Defense, Presentation & Whiteboard | • [`FINAL_PRESENTATION_SCRIPT.md`](session_4/FINAL_PRESENTATION_SCRIPT.md): 20-Minute presentation script for mixed technical/non-technical audience.<br>• [`SYSTEM_DESIGN_INTERVIEW_DEFENSE.md`](session_4/SYSTEM_DESIGN_INTERVIEW_DEFENSE.md): Master architectural defense transcript under tough probes.<br>• [`WHITEBOARD_AGENT_SYSTEM_DESIGN.md`](session_4/WHITEBOARD_AGENT_SYSTEM_DESIGN.md): Edge Sentinel air-gapped industrial agent whiteboarded under fresh constraints.<br>• [`operational_runbook.md`](session_4/operational_runbook.md) & [`FINAL_RUBRIC_ASSESSMENT.md`](session_4/FINAL_RUBRIC_ASSESSMENT.md): Production SOP & 100/100 Rubric alignment. |

---

## 2. Quickstart: Clean Clone Execution

OpsSentinel Enterprise runs cleanly from a fresh git clone with zero external unmocked dependencies.

### Step 1: Environment Setup
```bash
# Clone and enter workspace
git clone <repo-url>
cd Agentic-AI

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install pinned dependencies
pip install -r day_15/requirements.txt
```

### Step 2: Run Master Automated Test Suite
```bash
# Validates all 14 end-to-end integration tests across all sessions
python day_15/test_day_15_all.py
```

### Step 3: Run Evaluation & 10x Cost Package
```bash
# Generates stratified pass rates, latency charts, and 10x volume bill
python day_15/session_3/eval_and_cost_package.py
```

### Step 4: Test CI Evaluation & Regression Gating
```bash
# 1. Baseline Run: 100% Pass Rate -> Exit Code 0 (Build Passes)
python day_15/session_1/eval_ci_runner.py

# 2. Simulated Regression: Pass Rate Drops to 66.7% -> Exit Code 1 (Build Fails)
python day_15/session_1/eval_ci_runner.py --simulate-regression
```

### Step 4: Run Interactive CLI Console
```bash
# Direct SRE Diagnostic Query
python day_15/session_1/main.py --query "Check metrics and health for auth-service"

# Inspect Active Durable Sessions
python day_15/session_1/main.py --list-sessions

# Verify Cryptographic Audit Chain Integrity
python day_15/session_1/main.py --audit-check
```

### Step 5: Launch FastAPI Production Microservice
```bash
python day_15/session_1/api_server.py
# API is accessible at: http://localhost:8000
# OpenAPI Docs at:     http://localhost:8000/docs
```

### Step 6: Launch Streamlit Operational Control Center
```bash
streamlit run day_15/session_1/dashboard.py
# Dashboard is accessible at: http://localhost:8501
```

### Step 7: Containerized Deployment via Docker Compose
```bash
docker compose -f day_15/docker-compose.yml up --build -d
# Healthcheck: curl http://localhost:8000/health
```

---

## 3. Empirical Performance Scorecard

Aggregated across multi-scenario empirical evaluation runs (`session_3/benchmark_runner.py`):

```text
=============================================================================
METRIC                                  VALUE                   TARGET SLA
-----------------------------------------------------------------------------
Overall Evaluation Pass Rate:           100.0% (12/12)          >= 90.0%
Layer 0 Guardrail Triage Latency:       < 2.0 ms                <= 5.0 ms
Median Diagnostic Latency (p50):        54.3 ms                 <= 100.0 ms
95th Percentile Latency (p95):          181.8 ms                <= 500.0 ms
Average Tokens per Interaction:         245 tokens              <= 500 tokens
Average Unit Cost per Query:            $0.000018               <= $0.000030
Projected Monthly OPEX (10k/day):       $5.48 / month           <= $15.00 / month
Cryptographic Audit Chain Integrity:    100% Valid (SHA-256)    Strict Invariant
=============================================================================
```

---

## 4. Architectural Highlights

```text
                          INCOMING INQUIRY
                                 │
                                 ▼
                     Layer 0 Guardrail Triage
                     (Sub-2ms Regex Intercept)
                    ┌────────────┴────────────┐
             [Adversarial]              [Legitimate]
                    │                         │
                    ▼                         ▼
            IMMEDIATE BLOCK            Query Router
            (0 Tokens, $0.00)                 │
                                 ┌────────────┼────────────┐
                                 ▼            ▼            ▼
                             INFO_SOP    DIAGNOSTIC    DESTRUCTIVE
                             (Runbook)   (Read Tools)  (Remediation)
                                 │            │            │
                                 ▼            ▼            ▼
                             Hybrid RAG   async.gather   HITL Gate
                               (BM25)     (4 Tools)     (Suspension)
                                 │            │            │
                                 └────────────┬────────────┘
                                              ▼
                                   SQLite WAL Checkpoint
                                              ▼
                                    SHA-256 Audit Logger
                                              ▼
                                      Response Egress
`
