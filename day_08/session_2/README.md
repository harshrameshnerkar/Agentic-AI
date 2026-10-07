# Day 8 — Session 2: When NOT to Use Agents

This session explores one of the most critical engineering principles in AI systems design: **recognizing when an agent is the wrong tool for the job**. We demonstrate empirically why deterministic pipelines consistently outperform autonomous agents on known tasks, and how the **Single-Agent-with-Good-Tools** baseline should be your primary benchmark.

---

## 1. Executive Summary: The Agent vs. Pipeline Dichotomy

| Dimension | Fixed Deterministic Pipeline | Autonomous ReAct Agent |
| :--- | :--- | :--- |
| **Control Flow** | Explicit, statically typed code graph ($A \to B \to C$) | Dynamic, stochastic tool-calling loop (Model decides turn-by-turn) |
| **Arithmetic Precision** | **100% exact** (Standard IEEE 754 math in CPU) | Prone to rounding errors, hallucinated totals, or tool argument drift |
| **Data Processing Latency** | **Sub-millisecond (< 1 ms)** in Python | Multiplies with each LLM round-trip ($15\text{s} - 45\text{s}$) |
| **Token Consumption** | **Linear / Minimal**: Only payload needed for synthesis | **Quadratic ($O(N^2)$)**: Full conversation history re-sent every turn |
| **Operational Cost** | **$10\times - 30\times$ cheaper** | High token expenditure on intermediate thought tokens and tool schemas |
| **Debuggability** | **Trivial**: Standard stack traces, deterministic unit tests | **Difficult**: Non-deterministic branching, prompt sensitivity |
| **Best Used For** | Predictable workflows, calculations, data ETL, reports | Open-ended exploration, unknown step sequences, dynamic triage |

---

## 2. The Benchmark Task: Multi-Currency FinOps Spend Audit

Both approaches were tasked with the identical problem:
1. Ingest raw multi-currency monthly cloud invoice items (AWS, Snowflake, GCP, Datadog, Cloudflare in USD, EUR, GBP).
2. Normalize foreign currencies to USD using exchange rates (EUR $\to$ 1.08, GBP $\to$ 1.28).
3. Compute exact gross spend across all services (Ground Truth: **$59,956.00**).
4. Identify Top 3 spend drivers and any budget anomalies exceeding allocated monthly thresholds by $>15\%$.
5. Produce an Executive Summary Briefing with key takeaways and recommendations.

### Architectural Approaches Compared:

1. **Fixed Deterministic Pipeline** ([`fixed_pipeline.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_08/session_2/fixed_pipeline.py)):
   - **Step 1 (Python Code)**: Currency normalization, math summation, sorting, anomaly filtering ($0.0003\text{s}$).
   - **Step 2 (Single Targeted LLM Call)**: Generates executive narrative from exact pre-calculated metrics ($2.5\text{s}$).
   - Total LLM Calls: **1 call**.

2. **Autonomous ReAct Agent** ([`agent_solution.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_08/session_2/agent_solution.py)):
   - Loops through multiple turns calling `tool_get_invoices`, `tool_convert_currency`, `tool_calculate`, `tool_check_budget_anomaly`.
   - Total LLM Calls: **3 to 5 calls**.

---

## 3. The "Single-Agent-with-Good-Tools" Baseline

Before building complex multi-agent swarms or autonomous loops, engineers must apply the **Pragmatic Baseline Test**:

```
                       ┌───────────────────────────────┐
                       │  Can the sequence of steps    │
                       │     be known in advance?      │
                       └───────────────┬───────────────┘
                                       │
                      ┌────────────────┴────────────────┐
                      ▼ YES                             ▼ NO
        ┌───────────────────────────────┐ ┌───────────────────────────────┐
        │    DO NOT USE AN AGENT!       │ │      Is the task deeply       │
        │ Use a Deterministic Pipeline  │ │  multimodal or non-linear?    │
        │   + Single LLM for Synthesis  │ └───────────────┬───────────────┘
        └───────────────────────────────┘                 │
                                         ┌────────────────┴────────────────┐
                                         ▼ YES                             ▼ NO
                           ┌───────────────────────────────┐ ┌───────────────────────────────┐
                           │   Use Single Agent with       │ │      Use Multi-Agent Swarm    │
                           │   High-Leverage Tools         │ │   (Only when isolation and    │
                           │ (The Gold Standard Baseline)  │ │    independent roles demand)  │
                           └───────────────────────────────┘ └───────────────────────────────┘
```

---

## 4. File Index

- [`fixed_pipeline.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_08/session_2/fixed_pipeline.py): Deterministic Python engine + single LLM synthesis step.
- [`agent_solution.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_08/session_2/agent_solution.py): Autonomous ReAct agent with fine-grained calculator and currency tools.
- [`data.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_08/session_2/data.py): Multi-currency invoice dataset and mathematical ground truth.
- [`benchmark.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_08/session_2/benchmark.py): Side-by-side comparative benchmarking engine.
- [`main.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_08/session_2/main.py): Master test runner and empirical analysis script.

---

## 5. Execution

Run the comparative benchmark:

```bash
.venv\Scripts\python.exe day_08\session_2\main.py
```
