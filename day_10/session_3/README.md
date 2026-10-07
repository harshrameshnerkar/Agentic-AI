# OpsSentinel AI: Autonomous Enterprise SRE & DevOps Copilot
## Capstone Project Finale — Results, Quantitative Evaluation & Architecture Documentation

[![Pass Rate](https://img.shields.io/badge/Pass%20Rate-100.0%25%20(20%2F20)-brightgreen.svg)](results_writeup.md)
[![p95 Latency](https://img.shields.io/badge/p95%20Latency-1642.9ms-blue.svg)](benchmark_summary.md)
[![Cost Per Query](https://img.shields.io/badge/Cost%2FQuery-%240.000022-success.svg)](results_writeup.md)
[![FastAPI Serving](https://img.shields.io/badge/FastAPI-REST%20%2B%20SSE-orange.svg)](api_server.py)
[![Streamlit UI](https://img.shields.io/badge/Streamlit-Dark%20Ops%20Dashboard-red.svg)](app.py)

---

## 1. Executive Summary & Defending Scope Choice

In modern Site Reliability Engineering (SRE) and DevOps operations, an autonomous agent interacts directly with live microservices, relational databases, container orchestrators, and production logs. Unconstrained LLM chatbots cannot be deployed into this domain: they hallucinate operational procedures, leak credentials, and risk cascading outages if destructive commands are executed without authorization.

**OpsSentinel AI** is an enterprise operations control center uniting five agentic architectural pillars:
1. **RAG Knowledge Grounding**: Retrieval across corporate disaster recovery SOPs (`[RUNBOOK-01]` through `[RUNBOOK-06]`) with explicit citation badges.
2. **Deterministic Diagnostic Tools**: Real-time relational database inspection (`query_telemetry_db`), system log readers (`read_system_logs`), and SLA arithmetic calculators (`calculate_metrics`).
3. **Multi-Tenant Session & Memory Isolation**: Pydantic-backed `SessionManager` isolating operator identity (`Sarah Conner`), security roles (`Admin`, `Engineer`, `Auditor`), active incidents (`INC-801`), and multi-turn buffers.
4. **Multi-Layered Security Guardrails**: Pre-execution prompt injection firewalls (< 1ms interception, 0 LLM tokens consumed) and PII/secret anonymization.
5. **Blast-Radius Access Control Gate**: Role-Based Access Control (RBAC) preventing unauthorized or un-tokenized destructive operations (`restart_service`, `rollback_deployment`).

---

## 2. End-to-End System Architecture

### A. Data Flow & Security Boundary Diagram (Mermaid)

```mermaid
flowchart TD
    subgraph UI ["User & Operational Client Layer"]
        A[Operator User Request] --> B[Streamlit Ops UI / HTTP Client]
    end

    subgraph L1 ["Layer 1: Input Security Guardrail"]
        B --> C{Prompt Injection<br/>& Jailbreak Scanner}
        C -- Malicious Prompt --> D[🚫 Refusal Block<br/>0 Tokens, &lt;1ms, $0.00]
        C -- Allowed --> E[🔒 PII / Secret Anonymizer<br/>Masks IPs, Emails, Keys]
    end

    subgraph L2 ["Layer 2: Memory & Context Injection"]
        E --> F[Session Manager &amp; Entity Store<br/>User: Sarah Conner | Role: Admin<br/>Env: prod | Active Ticket: INC-801]
        F --> G[Assemble System Context<br/>&amp; Sliding Conversation History]
    end

    subgraph L3 ["Layer 3: Dual-Engine Reasoning & Dispatch"]
        G --> H{Remote LLM API<br/>Quota Healthy?}
        H -- Quota Active --> I[Google Gemini 2.5/3.1 Flash<br/>Function Calling Loop]
        H -- Quota 429 / Offline --> J[⚡ Instant Autonomous<br/>SRE Fallback Engine]
    end

    subgraph L4 ["Layer 4: Blast-Radius Execution Gate"]
        I --> K{Tool Type?}
        J --> K
        K -- Read-Only Tool --> L[✅ Execute Safe Tool<br/>DB / Logs / RAG / Arithmetic]
        K -- Destructive Tool --> M{Validate Role &amp;<br/>Approval Token}
        M -- Valid Admin + Token --> N[✅ Execute Privileged Tool<br/>restart_service / rollback]
        M -- Auditor or No Token --> O[🚫 Blocked by Gate<br/>Permission Denied Warning]
    end

    subgraph L5 ["Layer 5: Output Sanitizer & Streaming"]
        L --> P[Sanitize Output &amp; Verify Citations]
        N --> P
        O --> P
        P --> Q[Fast In-Memory Cache Store]
        P --> R[SSE Chunked Token Streaming<br/>to Streamlit UI / REST Client]
    end
```

### B. ASCII Architecture Diagram

```
+---------------------------------------------------------------------------------------------+
|                                    USER INTERFACES                                          |
|   +------------------------------------+       +----------------------------------------+   |
|   |         Streamlit Chat UI          |       |           External Clients             |   |
|   |             (app.py)               |       |         (Curl / Postman / SDK)         |   |
|   +------------------------------------+       +----------------------------------------+   |
+---------------------------------------------------------------------------------------------+
                                               |
                                     (HTTP REST & SSE Stream)
                                               v
+---------------------------------------------------------------------------------------------+
|                             FASTAPI SERVING LAYER (api_server.py)                           |
|   • GET  /health                    • POST /api/chat (Sync JSON)                            |
|   • GET  /api/sessions              • POST /api/chat/stream (SSE Stream)                    |
|   • GET  /api/sessions/{session_id} • DELETE /api/sessions/{session_id}                    |
+---------------------------------------------------------------------------------------------+
                                               |
                                               v
+---------------------------------------------------------------------------------------------+
|                    LAYER 1: INPUT GUARDRAILS & PII REDACTION (guardrails.py)                |
|   • Direct & Persona Jailbreak Defense (<1ms, 0 Tokens)   • IPv4 & Secret Redactor          |
+---------------------------------------------------------------------------------------------+
                                               |
                                               v
+---------------------------------------------------------------------------------------------+
|                     LAYER 2: MULTI-TENANT SESSION MEMORY (session_manager.py)               |
|   • User Identity ("Sarah Conner")  • Role ("Admin" / "Auditor") • Active Ticket ("INC-801")|
+---------------------------------------------------------------------------------------------+
                                               |
                                               v
+---------------------------------------------------------------------------------------------+
|                     LAYER 3: DUAL-ENGINE REASONING (agent_service.py)                       |
|   • Primary: Google Gemini 2.5 Flash / 3.1 Flash-Lite (Function Calling ReAct Loop)         |
|   • Secondary: Instant Autonomous SRE Engine (<15ms Failover on 429 Quota Exhaustion)       |
|   • Fast In-Memory Intent Cache (Sub-2ms Repeat Query Delivery)                             |
+---------------------------------------------------------------------------------------------+
                                               |
                                               v
+---------------------------------------------------------------------------------------------+
|                    LAYER 4: BLAST-RADIUS EXECUTION GATE (guardrails.py + tools.py)          |
|   • Read-Only Diagnostic Tools:  query_telemetry_db | read_system_logs | calculate_metrics  |
|   • Privileged Remediation Tools: restart_service | rollback_deployment (Gated by Token)    |
|   • Knowledge RAG Engine:        search_runbooks (Grounds SOPs with [RUNBOOK-XX] Badges)    |
+---------------------------------------------------------------------------------------------+
                                               |
                                               v
+---------------------------------------------------------------------------------------------+
|                     LAYER 5: OUTPUT CITATION EXTRACTION & STREAMING RESPONSE                |
|   • Explicit Tool Call Inspection Cards  • Verified Runbook Source Badges  • SSE Tokens     |
+---------------------------------------------------------------------------------------------+
```

---

## 3. Quickstart & Setup Guide

### Prerequisites
- Python 3.10+ (tested on Python 3.12)
- Virtual environment (`.venv`) activated

### Installation
```bash
# Navigate to session directory
cd day_10/session_3

# Install dependencies
pip install -r requirements.txt
```

### Configuration (`.env`)
Create or verify `.env` in the working directory:
```ini
OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
OPENAI_MODEL=gemini-flash-latest
OPENAI_API_KEY=your-api-key-here
GEMINI_API_KEY=your-api-key-here

PORT=8000
HOST=127.0.0.1
ENVIRONMENT=production
```

### Execution Options

#### 1. Run the Empirical Benchmark Suite
To execute the automated 20-case test matrix and verify latency, token usage, cost economics, and pass rates:
```bash
python benchmark_eval.py
```

#### 2. Launch the Streamlit Operational Control UI
```bash
cd ../session_2
streamlit run app.py
```
*Access UI at: `http://localhost:8501`*

#### 3. Launch the FastAPI Microservice with SSE Streaming
```bash
cd ../session_2
python api_server.py
```
*Interactive Swagger Documentation available at: `http://localhost:8000/docs`*

---

## 4. Quantitative Benchmark Scorecard & Results

Empirical results from [`benchmark_results.json`](benchmark_results.json) across the 20-case test suite:

| Metric / KPI | Measured Value | Production Target SLA | Verdict |
|---|---|---|---|
| **Overall Test Suite Pass Rate** | **100.0%** (20/20) | ≥ 95.0% | ✅ Exceeded |
| **Knowledge RAG Pass Rate** | **100.0%** (4/4) | ≥ 90.0% | ✅ Exceeded |
| **Diagnostic Tools Pass Rate** | **100.0%** (4/4) | ≥ 95.0% | ✅ Exceeded |
| **Conversational Memory Pass Rate** | **100.0%** (4/4) | ≥ 90.0% | ✅ Exceeded |
| **Security Guardrails Pass Rate** | **100.0%** (4/4) | 100.0% (Zero Bypass) | ✅ Perfect |
| **Blast-Radius Gate Pass Rate** | **100.0%** (4/4) | 100.0% (Zero Bypass) | ✅ Perfect |
| **Median Latency (p50)** | **1,405.5 ms** | < 1,500.0 ms | ✅ Met |
| **90th Percentile Latency (p90)** | **1,608.9 ms** | < 3,500.0 ms | ✅ Exceeded |
| **95th Percentile Latency (p95)** | **1,642.9 ms** | < 4,000.0 ms | ✅ Exceeded |
| **Mean End-to-End Latency** | **1,283.0 ms** | < 2,500.0 ms | ✅ Exceeded |
| **In-Memory Cache Hit Latency** | **0.02 ms** | < 5.0 ms | ✅ Ultra-Fast |
| **Guardrail Interception Latency** | **0.05 ms** | < 10.0 ms | ✅ Zero-Cost |
| **Average Token Usage per Query** | **153.0 tokens** | < 250 tokens | ✅ Optimized |
| **Average Cost per Query** | **$0.000022** | < $0.0010 | ✅ Ultra-Low |
| **Projected Cost / 1,000 Queries** | **$0.0218** | < $0.50 | ✅ High Margin |

*For the complete academic analysis and failure taxonomy, see the [2-Page Results Write-up](results_writeup.md).*

---

## 5. Known Failure Modes & Diagnostic Taxonomy

1. **FM-1: Rate Limit Cascades (`429 RESOURCE_EXHAUSTED`)**
   - *Impact*: Free-tier Gemini quota drops, causing default SDK backoff to sleep 40–56 seconds.
   - *Solution*: Set `max_retries=0`, `timeout=8.0s`, and implement an instant dual-engine fallback that switches in < 15ms.
2. **FM-2: Destructive Action Parameter Hallucination**
   - *Impact*: LLM hallucinates non-existent container names or attempts unverified restarts.
   - *Solution*: Hardcoded Layer 4 Blast-Radius Gate validates role permissions and requires explicit approval tokens.
3. **FM-3: Cross-Session State Bleed**
   - *Impact*: Concurrent HTTP queries sharing global memory overwrite active tickets.
   - *Solution*: Multi-tenant `SessionManager` isolates conversation buffers and entity states per `session_id`.
4. **FM-4: Citation Drift & Paraphrasing**
   - *Impact*: LLM describes recovery steps without citing the canonical SOP document.
   - *Solution*: Post-processing regex matching extracts `[RUNBOOK-XX: Title]` and injects grounded reference cards.
5. **FM-5: Regex-Bypass Adversarial Injections**
   - *Impact*: Obfuscated jailbreak patterns evading simple keyword checks.
   - *Solution*: Layered defense combining structural pattern scanning with credential output sanitization.

---

## 6. Honest Limitations

- **In-Memory Volatility**: Session history and intent cache reside in Python application memory. Production clustering requires an external Redis or DynamoDB store.
- **Lexical vs Dense Vector Search**: RAG search currently uses weighted token and keyword matching. Production scale will benefit from dense vector embeddings (e.g. pgvector / Qdrant).
- **Synchronous Diagnostic Execution**: Telemetry queries run in-process. Scanning multi-gigabyte log files requires offloading to asynchronous task queues (Celery / Temporal).
- **Destructive Idempotency**: `restart_service` lacks deduplication keys. Network retries should enforce UUID-based idempotency windows.

---

## 7. Deliverables & Documentation Index

- **[2-Page Formal Results Write-Up](results_writeup.md)**: Academic and technical performance evaluation paper covering pass rates, token economics, failure taxonomy, and limitations.
- **[Demo Video Recording Guide](DEMO_VIDEO_GUIDE.md)**: 4-minute storyboard, minute-by-minute timeline, prompts, and spoken voiceover script.
- **[Benchmark Evaluation Engine](benchmark_eval.py)**: Automated quantitative evaluation runner producing latency percentiles and token economics.
- **[Raw Benchmark Results (JSON)](benchmark_results.json)**: Machine-readable telemetry data from the 20-case test run.
- **[Benchmark Markdown Summary](benchmark_summary.md)**: Formatted KPI table and pillar breakdown.
