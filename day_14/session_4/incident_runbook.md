# SRE Incident Response Runbook: Agentic AI Production Operations

**Document ID**: RB-LLM-OPS-001  
**Target Services**: Production Autonomous Agent, Human-in-the-Loop Approval Queue, Model Routing Engine  
**Last Revised**: 2026-10-07  
**On-Call Escalation**: `#sre-incidents` | PagerDuty: `Agent-Core-Oncall`

---

## 1. Severity Classification & Triage Matrix

| Severity | Definition & Impact Criteria | MTTA Target | MTTR Target | Incident Commander |
| :--- | :--- | :--- | :--- | :--- |
| **SEV-1 (Critical)** | Agent executing unapproved destructive actions; pass rate $< 80\%$; upstream provider completely down; checkpoint corruption loop. | **< 5 min** | **< 30 min** | Staff SRE + Agent Tech Lead |
| **SEV-2 (Major)** | Provider degradation ($p95 > 2,000\text{ms}$); error rate $5\% - 15\%$; failover circuit breaker tripped; token cost surge $> 100\%$. | **< 15 min** | **< 1 hour** | Primary On-Call SRE |
| **SEV-3 (Minor)** | Silent quality decay detected (groundedness $< 0.85$); minor prompt regression; non-blocking tool timeout. | **< 1 hour** | **< 4 hours** | Secondary On-Call SRE |

---

## 2. Emergency Kill Switch Playbook

The agent execution engine incorporates a multi-tier operational kill switch. When an incident is declared, execute the appropriate kill switch level immediately before investigating root cause.

```
       ┌────────────────────────────────────────────────────────┐
       │             INCIDENT DECLARED (SEV-1 / SEV-2)          │
       └───────────────────────────┬────────────────────────────┘
                                   │
         Is the agent attempting destructive or unknown actions?
                     ├── YES ──► Level 1: READ_ONLY Mode
                     │           (Blocks node drain, DB drop, restarts)
                     │
         Are tool results suspicious or ungrounded?
                     ├── YES ──► Level 2: MANDATORY_HITL Mode
                     │           (100% of actions routed to human review)
                     │
         Is the model completely failing or corrupting data?
                     └── YES ──► Level 3: EMERGENCY_SHUTDOWN
                                 (Freezes agent, returns static fallback)
```

### Kill Switch Enforcement Commands

```powershell
# Level 1: Freeze all mutating/destructive tools (Allow diagnostics only)
.venv\Scripts\python.exe day_14\session_4\main.py --set-kill-switch READ_ONLY --reason "Suspected rogue cluster mutation"

# Level 2: Force 100% human-in-the-loop review for all tool calls
.venv\Scripts\python.exe day_14\session_4\main.py --set-kill-switch MANDATORY_HITL --reason "Groundedness drop, human verification required"

# Level 3: Hard Stop / Emergency Shutdown (Immediate agent execution halt)
.venv\Scripts\python.exe day_14\session_4\main.py --set-kill-switch EMERGENCY_SHUTDOWN --reason "Catastrophic provider outage / checkpoint corruption"

# Reset Kill Switch to Normal (Post-incident verification)
.venv\Scripts\python.exe day_14\session_4\main.py --set-kill-switch NORMAL --reason "Root cause mitigated, regression suite verified"
```

---

## 3. Provider Degradation & Failover Playbook

When the upstream foundation model provider (e.g., Anthropic Claude or OpenAI GPT) experiences rate-limiting (429), gateway timeouts (504), or internal errors (500/503):

### Step 1: Verify Provider Status
Check official status pages and telemetry dashboards:
- Anthropic Status: `https://status.anthropic.com`
- OpenAI Status: `https://status.openai.com`
- Telemetry: Check `http://127.0.0.1:8000/` Latency Percentiles chart and Failure Categories.

### Step 2: Trip Circuit Breaker & Engage Provider Failover
If consecutive provider errors exceed 5 within 60 seconds:
1. The **Circuit Breaker** trips to `OPEN`, shielding downstream systems from thundering herds.
2. Route traffic to the secondary fallback model:
   - Primary: `claude-3-5-sonnet`
   - Secondary: `gpt-4o`
   - Tertiary: Local Distilled Classifier / Static Graceful Degradation Response

```powershell
# Manually force failover to secondary model
.venv\Scripts\python.exe day_14\session_4\main.py --failover-model gpt-4o --reason "Primary provider 504 Gateway Timeouts"
```

---

## 4. Prompt & Model Rollback Playbook

When an incident is triggered by a regressed prompt release, schema change, or upstream model update:

### Step 1: Identify Last Known Good (LKG) Version
Retrieve the verified baseline commit and prompt tag:
```powershell
# Inspect active config version vs history
.venv\Scripts\python.exe day_14\session_4\main.py --show-config
```

### Step 2: Execute Instant Rollback
Revert the configuration controller to the last known good version without restarting container replicas:
```powershell
# Rollback to Last Known Good (LKG) baseline
.venv\Scripts\python.exe day_14\session_4\main.py --rollback-lkg --reason "Prompt v2.1.0 induced high hallucination rate"
```

### Step 3: Run Validation Regression Suite
Execute the 100-case stratified evaluation suite to verify that the rollback restored compliance:
```powershell
.venv\Scripts\python.exe day_14\session_2\main.py --eval-100
```
Confirm:
- Overall pass rate $\ge 95.0\%$.
- Destructive safety score $= 100.0\%$.

---

## 5. Detecting and Mitigating Silent Model Updates

### What is a Silent Model Update?
A silent model update occurs when an LLM provider deploys backend weight updates, alignment changes, or system prompt adjustments to an existing model endpoint (e.g., updating `gpt-4o` or `claude-3-5-sonnet` weights without incrementing the public model string or notifying consumers).

### Warning Signs of Silent Model Drift:
1. **Schema Breakages**: Model suddenly wraps JSON tool calls in Markdown blocks (```` ```json ````) instead of raw schema objects.
2. **Refusal Surges**: Model refuses safe operational diagnostics (e.g., "reading error logs") due to overzealous safety filters.
3. **Token Inflation**: Model output verbosity increases by 30–60% for identical prompts, causing cost spikes and latency degradation.
4. **Judge Calibration Shift**: Automated evaluator pass rates jump or drop without any local code changes.

### Mitigation Protocol:
1. **Pin Exact Dated Snapshots**: NEVER use floating model aliases in production. Use pinned date-stamped versions (e.g., `claude-3-5-sonnet-20241022` or `gpt-4o-2024-08-06`).
2. **Defensive Schema Parsing**: Always strip markdown fences (```` ```json ... ``` ````) and perform resilient Pydantic JSON repair.
3. **Continuous Synthetic Canary Tests**: Run a hourly canary trace that asserts deterministic tool schema generation.
