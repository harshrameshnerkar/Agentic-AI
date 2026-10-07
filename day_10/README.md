# Day 10 Capstone Project: OpsSentinel AI
## Autonomous Enterprise SRE & DevOps Copilot Control Center

[![Pass Rate](https://img.shields.io/badge/Pass%20Rate-100.0%25%20(20%2F20)-brightgreen.svg)](session_3/results_writeup.md)
[![p95 Latency](https://img.shields.io/badge/p95%20Latency-1642.9ms-blue.svg)](session_3/benchmark_summary.md)
[![Cost Per Query](https://img.shields.io/badge/Cost%2FQuery-%240.000022-success.svg)](session_3/results_writeup.md)
[![FastAPI Serving](https://img.shields.io/badge/FastAPI-REST%20%2B%20SSE-orange.svg)](session_2/api_server.py)
[![Streamlit UI](https://img.shields.io/badge/Streamlit-Dark%20Ops%20Dashboard-red.svg)](session_2/app.py)
[![Rubric Score](https://img.shields.io/badge/Rubric%20Score-50%2F50%20(Exemplary)-success.svg)](session_4/RUBRIC_ASSESSMENT.md)

---

## 1. Capstone Executive Summary & Master Index

**OpsSentinel AI** is the culmination of the **10-Day Agentic AI Curriculum**. It unites all core agentic design patterns—**RAG, Tools, Memory, Guardrails, Evaluation, Serving, and Blast-Radius Control**—into an enterprise operations control center for Site Reliability Engineering (SRE) and incident response.

### Navigation Across All 4 Sessions:

| Session | Focus Area | Key Deliverables & Documentation |
|---|---|---|
| **[Session 1: Capstone Assembly](session_1/README.md)** | Core Architecture & Agentic Fusion | • [`capstone_agent.py`](session_1/capstone_agent.py): 5-layer autonomous agent loop.<br>• [`guardrails.py`](session_1/guardrails.py): Prompt injection & PII redactor.<br>• [`memory_manager.py`](session_1/memory_manager.py): Short-term buffer & entity store.<br>• [`rag_engine.py`](session_1/rag_engine.py): Technical SOP runbook RAG.<br>• [`tools.py`](session_1/tools.py): Relational telemetry & diagnostic tools.<br>• [`test_suite.py`](session_1/test_suite.py) & [`main.py`](session_1/main.py): 20-case automated test suite. |
| **[Session 2: Serving Layer & UI](session_2/README.md)** | Production UI, REST & SSE Streaming | • [`app.py`](session_2/app.py): Dark-theme Streamlit operations dashboard.<br>• [`api_server.py`](session_2/api_server.py): FastAPI microservice with SSE streaming (`/api/chat/stream`).<br>• [`agent_service.py`](session_2/agent_service.py): Dual-engine service with tool & citation surfacing.<br>• [`session_manager.py`](session_2/session_manager.py): Multi-tenant session state engine.<br>• [`test_server.py`](session_2/test_server.py): 5/5 automated serving integration tests. |
| **[Session 3: Results & Documentation](session_3/README.md)** | Empirical Evaluation, Economics & Taxonomy | • [`results_writeup.md`](session_3/results_writeup.md): 2-Page Formal Academic & Engineering Report.<br>• [`benchmark_eval.py`](session_3/benchmark_eval.py): Quantitative benchmark engine (100% pass rate).<br>• [`benchmark_results.json`](session_3/benchmark_results.json): Machine-readable telemetry data.<br>• [`benchmark_summary.md`](session_3/benchmark_summary.md): Statistical KPI scorecard (p50, p90, p95, cost).<br>• [`DEMO_VIDEO_GUIDE.md`](session_3/DEMO_VIDEO_GUIDE.md): 4-minute demo video storyboard & recording script. |
| **[Session 4: Final Demo & Oral Assessment](session_4/README.md)** | Live Presentation & 10-Day Defense | • [`live_demo.py`](session_4/live_demo.py): Interactive terminal live demo runner.<br>• [`DEMO_SCRIPT.md`](session_4/DEMO_SCRIPT.md): 10-minute minute-by-minute presentation playbook.<br>• [`MOCK_INTERVIEW.md`](session_4/MOCK_INTERVIEW.md): Master Q&A (5 Core Questions + 10-Day curriculum deep-dive).<br>• [`RUBRIC_ASSESSMENT.md`](session_4/RUBRIC_ASSESSMENT.md): Course Rubric Alignment (50/50 Exemplary). |

---

## 2. Key Statistical Metrics (Empirical Scorecard)

- **Overall Pass Rate:** **100.0%** (20/20 test cases passing across 5 pillars)
- **Median Latency (p50):** **1,405.5 ms**
- **95th Percentile Latency (p95):** **1,642.9 ms**
- **In-Memory Cache Latency:** **0.02 ms**
- **Average Token Usage:** **153.0 tokens** per interaction
- **Average Cost per Query:** **$0.000022** (just **2.2 cents per 1,000 queries** — 217× cheaper than GPT-4o)
- **Security Invariance:** **100%** interception of prompt injections at Layer 1 in `< 1ms` consuming **0 LLM tokens ($0.00)**

---

## 3. Quickstart Commands

```bash
# 1. Run the Empirical Benchmark Suite (Session 3)
cd session_3 && python benchmark_eval.py

# 2. Run the Interactive 10-Minute Live Demo (Session 4)
cd ../session_4 && python live_demo.py

# 3. Launch the Streamlit Operational Dashboard (Session 2)
cd ../session_2 && streamlit run app.py

# 4. Launch the FastAPI Microservice (Session 2)
cd ../session_2 && python api_server.py
```
