# Day 9 - Guardrails, Security & Agent Evaluation
## Session 3: Agent Evaluation & Benchmarking

This session establishes an automated, production-grade **30-Case Agent Evaluation Harness** designed to audit agent reasoning trajectories, tool-call precision, step efficiency, and final-answer accuracy, backed by a structured **Failure Taxonomy**.

---

## 1. What to Learn: Core Agent Evaluation Concepts

### 1.1 Task Success Rate
- Evaluates whether the end-to-end user goal was successfully achieved.
- In agent systems, **Task Success is NOT just text matching**; it requires both a **valid trajectory** (the agent performed authorized, appropriate actions) and an **accurate final response**.

### 1.2 Tool-Call Accuracy
- **Tool Selection Accuracy**: Did the agent select the correct tool(s) for the operational domain?
- **Argument Accuracy**: Were the parameters passed to the tool syntactically and semantically correct (e.g. `table="customers"` or `path="/etc/config.json"`)?
- **Forbidden Tool Avoidance**: Did the agent refrain from invoking unauthorized or destructive tools (e.g. `send_alert` when not asked)?

### 1.3 Step Count & Efficiency
- Unchecked agents can loop indefinitely or make redundant queries, wasting latency and tokens.
- Each test case enforces a `max_allowed_steps` threshold (typically 3 to 4 turns). Taking more turns than the optimal budget represents an efficiency regression.

### 1.4 Trajectory Evaluation vs. Final-Answer Evaluation

| Evaluation Paradigm | What is Checked | Why It Matters / Flaws |
| :--- | :--- | :--- |
| **Final-Answer Evaluation** | Checks only the final generated text (e.g., presence of keywords, BLEU, ROUGE). | **Severe Blindspot**: The agent might guess the right number via lucky hallucination while failing to query the database, or it might achieve the correct answer by taking a dangerous, unauthorized path (e.g., reading unauthorized secret files). |
| **Trajectory Evaluation** | Audits the entire sequence of intermediate steps: thoughts, tool selections, arguments, and execution order. | **Production Standard**: Proves *how* the agent solved the task. Confirms the agent gathered verified facts through authorized channels before synthesizing an answer. |

### 1.5 Regression Suites & Quality Gates
- Automated test suites act as a regression firewall in CI/CD pipelines.
- Whenever a system prompt, tool signature, or underlying LLM model is upgraded, the 30-case suite ensures no regression below the required quality threshold ($\ge 90\%$).

### 1.6 The 7-Class Failure Taxonomy

When an agent fails a task, our evaluation engine classifies the failure into a standardized root-cause bucket:

```
                              [ Agent Failure ]
                                      │
         ┌────────────────────────────┼───────────────────────────┐
         ▼                            ▼                           ▼
[ Trajectory Failures ]      [ Execution Budget ]       [ Synthesis Failures ]
 • WRONG_TOOL_SELECTION       • STEP_LIMIT_EXCEEDED      • INACCURATE_FINAL_ANSWER
 • FORBIDDEN_TOOL_VIOLATION   • PREMATURE_TERMINATION
 • ARGUMENT_MALFORMED_ERROR
 • TRAJECTORY_ORDERING_ERROR
```

1. **`WRONG_TOOL_SELECTION`**: Failed to invoke the required tool, or invoked an irrelevant tool.
2. **`FORBIDDEN_TOOL_VIOLATION`**: Invoked a tool specifically prohibited for the task (e.g., dispatching alerts on read-only queries).
3. **`ARGUMENT_MALFORMED_ERROR`**: Tool selection was correct, but parameters were invalid or missing.
4. **`TRAJECTORY_ORDERING_ERROR`**: Tools were executed out of required logical sequence (e.g., calculating before querying data).
5. **`STEP_LIMIT_EXCEEDED`**: Agent exceeded maximum allowed turn budget (caught in loops or redundant calls).
6. **`INACCURATE_FINAL_ANSWER`**: Trajectory was valid, but final text synthesis omitted ground-truth facts.
7. **`PREMATURE_TERMINATION`**: Model exited prematurely without taking necessary actions.

---

## 2. The 30-Case Test Suite Matrix

The suite covers 6 enterprise operational domains (5 cases per domain = 30 cases):

| Domain | Case Range | Operational Focus | Key Tools Tested |
| :--- | :--- | :--- | :--- |
| **1. Database & SQL Analytics** | `TC-01` to `TC-05` | Customer tier queries, order lookups, inventory counts, churn filters. | `query_database` |
| **2. Knowledge Base & RAG** | `TC-06` to `TC-10` | JWT rotation policy, Sev-1 on-call SLA, rate limits, SLA tiers, data retention. | `search_docs` |
| **3. Math & Metric Computations** | `TC-11` to `TC-15` | ARR multiplication, gross profit margins, order sums, inventory valuation, uptime SLA %. | `calculate` |
| **4. Filesystem & Log Diagnostics**| `TC-16` to `TC-20` | Server JSON configs, syslog connection pool errors, k8s replicas, auth logs, directory listings. | `read_file`, `list_dir` |
| **5. Multi-Step Workflows** | `TC-21` to `TC-25` | Chained inventory lookup $\rightarrow$ cost calculation; database lookup $\rightarrow$ conditional alert; log scan $\rightarrow$ incident bridge alert. | `query_database`, `read_file`, `calculate`, `send_alert` |
| **6. Edge Cases & Boundaries** | `TC-26` to `TC-30` | Non-existent customer IDs, missing files, division by zero, zero-match searches, arithmetic without tool leakage. | Boundary handling & error resilience |

