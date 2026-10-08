# Agentic AI: Production-Grade Autonomous Systems & Enterprise Capstone

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg?logo=python&logoColor=white)](https://python.org)
[![FastAPI Microservice](https://img.shields.io/badge/FastAPI-Production%20REST-009688.svg?logo=fastapi&logoColor=white)](day_15/session_1/api_server.py)
[![CI/CD Pass Rate](https://img.shields.io/badge/CI%20Eval%20Gate-100.0%25%20Pass-brightgreen.svg?logo=github-actions&logoColor=white)](.github/workflows/day15_capstone_ci.yml)
[![p50 Latency](https://img.shields.io/badge/p50%20Latency-54.3ms-success.svg)](day_15/session_3/BENCHMARK_REPORT.md)
[![p95 Latency](https://img.shields.io/badge/p95%20Latency-181.8ms-informational.svg)](day_15/session_3/BENCHMARK_REPORT.md)
[![Durable State](https://img.shields.io/badge/State%20Engine-SQLite%20WAL%20ACID-orange.svg)](day_15/session_1/durable_state.py)
[![Security & HITL](https://img.shields.io/badge/HITL%20Gate-Cryptographic%20SHA--256-purple.svg)](day_15/session_1/hitl_gateway.py)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Author & Engineer:** [Harsh Ramesh Nerkar](https://github.com/harshrameshnerkar)  
> **Repository:** [`harshrameshnerkar/Agentic-AI`](https://github.com/harshrameshnerkar/Agentic-AI)  
> **Program:** **Agentic AI — Production Engineering Curriculum**

---

## 📌 Executive Summary

This repository contains the complete **15-day hands-on engineering assignments** completed across the **15-Day Autonomous Agentic AI Engineering Curriculum**. 

Moving far beyond naive prompt wrappers and single-turn completions, this repository implements the full architectural spectrum of modern **Autonomous Agent Engineering, Multi-Agent Swarms, Model Context Protocol (MCP), and LLMOps at Scale**:
- Deterministic ReAct execution loops & structured tool schemas
- Multi-agent hierarchical supervisor patterns & worker swarms
- Adversarial prompt injection defense & safety guardrails
- Sub-millisecond intent routing & hybrid adaptive RAG
- High-throughput asynchronous concurrency (`asyncio.gather`)
- Durable transactional state machines with SQLite Write-Ahead Logging (WAL)
- Human-in-the-Loop (HITL) approval gates with cryptographic SHA-256 audit chaining
- Automated CI/CD regression gates with golden evaluation suites
- Production containerization (Docker & docker-compose) and real-time observability

---

## 📚 Complete 15-Day Topic-Wise Syllabus & Deliverables

| Days | Topic Name | Technical Scope & Key Deliverables | Code Link |
|:---:|---|---|:---:|
| **1** | **LLM Fundamentals & API Basics** | • Setup, first LLM API calls, tokenization mechanics<br>• Temperature, top_p, frequency penalty parameters, context windows, cost models | [`day_01/`](day_01/) |
| **2** | **Advanced Prompting & Structured Output** | • Chain-of-Thought (CoT), Task Decomposition, Few-Shot prompting<br>• Pydantic schema validation, JSON mode parsing, prompt templates & versioning | [`day_02/`](day_02/) |
| **3** | **Embeddings, Vector DB & RAG** | • Dense vector embeddings, cosine/dot similarity, chunking strategies<br>• Vector database indexing, retrieval failure modes, semantic search | [`day_03/`](day_03/) |
| **4** | **Tool Calling & Function Execution** | • OpenAI/Anthropic/Gemini function schemas, tool registration<br>• Multi-step tool use, argument extraction, error handling loops | [`day_04/`](day_04/) |
| **6** | **Tool Calling & MCP** | • Model Context Protocol (MCP) integration & tool design best practices<br>• Blast-radius classification, safe read vs destructive write tiers, compensating rollbacks | [`day_06/`](day_06/) |
| **7** | **Agents: ReAct, Frameworks & Memory** | • Pure Thought-Action-Observation ReAct execution loops<br>• LangGraph `StateGraph` workflows, conversational & episodic checkpointed memory | [`day_07/`](day_07/) |
| **8** | **Multi-Agent Systems & Orchestration** | • Centralized Supervisor router, collaborative worker swarms<br>• Inter-agent communication protocols, context compaction & engineering | [`day_08/`](day_08/) |
| **9** | **Guardrails, Security & Agent Evaluation** | • Prompt injection detection, jailbreak mitigation, Canary token leaks<br>• Dual-LLM safety boundary guards, adversarial red-teaming test suite | [`day_09/`](day_09/) |
| **10** | **Capstone, Deployment & Final Review** | • OpsSentinel AI Midterm Capstone: autonomous multi-tool SRE diagnostic copilot<br>• Containerized deployment, interactive Streamlit UI, comprehensive review | [`day_10/`](day_10/) |
| **11** | **Advanced Retrieval Architectures** | • Hybrid dense/sparse search (BM25 + vector), graph & structured metadata RAG<br>• Query rewriting, sub-query decomposition, dynamic retrieval routing | [`day_11/`](day_11/) |
| **12** | **Fine-Tuning & Model Customisation** | • Decision framework: RAG vs Fine-Tuning, SFT data synthesis & QC filters<br>• Parameter-Efficient Fine-Tuning (PEFT/LoRA), multi-tier cost router | [`day_12/`](day_12/) |
| **13** | **Production Agent Architecture** | • High-throughput async tool dispatch via `asyncio.gather` (3.2x speedup)<br>• SQLite WAL ACID checkpointer, multi-tenant state isolation, circuit breakers | [`day_13/`](day_13/) |
| **14** | **LLMOps, Evaluation at Scale & Incidents** | • Automated GitHub Actions CI regression gates with 100-case golden datasets<br>• Canary/shadow trace evaluators, emergency kill switches & postmortems | [`day_14/`](day_14/) |
| **15** | **Production Capstone & Final Assessment** | • Hardened autonomous SRE control center with sub-2ms intent router<br>• FastAPI microservice, SHA-256 Merkle audit trail, HITL approval gate<br>• 4-Page publication TDD, 10x cost projection, 20-min executive defense | [`day_15/`](day_15/) |
| **16** | **Scoping a Real Problem** | • **Session 1 (Discovery):** Stakeholder problem statement in stakeholder's words, 7-stage workflow replacement analysis & Monte Carlo MTTR simulation<br>• **Session 2 (Constraints):** Signed-off success metrics charter (95% accuracy, <=90s p95 latency, <=$0.15 cost ceiling), 3-tier blast radius classification, 5 Never-Automate red lines & cryptographic HMAC-SHA256 HITL approval gateway | [`day_16/`](day_16/) |

---

## 🏆 Final Capstone Spotlight: OpsSentinel AI Enterprise (Day 15)

The program culminates in **OpsSentinel AI Enterprise** ([`day_15/`](day_15/README.md)) — an autonomous Site Reliability Engineering (SRE) copilot designed to detect, triage, and remediate distributed cloud infrastructure incidents under enterprise SLAs and strict blast-radius controls.

```
                           +-------------------------------------------+
                           |         Inbound Operations Query          |
                           |   (Terminal CLI / REST API / Webhook)     |
                           +---------------------+---------------------+
                                                 |
                                                 v
                           +-------------------------------------------+
                           |        Sub-2ms Semantic Query Router      |
                           |  (Regex Pre-Filter + Tenant-Scoped SOPs)  |
                           +---------------------+---------------------+
                                                 |
             +--------------------+--------------+--------------+---------------------+
             |                    |                             |                     |
             v                    v                             v                     v
    [ INFO_SOP (RAG) ]   [ DIAGNOSTIC_READ ]          [ DESTRUCTIVE_WRITE ]   [ ADVERSARIAL_ATTACK ]
    Vector Runbook SOP   Parallel async tools         Tier 3 Blast Radius     Immediate Abort
    Direct response      (Metrics, Logs, Topology)    State: AWAITING_APV     Security Audit Log
             |                    |                             |                     |
             +--------------------+-----------------------------+---------------------+
                                  |
                                  v
        +---------------------------------------------------------------+
        |               Transactional Durable Checkpointer              |
        |              (SQLite WAL ACID - Crash-Safe State)             |
        +-------------------------------+-------------------------------+
                                        |
                   +--------------------+--------------------+
                   |                                         |
                   v                                         v
   +-------------------------------+         +-------------------------------+
   |   Human-In-The-Loop Gateway   |         | Cryptographic Audit Trail Log |
   |  (HMAC Token / Role Approval) |         | (SHA-256 Tamper-Evident Chain)|
   +---------------+---------------+         +-------------------------------+
                   |
                   v (Approved)
   +-------------------------------+
   | Executing Blast-Radius Action |
   | (Rollback Hook + Verification)|
   +-------------------------------+
```

### Key Architectural Highlights
1. **Parallel Concurrency**: 3.2x latency reduction over sequential tool dispatch using `asyncio.gather` for cluster telemetry, logs, and topology checks.
2. **Crash-Resilient State**: 100% state recovery across mid-execution crashes with SQLite WAL checkpointing and idempotent replay.
3. **Cryptographic Blast-Radius Control**: Any Tier-3 destructive operation (service restarts, scaling, cache flushes) is paused in `AWAITING_APPROVAL`. Authorized actions produce an immutable SHA-256 Merkle-style audit log.
4. **CI/CD Quality Gates**: Fully wired into GitHub Actions (`.github/workflows/day15_capstone_ci.yml`) enforcing $\ge 90\%$ pass rate, 0 critical regressions, and sub-250ms p95 latency.

---

## 📊 Empirical Benchmarks & Telemetry

Empirical test data measured on `Python 3.12` running against the golden evaluation harness (12 stratified incident cases):

| Metric | Target SLA | Measured Baseline | Status |
|---|:---:|:---:|:---:|
| **Overall Pass Rate** | $\ge 90.0\%$ | **$100.0\%$** |  PASS |
| **Critical Regressions** | $0$ | **$0$** |  PASS |
| **Adversarial Jailbreak Defense** | $100.0\%$ | **$100.0\%$** (Blocked) |  PASS |
| **Sequential Diagnostics Latency** | — | $482.4 \text{ ms}$ | Baseline |
| **Async Parallel Latency** | $< 250 \text{ ms}$ | **$150.1 \text{ ms}$ (3.2x Speedup)** |  PASS |
| **p50 Latency (Overall)** | $< 100 \text{ ms}$ | **$54.3 \text{ ms}$** |  PASS |
| **p95 Latency (Overall)** | $< 250 \text{ ms}$ | **$181.8 \text{ ms}$** |  PASS |
| **Audit Chain Cryptographic Integrity** | 100% Intact | **SHA-256 Validated** |  PASS |

---

## 🚀 Quickstart Guide

### 1. Prerequisites & Virtual Environment
```bash
git clone https://github.com/harshrameshnerkar/Agentic-AI.git
cd Agentic-AI

# Create virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r day_15/requirements.txt
```

### 2. Run All Capstone Master Tests
```bash
python day_15/test_day_15_all.py
```
*Expected: 16 integration tests passing in ~4 seconds with 100% evaluation pass rate.*

### 3. Launch OpsSentinel REST Microservice
```bash
python day_15/session_1/api_server.py
```
*Microservice starts at `http://localhost:8000`. Access Swagger UI docs at `http://localhost:8000/docs`.*

### 4. Run CLI Operations
```bash
# Verify cryptographic audit chain integrity
python day_15/session_1/main.py --audit-check

# Run an infrastructure diagnostic query
python day_15/session_1/main.py -q "check cpu and error rate on auth-service"

# Trigger a destructive write requiring HITL approval
python day_15/session_1/main.py -q "restart pod auth-service-prod-0"
```

---

## 👨‍💻 Author & Connect

**Harsh Ramesh Nerkar**  
*Autonomous AI Systems Engineer | Production LLMOps Architect*  
- **GitHub:** [@harshrameshnerkar](https://github.com/harshrameshnerkar)  
- **Repository:** [harshrameshnerkar/Agentic-AI](https://github.com/harshrameshnerkar/Agentic-AI)
