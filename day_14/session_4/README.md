# Day 14 - Session 4: Incident Response

## Overview

In mission-critical autonomous agent architectures, incident response cannot be an afterthought. When foundational LLMs suffer from upstream degradation, floating-tag silent updates, or hallucinations, traditional software engineering assumptions break down:
- The agent does not necessarily crash with HTTP 500 errors; it may generate syntactically invalid tool calls or attempt dangerous unapproved cluster actions.
- Checkpoint resumption queues can turn a single failed request into an infinite **poison crash loop**.
- Rolling back application code is ineffective if the root cause was an unpinned model alias or an updated system prompt.

This module provides a production-grade **Incident Response Framework** for agentic systems:
1. **Multi-Level Kill Switches**: Operational controls to freeze mutating tools (`READ_ONLY`), mandate human-in-the-loop review (`MANDATORY_HITL`), or trigger a hard halt (`EMERGENCY_SHUTDOWN`).
2. **Provider Circuit Breaker**: Automated failure tracking that trips to `OPEN` when consecutive provider errors (429, 502, 504) exceed SLO thresholds.
3. **Automated Configuration Rollback**: Instant reversion of prompts and model IDs to the **Last Known Good (LKG)** baseline without container redeployment.
4. **SRE Incident Runbook**: Standardized protocols covering Sev-1/Sev-2 triage, failover routing, and silent model update verification.
5. **Blameless Postmortem (INC-2026-0929)**: Authentic Google SRE-style analysis of a real Week 3 failure involving upstream schema drift and checkpoint crash loops.

---

## Architecture: Emergency Safety Gate

```
                             Incoming User Incident Query
                                          │
                                          ▼
                      ┌───────────────────────────────────────┐
                      │    Emergency Kill Switch Controller   │
                      └───────────────────┬───────────────────┘
                                          │
            ┌─────────────────────────────┼─────────────────────────────┐
            ▼                             ▼                             ▼
   [NORMAL LEVEL]                [READ_ONLY LEVEL]            [EMERGENCY_SHUTDOWN]
   All actions permitted         Blocks destructive tools     Completely halts agent
                                 (Node drain, DB drop)        Returns static fallback
                                          │
                                          ▼
                      ┌───────────────────────────────────────┐
                      │    Tool Dispatcher & Defensive Parser │
                      │  - Strips markdown code fences        │
                      │  - Recovers from upstream schema drift│
                      └───────────────────┬───────────────────┘
                                          │
                                          ▼
                      ┌───────────────────────────────────────┐
                      │       Provider Circuit Breaker        │
                      │  - Monitors 500/504/429 errors        │
                      │  - Trips OPEN on 4 consecutive errors │
                      │  - Auto-routes to secondary model     │
                      └───────────────────────────────────────┘
```

---

## Core Components

| Component | File | Description |
| :--- | :--- | :--- |
| **Kill Switch Controller** | [`kill_switch_controller.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_14/session_4/kill_switch_controller.py) | Multi-tier operational kill switch state machine, circuit breaker, and configuration rollback engine. |
| **Incident Runbook** | [`incident_runbook.md`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_14/session_4/incident_runbook.md) | Production SRE runbook with triage matrix, kill switch enforcement commands, and failover procedures. |
| **Blameless Postmortem** | [`postmortem_incident_inc042.md`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_14/session_4/postmortem_incident_inc042.md) | Formal postmortem for INC-2026-0929 (schema drift, checkpoint crash loops, and rogue cluster actions). |
| **Safety CLI** | [`main.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_14/session_4/main.py) | Interactive CLI to simulate incidents, trip circuit breakers, enforce kill switch levels, and execute rollbacks. |
| **Test Suite** | [`test_incident_response.py`](file:///c:/Users/harsh/OneDrive/Desktop/Agentic-AI/day_14/session_4/test_incident_response.py) | Unit tests validating kill switch levels, circuit breaker state machine, and defensive parser. |

---

## Verification & Execution Guide

### 1. Run Automated Test Suite
Executes all 5 test cases validating kill switch levels, circuit breakers, rollbacks, and schema parsing:
```powershell
.venv\Scripts\python.exe day_14\session_4\test_incident_response.py
```

### 2. Run Full Incident & Rollback Simulation
Simulates silent upstream provider drift, circuit breaker trip, kill switch block, and configuration rollback:
```powershell
.venv\Scripts\python.exe day_14\session_4\main.py --simulate-incident
```

### 3. Enforce Kill Switch Levels via CLI
```powershell
# Freeze mutating tools globally
.venv\Scripts\python.exe day_14\session_4\main.py --set-kill-switch READ_ONLY --reason "Suspected rogue cluster action"

# Force 100% human-in-the-loop review
.venv\Scripts\python.exe day_14\session_4\main.py --set-kill-switch MANDATORY_HITL --reason "Groundedness drift detected"

# Emergency Shutdown
.venv\Scripts\python.exe day_14\session_4\main.py --set-kill-switch EMERGENCY_SHUTDOWN --reason "Catastrophic provider outage"

# Reset back to Normal
.venv\Scripts\python.exe day_14\session_4\main.py --set-kill-switch NORMAL --reason "Mitigation verified"
```

### 4. Rollback Configuration to Last Known Good (LKG)
```powershell
.venv\Scripts\python.exe day_14\session_4\main.py --rollback-lkg --reason "Prompt v1.1.0 regression"
```

### 5. Inspect Incident Runbook and Postmortem
```powershell
.venv\Scripts\python.exe day_14\session_4\main.py --show-runbook
.venv\Scripts\python.exe day_14\session_4\main.py --show-postmortem
```
