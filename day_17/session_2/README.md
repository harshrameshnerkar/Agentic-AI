# Day 17 - Session 2: Simplest Thing That Works

## 📌 Syllabus & Session Objectives
- **Session:** Day 17 - Session 2: Simplest Thing That Works
- **Topic:** Build Sprint 1 — Establishing the Non-Agent Baseline
- **What to Learn:** A plain prompt or single retrieval call as the baseline, scored against the eval set. Resisting the pull to build an agent before proving a chain is insufficient.
- **Task:** A baseline scored on the eval set, with the score recorded.
- **Resources:** Intern (Harsh Ramesh Nerkar).

---

## 🎯 Engineering Principle: Resisting Premature Complexity

> *"Before building an autonomous multi-step agent loop, you MUST prove that simpler architectures cannot solve the problem.*  
> *Start with a plain prompt. If that fails, test a single retrieval call (Vanilla RAG).*  
> *Only when your evaluation set proves a hard ceiling should you add tools, routing, or agentic control."*

In this session, we built and benchmarked:
1. **Baseline 1 — Plain Prompt (Zero-Shot Completion):** Direct LLM inference relying solely on pre-training weights.
2. **Baseline 2 — Single Retrieval Call (Vanilla RAG):** Single-step document retrieval from enterprise runbooks appended to the prompt context.

Both baselines were evaluated against a golden 20-case enterprise incident evaluation dataset (`eval_dataset.json`).

---

## 📊 Recorded Baseline Scorecard

```
================================================================================
                    EMPIRICAL BASELINE SCORECARD
================================================================================
EVALUATION METRIC                    | PLAIN PROMPT       | SINGLE RETRIEVAL RAG
--------------------------------------------------------------------------------
Overall Pass Rate                    |              0.0%  |               30.0%
Static Runbook Pass Rate (6 Cases)   |              0.0%  |              100.0%
Dynamic Incident Pass Rate (14 Cases)|              0.0%  |                0.0%
Key Indicator Recall                 |              3.8%  |               30.0%
Generic Guess / Hallucination Rate   |            100.0%  |               50.0%
Mean Latency (ms)                    |            120.0ms |              280.2ms
Cost per Query ($)                   | $       0.000045   | $         0.000115
================================================================================
```

### Key Findings & Failure Analysis:
- **Baseline 1 (Plain Prompt) fails 100% of cases (0.0% pass rate):** Zero-shot LLMs produce plausible-sounding generic advice (*"Restart the pod"*, *"Check your network"*), completely missing exact enterprise compliance rules and root causes.
- **Baseline 2 (Vanilla RAG) solves 100% of static runbooks (30.0% overall pass rate):** Single-document retrieval succeeds on all 6 static operational queries (e.g. Vault root token rotation, S3 lifecycle, Twilio retry policy).
- **The Ephemeral Gap (0% on live incidents):** Vanilla RAG fails on all 14 dynamic incidents. The root cause for a live crash (`OutOfMemoryError ExitCode 137`, `poison pill Kafka message`, `missing ConfigMap secret`) exists in **ephemeral cluster state**, NOT static documentation.

**Conclusion:** We have empirically proved that an **agentic, tool-augmented chain** is required for Session 3.

---

## 📂 Deliverables & File Directory

- [BASELINE_SCORE_REPORT.md](BASELINE_SCORE_REPORT.md): Comprehensive analysis of baseline scores, failure modes, and architectural justification.
- [BASELINE_SCORES.json](BASELINE_SCORES.json): Recorded JSON scorecard with full per-incident evaluation results.
- [eval_dataset.json](eval_dataset.json): 20-case golden evaluation dataset (6 static runbook queries, 14 live cluster incidents).
- [static_runbooks.json](static_runbooks.json): Enterprise static runbook knowledge base for vanilla RAG retrieval.
- [baseline_runner.py](baseline_runner.py): Execution engine for Baseline 1 (Plain Prompt) and Baseline 2 (Single Retrieval RAG).
- [main.py](main.py): Interactive CLI supporting `--summary`, `--eval`, and `--inspect <incident_id>`.
- [test_baseline.py](test_baseline.py): 4 integration tests validating dataset integrity, retriever accuracy, and scoring correctness.
- [requirements.txt](requirements.txt): Environment configuration.

---

## 🚀 Execution & Verification

### 1. View Summary Scorecard
```bash
python day_17/session_2/main.py --summary
```

### 2. Re-run Live Evaluation Across 20 Golden Cases
```bash
python day_17/session_2/main.py --eval
```

### 3. Inspect a Specific Incident Ground Truth & Telemetry
```bash
python day_17/session_2/main.py --inspect INC-101
```

### 4. Run Integration Test Suite
```bash
python day_17/session_2/test_baseline.py
```
*Expected: 4 tests passing in < 0.05 seconds with 100% assertions satisfied.*
