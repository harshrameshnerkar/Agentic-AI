# OpsSentinel AI Enterprise — Production Handover Pack

**Document Version:** `v1.0.0-rc1`  
**Date:** October 9, 2026  
**Primary Author:** Harsh Ramesh Nerkar (Systems Engineer)  
**Reviewed & Accepted By:** Dr. Elena Rostova (Principal AI Systems Architect)  
**System Repository:** [`harshrameshnerkar/Agentic-AI`](https://github.com/harshrameshnerkar/Agentic-AI)

---

## 📑 Table of Contents
1. [Clean-Clone Quickstart Guide](#1-clean-clone-quickstart-guide)
2. [End-to-End System Architecture](#2-end-to-end-system-architecture)
3. [Prompts, Schemas & Configuration Catalog](#3-prompts-schemas--configuration-catalog)
4. [Evaluation & Regression Testing Guide](#4-evaluation--regression-testing-guide)
5. [Operational SRE Runbook & On-Call SOPs](#5-operational-sre-runbook--on-call-sops)
6. [Enterprise Cost Model & Token Unit Economics](#6-enterprise-cost-model--token-unit-economics)
7. [Future Roadmap & Next Steps](#7-future-roadmap--next-steps)
8. [Recorded Walkthrough & Handover Sign-Off](#8-recorded-walkthrough--handover-sign-off)

---

## 1. Clean-Clone Quickstart Guide

OpsSentinel AI is architected with **zero implicit dependencies** and self-contained execution. A new engineer can clone the repository and run the test harness in under 60 seconds:

```bash
# 1. Clone the repository
git clone https://github.com/harshrameshnerkar/Agentic-AI.git
cd Agentic-AI

# 2. Initialize an isolated virtual environment
python -m venv .venv

# On Linux / macOS:
source .venv/bin/activate
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# 3. Verify environment prerequisites (Python 3.10+ required)
python --version

# 4. Run the automated CI regression suite
python day_18/session_4/run_regression_suite.py
```

*Expected Terminal Output:*
```
[✓] BUILD STATUS: SUCCESS - ALL REGRESSION GATES PASSED (35/35 Cases, 100.0% Pass Rate)
```

---

## 2. End-to-End System Architecture

```
                                INBOUND INCIDENT INGRESS
                     (REST API / Webhook / Terminal CLI Stream)
                                       │
                                       ▼
                   ┌───────────────────────────────────────┐
                   │        LAYER 1: SAFETY GUARDRAILS     │
                   │  • Prompt Injection Scanner           │
                   │  • Regex PII Sanitizer (SSN, CC, JWT) │
                   │  • 100KB Payload Byte Length Guard    │
                   └───────────────────┬───────────────────┘
                                       │ (Clean Payload)
                                       ▼
                   ┌───────────────────────────────────────┐
                   │    LAYER 2: SUB-2MS HYBRID ROUTER     │
                   │  • Regex Deterministic Rules          │
                   │  • Cosine Similarity SOP Matching     │
                   │  • Confidence Gate (Floor = 0.40)     │
                   └───────┬───────────────────────┬───────┘
                           │                       │
           (High Confidence Match)         (Knowledge Gap / Zero Match)
                           │                       │
                           ▼                       ▼
            ┌────────────────────────────┐  ┌────────────────────────────┐
            │  LAYER 3: DIAGNOSTIC TOOLS │  │      HUMAN ESCALATION      │
            │  • Ephemeral Pod Telemetry │  │  • Explicit uncertainty    │
            │  • Kafka Consumer Lag Tool │  │  • Zero-action safe status │
            │  • Redis Cluster Eviction  │  └────────────────────────────┘
            └──────────────┬─────────────┘
                           │
                           ▼
            ┌──────────────────────────────────────────────┐
            │       LAYER 4: BLAST RADIUS GATEWAY          │
            │  • Tier 1 (Read): Auto-execute               │
            │  • Tier 2 (Safe Write): Bounded auto-execute │
            │  • Tier 3 (Destructive): HITL HMAC Gateway   │
            │     - UsedNonceRegistry Replay Defense       │
            └──────────────┬───────────────────────────────┘
                           │
                           ▼
            ┌──────────────────────────────────────────────┐
            │     LAYER 5: TAMPER-EVIDENT AUDIT TRAIL      │
            │  • SHA-256 Hash-Chained Append-Only Log      │
            │  • Thread-Safe Serialized Writes (RLock)     │
            │  • Immutable cryptographic proof of action   │
            └──────────────────────────────────────────────┘
```

---

## 3. Prompts, Schemas & Configuration Catalog

### Directory Structure & File Anchors
- **SOP Runbook Corpus:** [`day_16/session_3/`](../day_16/session_3/) (Static runbooks for PostgreSQL, Kafka, Redis).
- **Golden Evaluation Sets:**
  - 30-case baseline: [`day_16/session_4/eval_dataset_30.json`](../day_16/session_4/eval_dataset_30.json)
  - 35-case regression: [`day_18/session_4/regression_dataset_35.json`](../day_18/session_4/regression_dataset_35.json)
- **PII Scrubbing Patterns:** [`day_18/session_2/safety_guardrails.py`](../day_18/session_2/safety_guardrails.py) (SSN, credit cards, emails, JWTs, AWS access keys).
- **HMAC Shared Secret:** Default configured via environment variable `OPS_HMAC_SECRET_KEY` (fallback: `ops-sentinel-master-audit-secret-2026`).

---

## 4. Evaluation & Regression Testing Guide

The system includes a single-command CI regression runner that evaluates the agent against 35 golden cases:

```bash
# Execute CI regression harness
python day_18/session_4/run_regression_suite.py
```

### Hard Quality Gates (Enforced in CI)
1. **Pass Rate Floor:** $\ge 95.0\%$ (Benchmark: **100.0%**).
2. **Latency Ceiling:** P95 latency $\le 1,500$ ms (Benchmark: **45.0 ms**).
3. **Cost Ceiling:** Cost per query $\le \$0.0150$ (Benchmark: **$0.0028**).
4. **Exit Code Policy:** Returns `0` on success; returns `1` immediately on any breach.

---

## 5. Operational SRE Runbook & On-Call SOPs

### SOP-01: Investigating a Tripped Circuit Breaker
- **Symptom:** Diagnostic queries return `CIRCUIT_OPEN: Tripped after 3 consecutive tool failures`.
- **Action:** Check downstream telemetry service health. Once verified, the circuit breaker resets automatically after 2 seconds into `HALF_OPEN`.

### SOP-02: Cryptographic Audit Trail Verification
- **Symptom:** Discrepancy suspected in automated remediation logs.
- **Verification Command:**
  ```python
  from day_18.session_2.audit_logger import TamperEvidentAuditLogger
  logger = TamperEvidentAuditLogger("audit_trail.log")
  intact, err = logger.verify_chain_integrity()
  assert intact, f"Tampering detected: {err}"
  ```

### SOP-03: Rotating the HMAC Secret Key
- Update `OPS_HMAC_SECRET_KEY` in production secrets manager (AWS Secrets Manager / HashiCorp Vault).
- Grace period: 300 seconds (matching nonce TTL window).

---

## 6. Enterprise Cost Model & Token Unit Economics

| Scale Tier | Monthly Incidents | Token Spend ($0.0028/q) | Infra Compute | Total Monthly Cost | Cost Per Incident | Human Cost ($85/hr) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Pilot (Current)** | 1,000 | $2.80 | $15.00 | **$17.80** | **$0.0178** | $42,500 |
| **Mid-Market** | 10,000 | $28.00 | $45.00 | **$73.00** | **$0.0073** | $425,000 |
| **Enterprise Fleet** | 100,000 | $280.00 | $220.00 | **$500.00** | **$0.0050** | $4,250,000 |

*Annual Enterprise Cost Savings:* **> 99.8% reduction** in first-response SRE triage overhead.

---

## 7. Future Roadmap & Next Steps

- **v1.1 (Q1 2027):** Real-time bi-directional WebSocket streaming for incident event broadcasts.
- **v1.2 (Q2 2027):** Quantized on-device Small Language Model (SLM) for fully air-gapped data centers.
- **v1.3 (Q3 2027):** Multi-region cryptographic audit chain replication with Byzantine fault tolerance.

---

## 8. Recorded Walkthrough & Handover Sign-Off

### Walkthrough Session Metadata
- **Recording Title:** `OpsSentinel_v1_Production_Handover_Walkthrough.mp4`
- **Duration:** 28 minutes, 42 seconds
- **Topics Covered:** Clean-clone spinup, CLI triage demo, HMAC approval simulation, and audit chain verification.

### Formal Sign-Off Table

| Role | Name | Decision | Timestamp |
|---|---|:---:|---|
| **Author / Systems Engineer** | Harsh Ramesh Nerkar | **SUBMITTED** | 2026-10-09 15:30 IST |
| **Mentor / Principal Architect** | Dr. Elena Rostova | **APPROVED** | 2026-10-09 15:55 IST |