---

## 3. Evaluation Architecture

```
                       [ TestCase (Prompt + Contract) ]
                                      │
                                      ▼
                             [ EvaluatedAgent ]
                                      │
                  ┌───────────────────┴───────────────────┐
                  ▼                                       ▼
       [ Intermediate Trajectory ]               [ Final Output Text ]
        • Tool calls executed                     • Synthesized answer
        • Arguments passed
        • Step count taken
                  │                                       │
                  └───────────────────┬───────────────────┘
                                      ▼
                            [ AgentEvaluator ]
                                      │
          ┌───────────────────────────┴───────────────────────────┐
          ▼                                                       ▼
[ Trajectory Audit ]                                     [ Final Answer Audit ]
 • Tool Selection Check                                   • Keyword & Fact Check
 • Argument Matching Check                                • Hallucination Filter
 • Prerequisite Ordering Check
 • Step Budget Cap Check
          │                                                       │
          └───────────────────────────┬───────────────────────────┘
                                      ▼
                        [ Task Success Evaluation ]
                                      │
                                      ├─► PASS: Trajectory OK AND Answer OK
                                      │
                                      └─► FAIL: Map to Failure Taxonomy
```

---

## 4. Empirical Benchmark Results

Running the automated 30-case evaluation suite via [`main.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_09/session_3/main.py) yielded the following metrics:

### 4.1 Executive Evaluation Metrics
- **Total Test Cases Evaluated**: 30
- **Overall Task Success Rate**: 30/30 (**100.0%**)
- **Trajectory Pass Rate**: 30/30 (**100.0%**)
- **Final-Answer Pass Rate**: 30/30 (**100.0%**)
- **Average Steps / Turns Taken**: **2.17 turns per task** (Optimal step efficiency)

### 4.2 Category Performance Breakdown

| Category Domain | Total Cases | Passed | Failed | Success Rate | Key Validated Behaviors |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Database_Analytics** | 5 | 5 | 0 | **100.0%** | Accurate table targeting (`customers`, `orders`, `inventory`), row filtering. |
| **Knowledge_RAG** | 5 | 5 | 0 | **100.0%** | Strict factual retrieval across JWT SOP, on-call SLAs, rate limits. |
| **Math_Computations** | 5 | 5 | 0 | **100.0%** | Formula evaluation for ARR, margins, sums, inventory batch values, uptime %. |
| **Filesystem_Diagnostics** | 5 | 5 | 0 | **100.0%** | Accurate virtual JSON parsing, syslog error isolation, directory listing. |
| **Multi_Step** | 5 | 5 | 0 | **100.0%** | Chained dependencies: lookups $\rightarrow$ calculations, log scans $\rightarrow$ conditional alerts. |
| **Edge_Cases** | 5 | 5 | 0 | **100.0%** | Non-existent records, missing files, division by zero, zero-match search, arithmetic without alerts. |

### 4.3 Failure Taxonomy Analysis
- **Total Failures**: 0 out of 30 cases (0.0% error rate).
- **Classification Taxonomy**:
  * `WRONG_TOOL_SELECTION`: 0
  * `FORBIDDEN_TOOL_VIOLATION`: 0
  * `ARGUMENT_MALFORMED_ERROR`: 0
  * `TRAJECTORY_ORDERING_ERROR`: 0
  * `STEP_LIMIT_EXCEEDED`: 0
  * `INACCURATE_FINAL_ANSWER`: 0
  * `PREMATURE_TERMINATION`: 0

---

## 5. File Manifest

- [`test_cases.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_09/session_3/test_cases.py): Complete 30-case evaluation specification spanning 6 operational domains.
- [`tools.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_09/session_3/tools.py): Enterprise tools (Database, Docs, Math, Filesystem, Alerting).
- [`agent.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_09/session_3/agent.py): Evaluated Agent with trajectory recording and rate-limit backoff handling.
- [`evaluator.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_09/session_3/evaluator.py): Evaluation Engine with trajectory auditing, final-answer scoring, and failure taxonomy classification.
- [`main.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_09/session_3/main.py): Automated test runner printing scorecard, aggregate metrics, category breakdowns, and failure taxonomy distributions.

---

## 6. How to Run

```bash
cd day_09/session_3
python main.py
```
