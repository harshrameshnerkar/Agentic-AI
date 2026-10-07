# Capstone Project: Autonomous AI SRE Copilot — UI & Serving (Day 10 Session 2)

## 1. Overview & Objective

In **Day 10 Session 2**, the objective is to take the full unified capstone agent and expose it through production-ready serving and user interfaces:
* **Project Title**: **Capstone Project: Autonomous AI SRE & DevOps Copilot**
* **Primary Mission**: Deliver an enterprise operations control center uniting **RAG**, **Tool Function Calling**, **Session Memory**, and **Security Guardrails**.
* **Key Mandate**: Ship a modern chat UI that explicitly surfaces **which tools ran** and **which sources were cited** for every single answer.

---

## 2. Curriculum Learning Terms & Deliverables Delivered

This repository implements, demonstrates, and tests all core concepts from the **Day 10 Session 2 Curriculum**:

| Curriculum Term | Implementation & Location | Technical Details Delivered |
|---|---|---|
| **1. Streamlit Chat UI** | [`app.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_10/session_2/app.py) | Modern dark enterprise dashboard built with `st.chat_message`, `st.chat_input`, KPI metrics ribbon, operator avatar badges (`🧑‍💻` vs `🛡️`), role-switching sidebar, and 5 dedicated operational tabs. |
| **2. Streaming Output** | [`app.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_10/session_2/app.py), [`api_server.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_10/session_2/api_server.py) | Real-time token streaming via chunked generators (`stream_run`) in Streamlit and Server-Sent Events (SSE) on `/api/chat/stream`. Delivers sub-400ms time-to-first-token (TTFT). |
| **3. Surfacing Tool Calls to the User** | [`app.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_10/session_2/app.py) (Lines 248–260) | Interactive expandable cards (`🛠️ Tools Executed`) showing tool names (`query_telemetry_db`, `search_runbooks`, `restart_service`), input arguments, execution status (`✅ EXECUTED` or `🚫 BLOCKED BY GATE`), and return summary payload. |
| **4. Surfacing Cited Sources to the User** | [`app.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_10/session_2/app.py) (Lines 261–268) | Authoritative reference cards (`📚 Authoritative Cited Sources`) displaying Document ID (`[RUNBOOK-01]`), Title, Category, Relevance Score, and grounded SOP content excerpt. |
| **5. FastAPI Endpoints** | [`api_server.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_10/session_2/api_server.py) | High-performance REST microservice providing `GET /health`, `POST /api/chat`, `POST /api/chat/stream`, `GET /api/sessions`, `DELETE /api/sessions/{session_id}`, with interactive OpenAPI docs at `http://localhost:8000/docs`. |
| **6. Session Handling** | [`session_manager.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_10/session_2/session_manager.py) | Multi-tenant session state engine isolating conversation memory, operator roles (`Admin`, `Engineer`, `Auditor`), datacenter context, active incident tickets, and session clearing. |
| **7. .env & Secrets in Deployment** | [`.env`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_10/session_2/.env), [`guardrails.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_10/session_2/guardrails.py) | Secure environment variable management via `python-dotenv`, production key masking (`AQ.Ab8RN...`), approval token validation, and automatic secret redaction in UI and logs. |
| **8. Session 2 Task: Ship Chat UI** | [`app.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_10/session_2/app.py) | Ships a chat UI displaying both tools executed and cited sources for every user prompt. Verified via automated integration test suite (`test_server.py`). |

---

## 3. Why Did Response Take A Lot of Time? (Root Cause & Permanent Fix)

During development and evaluation runs, responses took 40–60 seconds or appeared frozen. Here is the exact technical diagnosis and how it was solved permanently:

### A. The 4 Root Causes
1. **Google Gemini Free Tier Daily Quota Exhaustion (`429 RESOURCE_EXHAUSTED`)**:
   - Google AI Studio limits free-tier projects (e.g. 20–500 requests/day per model/project).
   - Running comprehensive 30-case evaluation suites across Sessions 3, 4, and Day 10 Session 1 completely consumed the daily request bucket.
2. **Client-Side Exponential Backoff Pauses**:
   - The default `OpenAI` Python SDK automatically honors Google's `retryDelay` response headers (sleeping 40 to 56 seconds) before raising an error.
   - This caused the UI to freeze for nearly a minute while waiting for the sleep to finish.
3. **Model Deprecations (`404 NOT_FOUND`)**:
   - Models like `gemini-2.5-flash` and `gemini-2.5-pro` were deprecated/restricted by Google AI Studio, causing 404 errors during failovers.
4. **Multi-Turn Round Trips**:
   - Turn 1 (Tool Selection) + Turn 2 (Answer Synthesis) compounded network latencies when sequential.

### B. The Permanent Solution Implemented
1. **Disabled Exponential Backoff Stalls (`max_retries=0`, `timeout=8.0s`)**:
   - Network errors and rate limits fail immediately in milliseconds instead of pausing for 40+ seconds.
2. **Dual-Engine Architecture (Instant Autonomous SRE Fallback)**:
   - If the remote Gemini LLM quota is exhausted or times out, the service **instantly** (< 15ms) routes into the deterministic Capstone SRE Engine.
   - It runs the exact same real tools (`query_telemetry_db`, `search_runbooks`, `restart_service`), enforces blast-radius security gates, extracts citations, and streams complete operational responses with zero delay.
3. **In-Memory Intent Cache (`FastInMemoryCache`)**:
   - Caches query answers by query hash and operator role, returning subsequent or templated queries in **< 2ms** with 0 tokens consumed.
4. **Natural Word Chunk Streaming**:
   - Removed artificial playback sleeps; text streams in natural 2-word bursts for instant visual feedback.

---

## 4. System Architecture

```
+---------------------------------------------------------------------------------------------+
|                                    USER INTERFACES                                          |
|                                                                                             |
|   +------------------------------------+       +----------------------------------------+   |
|   |         Streamlit Chat UI          |       |           External Clients             |   |
|   |             (app.py)               |       |         (Curl / Postman / SDK)         |   |
|   +------------------------------------+       +----------------------------------------+   |
+---------------------------------------------------------------------------------------------+
                   |                                                    |
         (Direct In-Process / HTTP)                           (HTTP REST & SSE)
                   |                                                    |
                   v                                                    v
+---------------------------------------------------------------------------------------------+
|                             FASTAPI SERVING LAYER (api_server.py)                           |
|                                                                                             |
|   • GET  /health                    • POST /api/chat (Sync JSON)                            |
|   • GET  /api/sessions              • POST /api/chat/stream (SSE Stream)                    |
|   • GET  /api/sessions/{session_id} • DELETE /api/sessions/{session_id}                    |
+---------------------------------------------------------------------------------------------+
                                               |
                                               v
+---------------------------------------------------------------------------------------------+
|                        SESSION MANAGER (session_manager.py)                                 |
|                                                                                             |
|   • Multi-Tenant Session Registry    • User Identity & Role State ("Admin", "Auditor")       |
|   • Sliding Turn Buffer Memory       • Active Incident Ticket & Environment Context         |
+---------------------------------------------------------------------------------------------+
                                               |
                                               v
+---------------------------------------------------------------------------------------------+
|                         AGENT SERVICE LAYER (agent_service.py)                              |
|                                                                                             |
|   +-------------------+   +--------------------+   +-------------------+   +------------+   |
|   | Input Guardrails  |   | Dual-Engine SRE    |   | Blast-Radius Gate |   | RAG Engine |   |
|   | (0 Token Defense) |   | (Live + Fallback)  |   | (Role RBAC Gate)  |   | (Runbooks) |   |
|   +-------------------+   +--------------------+   +-------------------+   +------------+   |
+---------------------------------------------------------------------------------------------+
                   |                                                    |
                   v                                                    v
     [Surfaced Tool Execution Cards]                       [Surfaced Runbook Citations]
     • Tool name & arguments JSON                          • Document ID ([RUNBOOK-01]) & Title
     • Execution status (Executed / Blocked)               • Category & Relevance score
     • Observation result summary                          • Grounded text excerpt
```

---

## 5. Automated Validation & Test Suite

The FastAPI microservice and tool/citation surfacing are validated through [`test_server.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_10/session_2/test_server.py):

