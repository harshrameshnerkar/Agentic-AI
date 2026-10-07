# Day 14 - Session 2: Evaluation at Scale

## Overview

A 20-example evaluation suite is sufficient for rapid pre-commit sanity checks, but **production agent evaluation at scale** demands a statistically rigorous framework. If an evaluation suite only tests simple queries, an agent can achieve a deceptive 98% pass rate while failing in critical operational categories (such as database deadlocks or destructive cluster mutations).

This module implements a production-grade **Evaluation at Scale** system:
1. **Trace Mining & Stratification**: Expanding the golden dataset to **100 curated cases mined from real production telemetry**, stratified across 5 critical query types.
2. **Inter-Rater Reliability (Cohen's Kappa $\kappa$)**: Quantifying human-human and human-LLM judge agreement to ensure grading rubrics are noise-free.
3. **Judge Calibration Drift**: Monitoring automated LLM evaluators over time to detect **leniency drift** (overly generous scores) and **harshness drift**, with mathematical recalibration.
4. **Online vs. Offline Evaluation & Production A/B Testing**: Measuring real-world impact across 1,000 live sessions using two-proportion $z$-tests on MTTR, human escalation rates, and undo actions.

---

## Architecture & Stratification Matrix

```
                      Raw Production Telemetry Traces
                      (User Sessions, Alerts, Errors)
                                     │
                                     ▼
                      ┌─────────────────────────────┐
                      │    Production Trace Miner   │
                      │  - Deduplication & Filter   │
                      │  - Escalation Ticket Mining │
                      └──────────────┬──────────────┘
                                     │
                                     ▼
                ┌─────────────────────────────────────────┐
                │   100-Case Stratified Golden Benchmark  │
                ├─────────────────────────────┬───────────┤
                │ 1. INFRA_DIAGNOSTIC         │ 25 Cases  │
                │ 2. DESTRUCTIVE_REMEDIATION  │ 25 Cases  │
                │ 3. DATABASE_STORAGE         │ 20 Cases  │
                │ 4. NETWORK_INGRESS          │ 15 Cases  │
                │ 5. SECURITY_ADVERSARIAL     │ 15 Cases  │
                └─────────────────────────────┴───────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         ▼                           ▼                           ▼
┌──────────────────┐       ┌──────────────────┐        ┌──────────────────┐
│ Inter-Rater Rel. │       │ Judge Drift Mon. │        │ Online A/B Test  │
│  Cohen's Kappa   │       │  Z-Score Recal.  │        │  Two-Sample Z    │
│   (κ >= 0.80)    │       │ (Δ <= ±0.05)     │        │  (p < 0.05 MTTR) │
└──────────────────┘       └──────────────────┘        └──────────────────┘
```

---

## Core Components

| Component | File | Description |
| :--- | :--- | :--- |
| **Stratified Dataset Models** | [`stratified_dataset.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_14/session_2/stratified_dataset.py) | Defines `StratifiedTestCase`, schema serialization, and stratum registry. |
| **Trace Miner** | [`trace_miner.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_14/session_2/trace_miner.py) | Generates exactly 100 cases mined from telemetry traces, stratified across 5 operational categories. |
| **Inter-Rater Engine** | [`inter_rater_agreement.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_14/session_2/inter_rater_agreement.py) | Calculates Observed Agreement ($P_o$), Expected Agreement by Chance ($P_e$), Cohen's Kappa ($\kappa$), and confusion matrices. |
| **Judge Drift Detector** | [`judge_calibration_drift.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_14/session_2/judge_calibration_drift.py) | Detects leniency and harshness distribution shifts against frozen benchmarks and computes recalibration scaling factors. |
| **A/B Testing Engine** | [`ab_testing_framework.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_14/session_2/ab_testing_framework.py) | Simulates online traffic splits (1,000 sessions), tracking MTTR, human escalations, and computing two-proportion $z$-scores. |
| **Stratified Eval Runner** | [`eval_runner.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_14/session_2/eval_runner.py) | Executes batch evaluations over all 100 test cases and outputs per-stratum scorecards. |
| **Master CLI** | [`main.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_14/session_2/main.py) | Interactive CLI runner for all 5 evaluation modules. |
| **Test Suite** | [`test_session_2.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_14/session_2/test_session_2.py) | Automated test suite validating dataset quotas, Cohen's Kappa, drift detection, and A/B hypothesis tests. |

---

## Verification & Execution Guide

### 1. Mine and Export 100 Stratified Test Cases
Generates the benchmark from traces, validates quotas, and exports `golden_dataset_100.json`:
```powershell
.venv\Scripts\python.exe day_14\session_2\main.py --mine-dataset
```

### 2. Run Batch Evaluation Across 100 Cases
Evaluates the production agent against all 100 test cases and renders a per-stratum scorecard:
```powershell
.venv\Scripts\python.exe day_14\session_2\main.py --eval-100
```

### 3. Compute Inter-Rater Agreement & Cohen's Kappa
Measures statistical alignment between Human SRE consensus and LLM Judge (Claude 3.5 Sonnet):
```powershell
.venv\Scripts\python.exe day_14\session_2\main.py --check-inter-rater
```

### 4. Audit Judge Calibration Drift
Monitors LLM evaluator score stability across sprints and computes recalibration factors:
```powershell
.venv\Scripts\python.exe day_14\session_2\main.py --audit-drift
```

### 5. Run Online Production A/B Experiment
Simulates 1,000 live production requests split 50/50 between Baseline and Candidate prompts, testing for statistical significance on MTTR and human escalation rate:
```powershell
.venv\Scripts\python.exe day_14\session_2\main.py --simulate-ab-test
```

### 6. Run Automated Test Suite
Executes all unit and integration tests:
```powershell
.venv\Scripts\python.exe day_14\session_2\test_session_2.py
```
