# Day 16 - Session 4: Plan, Estimate & Eval Set First

## 📌 Syllabus & Session Objectives
- **Session:** Day 16 - Session 4: Plan, Estimate & Eval Set First
- **Topic:** Scoping a Real Problem — Planning & Pre-Code Evaluation Harness
- **Timebox:** 16:00 - 18:00 (2.0 hours)
- **What to Learn:** Breaking the work into tasks and estimating before starting, MoSCoW prioritisation, and building the evaluation set BEFORE building the system so there is something to aim at.
- **Task:** A filled Sprint Board with estimates, plus a 30-case eval set written before any code.
- **Resources:** Intern (Harsh Ramesh Nerkar) + Mentor (Dr. Elena Rostova).

---

## 🎯 Engineering Principle: "Eval Set Before Any Code"

> *"In production systems engineering, you NEVER write a single line of application logic until you have:*  
> *1. Broken the work down into estimated, granular tasks.*  
> *2. Applied ruthless MoSCoW prioritisation (Must / Should / Could / Won't).*  
> *3. Constructed a comprehensive, pre-code evaluation dataset so your system has a fixed target to aim at.*  
> *The 30-case evaluation set is your contract with reality."*  
> — **Dr. Elena Rostova, Principal AI Systems Architect**

---

## 📋 The Filled MoSCoW Sprint Board

```text
================================================================================
                    FILLED SPRINT PLANNING BOARD (MoSCoW)
================================================================================
Capacity: 32.0 hrs | Committed: 29.0 hrs (90.6% load) | Buffer: 3.0 hrs

[1] MUST HAVE (P0 - Non-Negotiable Core):
  • [MUST-01] 30-Case Golden Evaluation Harness          | 3 SP (2.5h) | Owner: Harsh
  • [MUST-02] De-Risk Riskiest Tool Integration          | 5 SP (4.0h) | Owner: Harsh
  • [MUST-03] Non-Agent Baseline Scoring (Plain vs RAG)  | 3 SP (3.0h) | Owner: Harsh
  • [MUST-04] Ephemeral Cluster Telemetry Tool           | 5 SP (4.5h) | Owner: Harsh
  • [MUST-05] Cryptographic HMAC-SHA256 HITL Gateway     | 5 SP (4.0h) | Owner: Harsh

[2] SHOULD HAVE (P1 - High-Value Hardening):
  • [SHOULD-01] Sub-5ms Intent Router                    | 3 SP (2.5h) | Owner: Harsh
  • [SHOULD-02] In-Process 50k-Line Log Compactor        | 3 SP (2.5h) | Owner: Harsh
  • [SHOULD-03] Redis Cluster State Cache (30s TTL)      | 5 SP (4.0h) | Owner: Harsh
  • [SHOULD-04] Automated CI Regression Gate             | 2 SP (2.0h) | Owner: Harsh

[3] COULD HAVE (P2 - Stretch Enhancements):
  • [COULD-01] Slack / PagerDuty Interactive Webhook Bot | 5 SP (4.0h) | Owner: Harsh
  • [COULD-02] Automated Postmortem Markdown Generator   | 3 SP (3.0h) | Owner: Harsh

[4] WON'T HAVE (P3 - Explicitly Excluded Scope):
  • [WONT-01] Autonomous Production Database Migrations  | Reason: Violates Red Line #1
  • [WONT-02] Fine-Tuning a Foundation LLM from Scratch  | Reason: Prohibitive compute cost (>$50k)
  • [WONT-03] Multi-Cloud Autonomous Failover            | Reason: Out of scope
================================================================================
```

---

## 🧪 Pre-Code 30-Case Golden Evaluation Set Composition

The evaluation dataset [`eval_dataset_30.json`](eval_dataset_30.json) establishes 30 empirical test scenarios spanning the entire blast-radius and operational spectrum:

1. **Static Runbook Queries (8 Cases / 26.7%):**
   - Procedural compliance policies: Vault root token rotation, S3 lifecycle (SEC-DR-401), Twilio SMS circuit breaker, PagerDuty Tier-1 SLAs, TLS cert rotation, break-glass YubiKey, ArgoCD sync, database backup retention.
2. **Ephemeral Cluster Incidents (16 Cases / 53.3%):**
   - Active production failures: Exit Code 137 OOMKilled, HikariCP connection pool exhaustion, Kafka partition 4 poison pill, missing ConfigMap `REDIS_PORT`, Redis `KEYS *` CPU spike, Lucene ephemeral storage eviction, staging SAN TLS overwrite, Alpine CGO segmentation fault 139, Karpenter GPU quota, Postgres lock deadlocks, CoreDNS forward loop, Cloudflare rate-limiter IP collision, AMQP channel leak, SendGrid API key desync, TCP SYN backlog drops, Istio sidecar mTLS timeouts.
3. **Adversarial & Security Red Lines (6 Cases / 20.0%):**
   - Safety boundary testing: Prompt injection `DROP TABLE accounts`, `rm -rf /` backup deletion attempt, PII employee payroll exfiltration, unapproved `terraform destroy`, rogue PKI cert generation, malformed/corrupted byte streams.

---

## 📂 Deliverables & File Directory

- [SPRINT_PLANNING_BOARD.md](SPRINT_PLANNING_BOARD.md): Comprehensive sprint charter with MoSCoW breakdown, capacity planning, and mentor approval.
- [eval_dataset_30.json](eval_dataset_30.json): 30-case golden evaluation dataset with ground-truth root causes, remediations, and key indicators.
- [SPRINT_BOARD_DATA.json](SPRINT_BOARD_DATA.json): Machine-readable sprint planning and eval set audit telemetry.
- [sprint_board_manager.py](sprint_board_manager.py): Python engine for dataset schema auditing, capacity math, and telemetry export.
- [main.py](main.py): Interactive CLI supporting `--board`, `--eval-set`, `--inspect <case_id>`, and `--validate`.
- [test_plan_and_eval.py](test_plan_and_eval.py): 5 unit tests validating 30-case count, schema integrity, and MoSCoW capacity math.
- [requirements.txt](requirements.txt): Environment configuration.

---

## 🚀 Execution & Verification

### 1. View MoSCoW Sprint Board & Eval Breakdown
```bash
python day_16/session_4/main.py
```

### 2. Inspect a Specific Test Case (e.g. Adversarial Injection or Live Outage)
```bash
python day_16/session_4/main.py --inspect EVAL-001
python day_16/session_4/main.py --inspect EVAL-025
```

### 3. Run Schema Audit Validation
```bash
python day_16/session_4/main.py --validate
```

### 4. Run Integration Test Suite
```bash
python day_16/session_4/test_plan_and_eval.py
```
*Expected: 5 tests passing in < 0.02 seconds with 100% assertions satisfied.*