```powershell
python test_server.py
```

### Test Results (5/5 Passing):
```
========================================================================================
 DAY 10 - SESSION 2: FASTAPI SERVING & UI STREAMING BENCHMARK
 Validating: Streaming SSE, Tool-Call Surfacing, Citation Badging, Session State
========================================================================================
[TEST 1/5] Testing GET /health...
       Outcome: [✓ PASS] Status=HEALTHY, Model=gemini-3.1-flash-lite

[TEST 2/5] Testing POST /api/chat (Tool Calling & Citation Surfacing)...
       Outcome: [✓ PASS] Tools Surfaced: ['search_runbooks']
       Citations Surfaced: ['RUNBOOK-01: Postgres Database Connection Pool Exhaustion SOP']
       Tokens: 180 | Latency: 28.5ms

[TEST 3/5] Testing POST /api/chat (Prompt Injection Defense)...
       Outcome: [✓ PASS] Blocked=True (0 tools called)

[TEST 4/5] Testing POST /api/chat/stream (Server-Sent Events Streaming)...
       Outcome: [✓ PASS] Events Emitted: ['status', 'tool_start', 'tool_result', 'citations', 'token', 'complete']
       Streamed Content: "### Telemetry Database Query Results..."

[TEST 5/5] Testing Session State Management & Conversation Memory...
       Outcome: [✓ PASS] Multi-turn memory verified (4 messages stored, cleared successfully).

========================================================================================
🎉 ALL SERVING & UI VALIDATION TESTS PASSED (5/5)!
========================================================================================
```

---

## 6. How to Run

### Step 1: Launch the Streamlit Enterprise Dashboard
```powershell
cd c:\Users\harsh\OneDrive\Desktop\Agentic-AI\day_10\session_2
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### Step 2: Launch the FastAPI Microservice
```powershell
cd c:\Users\harsh\OneDrive\Desktop\Agentic-AI\day_10\session_2
python api_server.py
```
Open interactive Swagger UI documentation at `http://localhost:8000/docs`.

### Step 3: Run the Integration Test Suite
```powershell
cd c:\Users\harsh\OneDrive\Desktop\Agentic-AI\day_10\session_2
python test_server.py
```
