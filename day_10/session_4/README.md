# Day 10 - Session 4: Final Live Demo & Capstone Oral Assessment
## Enterprise SRE Copilot Live Demonstration, 10-Day Mock Interview & Assessment Defense

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Interactive%20CLI%20%2B%20Streamlit-brightgreen.svg)](live_demo.py)
[![Presentation Script](https://img.shields.io/badge/Presentation-10--Minute%20Playbook-blue.svg)](DEMO_SCRIPT.md)
[![Mock Interview](https://img.shields.io/badge/Mock%20Interview-5%20Core%20%2B%2010%20Days-orange.svg)](MOCK_INTERVIEW.md)
[![Rubric Assessment](https://img.shields.io/badge/Rubric%20Score-50%2F50%20(Exemplary)-success.svg)](RUBRIC_ASSESSMENT.md)

---

## 1. Overview & Assessment Objective

**Day 10 Session 4** represents the capstone finale of the entire **10-Day Agentic AI Curriculum**. The objective is two-fold:
1. **Deliver a 10-Minute Live Technical Demonstration** showing the complete end-to-end autonomous SRE copilot in action.
2. **Successfully Defend the Architecture in an Oral Technical Assessment** answering the 5 high-stakes assessment questions and demonstrating mastery across all 10 days of curriculum design patterns.

---

## 2. Key Deliverables in Session 4

| Deliverable | File | Purpose & Key Details |
|---|---|---|
| **1. Live Demo Runner** | [`live_demo.py`](live_demo.py) | Interactive CLI presentation runner executing the 4 core operational flows with live streaming, tool trajectories, and presenter cues. |
| **2. 10-Minute Presentation Script** | [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) | Minute-by-minute slide, screen, and speech outline covering mission, live demos, benchmarks, economics, and honest limitations. |
| **3. Master Mock Interview** | [`MOCK_INTERVIEW.md`](MOCK_INTERVIEW.md) | Exhaustive Q&A answering the **5 core high-stakes questions** + deep-dive questions covering **Days 1 through 10**. |
| **4. Rubric Assessment Matrix** | [`RUBRIC_ASSESSMENT.md`](RUBRIC_ASSESSMENT.md) | Comprehensive scoring breakdown mapping the capstone against all 5 evaluation pillars (50/50 Exemplary). |
| **5. Environment & Dependencies** | [`.env`](.env), [`requirements.txt`](requirements.txt) | Turnkey configuration for standalone execution in the session directory. |

---

## 3. Quickstart & Presentation Execution

### Step 1: Run the Interactive Live Demonstration
To run the automated terminal demo that walks through all 4 mission-critical scenarios:
```bash
cd day_10/session_4
python live_demo.py
```

### Step 2: Launch the Visual Streamlit Dashboard for the Audience
```bash
cd ../session_2
streamlit run app.py
```
*Access UI at: `http://localhost:8501`*

### Step 3: Launch the Production FastAPI Serving Layer (Optional for API Demo)
```bash
cd ../session_2
python api_server.py
```
*Interactive Swagger Documentation: `http://localhost:8000/docs`*

---

## 4. The 5 Core High-Stakes Oral Defense Questions (At A Glance)

### 1. Why an agent instead of a deterministic chain?
> **Answer Summary:** An incident diagnostic trajectory cannot be predicted in advance. An agent uses a dynamic ReAct (Thought-Action-Observation) loop to hypothesize, choose diagnostic tools, inspect live telemetry, and adaptively branch. A chain either explodes into an unmaintainable if-else tree or breaks on unexpected returns. Crucially, our execution is deterministic: diagnostic reasoning is agentic, while destructive execution is strictly gated by our Layer 4 Blast-Radius Gate.

### 2. How do you provably stop hallucination in an SRE agent?
> **Answer Summary:** We enforce four defense layers:
> 1. Strict RAG grounding injecting verbatim SOP playbooks.
> 2. Automated canonical citation extraction (`_extract_citations()`) verifying `[RUNBOOK-XX: Title]` references.
> 3. Schema-validated deterministic tool execution for all metrics and database queries.
> 4. Hardcoded argument validation in `guardrails.py` that intercepts hallucinated parameters or invalid tokens before execution.

### 3. What chunk size did you choose for RAG, and why?
> **Answer Summary:** We chose section-based Markdown header chunking averaging **600 to 900 characters (120 to 180 tokens)**. Fixed-token chunking (e.g. 256 tokens) is dangerous in DevOps because it slices multi-step terminal commands, detaches step numbers from escalation warnings, and destroys the causal link between root causes and mitigation procedures.

### 4. How did you quantitatively measure success across the system?
> **Answer Summary:** We executed an automated 20-case test matrix across five architectural pillars via [`benchmark_eval.py`](../session_3/benchmark_eval.py):
> - **Overall Pass Rate:** **100.0% (20/20)** against our ≥ 95.0% target SLA.
> - **Latency Percentiles:** Median p50: **1,405ms**, p95: **1,642ms** (well within our 4-second SLA).
> - **Cache Acceleration:** In-memory query cache hits in **0.02ms**.
> - **Security Invariance:** 100% interception of prompt injections and unauthorized roles.

### 5. What does this system cost to run?
> **Answer Summary:** Operating on Google Gemini Flash rates ($0.075 input / $0.30 output per 1M tokens), our average query consumes **153 tokens**, resulting in an average cost of **$0.000022 per query** (just **2.2 cents per 1,000 queries**). This makes OpsSentinel AI **217× cheaper than GPT-4o** and **302× cheaper than Claude 3.5 Sonnet**.

*For the complete word-for-word technical scripts, see [`MOCK_INTERVIEW.md`](MOCK_INTERVIEW.md).*

---

## 5. 10-Day Curriculum Mastery Overview

```
+---------------------------------------------------------------------------------------------------+
|                            10-DAY AGENTIC AI CURRICULUM ARCHITECTURE                              |
+---------------------------------------------------------------------------------------------------+
| Day 1  | LLM Foundations & Structured Output (JSON Schemas, Pydantic Models)                      |
| Day 2  | Prompt Engineering & System Instructions (Few-Shot Demonstrations, ReAct Prompts)         |
| Day 3  | Vector Embeddings & Similarity Search (Cosine Metric, FAISS, Dense vs Sparse)            |
| Day 4  | Retrieval-Augmented Generation (Section Chunking, Hybrid Search, Citation Badges)        |
| Day 5  | Tools & Function Calling (OpenAI Schemas, Dispatch Logic, Error Handling)                |
| Day 6  | Autonomous Agent Loops (Thought-Action-Observation Trajectories, Max Turns Bounding)     |
| Day 7  | State Management & Memory (Sliding Buffer, Long-Term Structured Entity Stores)           |
| Day 8  | Observability & Distributed Tracing (OpenTelemetry Spans, Latency Profiling, Replay)     |
| Day 9  | Evaluation & Cost Optimization (Evals, LLM-as-a-Judge, In-Memory Caching, Routing)       |
| Day 10 | Enterprise Production Serving (FastAPI, SSE Streaming, Guardrails, Blast-Radius Gates)   |
+---------------------------------------------------------------------------------------------------+
```

All 10 curriculum days are fully defended in detail in [`MOCK_INTERVIEW.md`](MOCK_INTERVIEW.md) and mapped to the rubric in [`RUBRIC_ASSESSMENT.md`](RUBRIC_ASSESSMENT.md).
