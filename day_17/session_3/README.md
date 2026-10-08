# Day 17 - Session 3: First Real Iteration

## 📌 Syllabus & Session Objectives
- **Session:** Day 17 - Session 3: First Real Iteration
- **Topic:** Build Sprint 1 — Hypothesis-Driven Iterative Engineering
- **What to Learn:** Adding only what the eval set proves is needed: retrieval improvement, a tool, routing. One change at a time, each scored.
- **Task:** A measured improvement over the baseline, logged with the reason it worked.
- **Resources:** Intern (Harsh Ramesh Nerkar).

---

## 🔬 Scientific Methodology: One Change at a Time

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

### 1. Step 1: +Enhanced Retrieval (Hybrid BM25 + Dense RRF)
- **Change:** Added Reciprocal Rank Fusion over lexical and service-conditioned dense runbook tokens.
- **Result:** **30.0% Pass Rate** (0.0% delta).
- **Reason:** Static runbooks contain policy knowledge, but cannot provide ephemeral pod exit codes or live Prometheus metrics. *More search cannot invent missing cluster telemetry.*

### 2. Step 2: +Cluster Telemetry Diagnostic Tool
- **Change:** Added targeted live cluster inspection tool (`query_live_telemetry`) supplying real-time pod exit codes, memory graphs, commit SHAs, and fatal log stack traces.
- **Result:** **100.0% Pass Rate** (**+70.0% massive delta**).
- **Reason:** Real-time cluster facts bridged the ephemeral gap, allowing the diagnostic synthesizer to identify root causes with 100% precision.

### 3. Step 3: +Conditional Intent Routing
- **Change:** Added sub-5ms `IntentRouter` routing static policy queries directly to fast-path Hybrid RAG (sub-250ms) and live outages to the deep-path cluster tool.
- **Result:** **100.0% Pass Rate**, with **13.7% latency reduction** (883.7ms -> 762.8ms) and reduced cluster API load.
- **Reason:** Prevented running expensive cluster inspections on documentation queries.

---

## 📂 Deliverables & File Directory

- [ITERATION_LOG.md](ITERATION_LOG.md): Comprehensive scientific log of the 3 iterations, hypotheses, scores, and causal analysis.
- [ITERATION_SCORECARD.json](ITERATION_SCORECARD.json): Recorded empirical scorecard JSON across all 4 steps.
- [eval_dataset.json](eval_dataset.json): Golden 20-case evaluation dataset.
- [static_runbooks.json](static_runbooks.json): Static enterprise runbooks knowledge base.
- [first_iteration_engine.py](first_iteration_engine.py): Step-by-step iterative benchmarking engine.
- [main.py](main.py): Interactive CLI supporting `--benchmark` and `--inspect-route <incident_id>`.
- [test_iteration.py](test_iteration.py): Integration test suite verifying progression, router accuracy, and performance gains.
- [requirements.txt](requirements.txt): Environment configuration.

---

## 🚀 Execution & Verification

### 1. Run Full Benchmark Across All Steps
```bash
python day_17/session_3/main.py --benchmark
```

### 2. Inspect Intent Router Path for Incident or Runbook
```bash
python day_17/session_3/main.py --inspect-route INC-101
python day_17/session_3/main.py --inspect-route INC-102
```

### 3. Run Test Suite
```bash
python day_17/session_3/test_iteration.py
```
*Expected: 3 tests passing in ~1.0 second with 100% assertions satisfied.*
