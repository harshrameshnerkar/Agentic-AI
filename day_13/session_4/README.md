# Day 13 - Session 4: Human-in-the-Loop (HITL) Design & Audit Ledger

## Overview

In mission-critical production environments (such as Site Reliability Engineering, financial transactions, database migrations, and infrastructure management), autonomous agents cannot be granted unrestricted write permissions without safeguards. Unsupervised execution of destructive actions introduces systemic operational risk: accidental table drops, unexpected cluster restarts during peak traffic, or cascading service outages.

This module implements a production-grade **Human-in-the-Loop (HITL)** framework combined with a **Cryptographic Tamper-Evident Audit Ledger**.

---

## Architecture & Core Components

```
                       User / Alert Incident
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │   HITL SRE Agent      │
                     │  (Diagnostic Loop)    │
                     └───────────┬───────────┘
                                 │ Formulates Plan
                                 ▼
                    Destructive Action Detected?
                   (e.g., restart, rollback, drop)
                     /                       \
             [NO]   /                         \   [YES]
                   ▼                           ▼
        ┌─────────────────────┐    ┌──────────────────────────────────┐
        │ Execute Safe Read   │    │ Check Blast Radius & Confidence  │
        │ Tool (telemetry/log)│    └─────────────────┬────────────────┘
        └──────────┬──────────┘                      │
                   │                                 ▼
                   │                   ┌──────────────────────────────┐
                   │                   │ Human Approval Gate (Queue)  │
                   │                   │  - Status: PENDING           │
                   │                   │  - Operator Review Station   │
                   │                   └──────────────┬───────────────┘
                   │                                  │
                   │                     ┌────────────┴────────────┐
                   │                     ▼                         ▼
                   │                [REJECTED]                 [APPROVED]
                   │                     │                         │
                   │                     ▼                         ▼
                   │              Abort Action &          ┌──────────────────┐
                   │              Report to User          │ Snapshot State & │
                   │                                      │ Execute Action   │
                   │                                      └────────┬─────────┘
                   │                                               │
                   │                                               ▼
                   │                                  ┌───────────────────────┐
                   │                                  │ Register Compensating │
                   │                                  │ Action (Undo Token)   │
                   │                                  └───────────┬───────────┘
                   │                                              │
                   └──────────────────────┬───────────────────────┘
                                          │
                                          ▼
                         ┌─────────────────────────────────┐
                         │ Cryptographic Audit Trail       │
                         │ (SHA-256 Block Chained Ledger)  │
                         └─────────────────────────────────┘
```

### 1. Blast Radius & Approval Gates ([approval_queue.py](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_13/session_4/approval_queue.py))
Actions are classified by blast radius:
- **`LOW`**: Read-only queries, log analysis, telemetry inspection (automated execution permitted).
- **`MEDIUM`**: Non-destructive cache flushes, log level adjustments (automated if confidence $\ge 0.95$).
- **`HIGH` / `CRITICAL`**: Pod restarts, traffic rerouting, schema migrations, rollbacks (always paused awaiting explicit human sign-off).

The approval queue models each ticket with:
- Ticket ID (e.g. `APR-824A468A`)
- Tenant ID & Session ID
- Action name & tool parameters
- Plain-English justification explaining *why* the action is necessary
- Concrete evidence citations (e.g., error rates, connection metrics)
- Time-to-live expiration (prevents stale authorizations from executing hours later)

### 2. Compensating & Reversible Actions ([compensating_actions.py](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_13/session_4/compensating_actions.py))
Every destructive mutation snapshots pre-execution state before modifying production resources:
- Registers an inverse compensating handler (e.g. restart $\to$ scale/rollback, route $\to$ reset routing).
- Issues an `action_id` (e.g. `ACT-BA0A2BE3`) allowing the operator or automated watchdog to trigger an instantaneous rollback (`compensate_action`).

### 3. Cryptographic Tamper-Evident Audit Trail ([audit_trail.py](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_13/session_4/audit_trail.py))
Every tool call, outcome, approval gate trigger, and rejection is recorded into an append-only JSONL ledger. Each record contains:
- `event_id`, `timestamp_utc`, `tenant_id`, `session_id`, `event_type`, `tool_name`
- `tool_arguments`, `result_summary`, `error`, `duration_ms`
- `previous_hash`: The SHA-256 hash of the preceding ledger entry.
- `entry_hash`: $\text{SHA-256}(\text{all canonical fields} + \text{previous\_hash})$.

The ledger provides a `verify_integrity()` method that mathematically proves the historical record has not been altered, deleted, or backdated.

### 4. Interactive Operator Review Station ([main.py](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_13/session_4/main.py))
Provides a CLI and API review terminal for SRE operators to inspect pending tickets, review AI-synthesized evidence, and grant or deny execution.

---

## Verification & Execution Guide

### Run End-to-End Test Suite
Runs the 5-stage lifecycle verification (Diagnostic $\to$ Gate Pause $\to$ Rejection $\to$ Approval & Snapshot $\to$ Undo $\to$ Cryptographic Chain Audit):
```powershell
.venv\Scripts\python.exe day_13\session_4\test_hitl_workflow.py
```

### Run Operator Review Station
Simulates the interactive review desk handling incoming high-blast approval tickets:
```powershell
.venv\Scripts\python.exe day_13\session_4\main.py --review-station
```
