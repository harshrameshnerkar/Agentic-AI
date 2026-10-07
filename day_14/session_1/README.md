# Day 14 - Session 1: Regression Suites & CI Quality Gates

## Overview

In traditional software engineering, code changes are validated by unit and integration tests. In Agentic AI and LLMOps, **prompts, model configurations, and tool schemas ARE code**. A subtle change to a system prompt (e.g. attempting to shorten outputs or reduce latency) can silently cause catastrophic regressions:
1. **Schema Drift**: Dropping required JSON keys expected by backend parsers.
2. **Tool Selection Regression**: Inadvertently proposing the wrong tool or omitting vital parameters.
3. **Safety Gate Bypass**: Bypassing human approval requirements on high-blast destructive operations (e.g. dropping tables or restarting active clusters).
4. **Accuracy Drop**: Hallucinating or failing edge cases that previously passed.

This module implements a production **LLMOps CI Regression Gate** wired into CI/CD that blocks pull requests if any quality, safety, or accuracy regressions are detected.

---

## Architecture Flow

```
                      Pull Request (PR) Opened
                (Prompt / Model Configuration Change)
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │   GitHub Actions CI   │
                     └───────────┬───────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
       ┌──────────────────┐            ┌──────────────────┐
       │ Frozen Baseline  │            │ Candidate PR     │
       │ Prompt (v1.0.0)  │            │ Prompt (v1.1.0)  │
       └────────┬─────────┘            └────────┬─────────┘
                │                               │
                └───────────────┬───────────────┘
                                │
                                ▼
               ┌─────────────────────────────────┐
               │   Golden Evaluation Suite (20)  │
               │   - Diagnostic Cases            │
               │   - Destructive Action Gates    │
               │   - Adversarial Injections      │
               └────────────────┬────────────────┘
                                │
                                ▼
               ┌─────────────────────────────────┐
               │    CI Quality & Safety Gate     │
               │   - Pass Rate >= 90%            │
               │   - Delta vs Base >= 0%         │
               │   - Safety Compliance = 100%    │
               │   - Schema Validity >= 95%      │
               └────────────────┬────────────────┘
                                │
                  ┌─────────────┴─────────────┐
                  ▼                           ▼
            [GATES MET]                [REGRESSION DETECTED]
                  │                           │
                  ▼                           ▼
          🟢 Exit Code 0              🔴 Exit Code 1
          Build Succeeded             Build Blocked
          Merge Allowed               PR Blocked with Diff
```

---

## Core Components

| Component | File | Description |
| :--- | :--- | :--- |
| **Prompt Registry** | [`prompt_registry.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_14/session_1/prompt_registry.py) | Semantic versioning for prompts (`PromptVersion`), author metadata, commit SHA, and model configs. |
| **Golden Benchmark** | [`golden_dataset.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_14/session_1/golden_dataset.py) | 20 curated SRE test cases with ground-truth targets, tools, and mandatory approval flags. |
| **Agent Evaluator** | [`agent_evaluator.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_14/session_1/agent_evaluator.py) | Evaluates prompt outputs against schema, tool accuracy, safety gates, and confidence thresholds. |
| **Eval Harness** | [`eval_harness.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_14/session_1/eval_harness.py) | Aggregates pass rates, latencies (p50, p95), and compiles GitHub-flavored Markdown job summaries. |
| **CI Gatekeeper** | [`ci_gate.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_14/session_1/ci_gate.py) | Enforces strict zero-regression and 100% safety rules. Exits with `0` (pass) or `1` (blocked). |
| **Canary & Shadow** | [`canary_shadow.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_14/session_1/canary_shadow.py) | Dark traffic mirroring (Shadow mode) and progressive traffic shifting with automated rollback watchdog. |
| **GitHub Actions** | [`.github/workflows/llm_eval_ci.yml`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/.github/workflows/llm_eval_ci.yml) | Production CI workflow posting evaluation scorecard to GitHub Job Summary. |

---

## Verification & Execution Guide

### 1. Run Baseline Evaluation (Build Passes)
Runs the stable `v1.0.0` prompt against the golden suite. Meets all criteria (100% pass, 100% safety):
```powershell
.venv\Scripts\python.exe day_14\session_1\main.py --run-baseline
```

### 2. Run Candidate Evaluation (Build Blocked)
Simulates a PR introducing a flawed candidate prompt (`v1.1.0-regressed`). The CI gate detects schema drift and safety violations, exiting with code `1` and blocking the merge:
```powershell
.venv\Scripts\python.exe day_14\session_1\main.py --run-candidate
```

### 3. Run Dark Traffic Shadow Mirroring
Demonstrates background dark traffic mirroring comparing candidate responses against baseline without impacting end users:
```powershell
.venv\Scripts\python.exe day_14\session_1\main.py --simulate-shadow
```

### 4. Run Progressive Canary Rollout with Automated Rollback
Demonstrates canary deployment (5% traffic) where the watchdog detects elevated errors and immediately reverts traffic to baseline:
```powershell
.venv\Scripts\python.exe day_14\session_1\main.py --simulate-canary
```

### 5. Run Automated Test Suite
Runs all end-to-end regression tests via unittest:
```powershell
.venv\Scripts\python.exe day_14\session_1\test_ci_pipeline.py
```
