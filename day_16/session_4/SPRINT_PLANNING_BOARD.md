# Sprint Planning Board & MoSCoW Prioritisation Charter

**Sprint Planning Horizon:** Sprint 1 (Day 17) & Sprint 2 (Day 18)  
**Session:** Day 16 — Session 4: Plan, Estimate & Eval Set First  
**Author:** Harsh Ramesh Nerkar (Intern, Autonomous SRE Systems)  
**Mentor & Technical Reviewer:** Dr. Elena Rostova (Principal AI Systems Architect)  
**Date:** October 8, 2026  
**Artifact ID:** `SPB-DAY16-S4-001`  
**Associated Golden Eval Set:** [`eval_dataset_30.json`](eval_dataset_30.json) (30 Pre-Code Cases)

---

## 1. Executive Planning Principle: "Eval Set Before Any Code"

> *"Junior engineers start typing code the minute a problem is described. That is how you build brittle, unguided software.*  
> *In production systems engineering, you NEVER write a single line of application logic until you have:*  
> *1. Broken the work down into estimated, granular tasks.*  
> *2. Applied ruthless MoSCoW prioritisation (Must / Should / Could / Won't).*  
> *3. Constructed a comprehensive, pre-code evaluation dataset so your system has a fixed target to aim at.*  
> *The 30-case evaluation set is your contract with reality."*  
> — **Dr. Elena Rostova, Principal AI Systems Architect**

---

## 2. MoSCoW Prioritisation Framework

| Priority Category | Guiding Principle | Story Points | Hours | Scope Commitment |
|:---|---|:---:|:---:|:---|
| **Must Have (M)** | Non-negotiable for system viability; without these, the sprint fails. | 21 SP | 18.0h | **100% Commitment** |
| **Should Have (S)** | Critical for production efficiency and SLAs, but viable workarounds exist. | 13 SP | 11.0h | **Committed if velocity holds** |
| **Could Have (C)** | High-value enhancements if time permits; first to be cut if velocity drops. | 8 SP | 7.0h | **Contingent stretch goals** |
| **Won't Have (W)** | Explicitly out-of-scope for Sprint 1 & 2 to protect blast radius and timeline. | — | — | **Explicitly Excluded** |

---

## 3. Filled Sprint Board & Task Breakdown

### 🟢 Must Have (P0 — Non-Negotiable Core)
| Task ID | Task Description | Owner | Est. SP | Est. Hrs | Sprint | Acceptance Criteria (Definition of Done) | Risk |
|:---:|---|:---:|:---:|:---:|:---:|---|:---:|
| **MUST-01** | **30-Case Golden Evaluation Harness** | Harsh | 3 | 2.5h | Day 16 | 30 verified cases (8 static, 16 ephemeral, 6 adversarial) written before code. | Low |
| **MUST-02** | **De-Risk Riskiest Tool Integration** | Harsh | 5 | 4.0h | Day 17 (S1) | Async concurrent dispatch across Kube/Prom/Git/Logs in $< 2.5\text{s}$ with circuit breakers. | High |
| **MUST-03** | **Non-Agent Baseline Scoring (Plain vs RAG)** | Harsh | 3 | 3.0h | Day 17 (S2) | Empirical scorecard recorded; proofs of 0% plain and 30% vanilla RAG ceiling. | Low |
| **MUST-04** | **Ephemeral Cluster Telemetry Diagnostic Tool** | Harsh | 5 | 4.5h | Day 17 (S3) | Ingest live exit codes, memory %, and fatal stack traces; pass rate $\ge 90\%$. | Med |
| **MUST-05** | **Cryptographic HMAC-SHA256 HITL Gateway** | Harsh | 5 | 4.0h | Day 18 (S2) | Block 100% of Tier 3 consequential actions until valid cryptographic signature provided. | Med |

---

### 🟡 Should Have (P1 — Performance & Production Hardening)
| Task ID | Task Description | Owner | Est. SP | Est. Hrs | Sprint | Acceptance Criteria (Definition of Done) | Risk |
|:---:|---|:---:|:---:|:---:|:---:|---|:---:|
| **SHOULD-01** | **Sub-5ms Intent Router** | Harsh | 3 | 2.5h | Day 17 (S3) | Classify `STATIC_POLICY` vs `EPHEMERAL_INCIDENT`; reduce latency by $\ge 10\%$. | Low |
| **SHOULD-02** | **In-Process 50k-Line Log Compactor** | Harsh | 3 | 2.5h | Day 17 (S1) | Filter 99% noise from 50,000 raw lines down to fatal traces in $< 1.0\text{s}$. | Med |
| **SHOULD-03** | **Redis Cluster State In-Memory Cache (30s TTL)** | Harsh | 5 | 4.0h | Day 18 (S1) | Guard against cloud API rate limiting during cascade outages; cache invalidation on rollout. | Med |
| **SHOULD-04** | **Automated CI Regression Gate** | Harsh | 2 | 2.0h | Day 18 (S4) | Single command test harness fails build if accuracy drops below 95%. | Low |

---

### 🔵 Could Have (P2 — Stretch Enhancements)
| Task ID | Task Description | Owner | Est. SP | Est. Hrs | Sprint | Acceptance Criteria (Definition of Done) | Risk |
|:---:|---|:---:|:---:|:---:|:---:|---|:---:|
| **COULD-01** | **Slack / PagerDuty Interactive Webhook Bot** | Harsh | 5 | 4.0h | Day 18 (S2) | Post triage diagnosis into `#prod-incidents` channel with interactive approve/reject buttons. | Low |
| **COULD-02** | **Automated Postmortem Markdown Generator** | Harsh | 3 | 3.0h | Day 18 (S2) | Generate retro document in Jira/Confluence format with root cause and timeline. | Low |

---

### 🔴 Won't Have (P3 — Explicitly Cut / Out of Scope)
| Item ID | Excluded Feature / Scope | Rationalization & Justification |
|:---:|---|---|
| **WONT-01** | **Autonomous Production Database Migrations** | Violates Red Line #1: High blast radius; irreversible risk of data loss. |
| **WONT-02** | **Fine-Tuning a Foundation LLM from Scratch** | Prohibitive training cost ($> \$50\text{k}$) and 3-week timeline; in-context tool augmentation satisfies the 95% target at \$0.0003/query. |
| **WONT-03** | **Multi-Cloud Autonomous Failover (AWS to GCP)** | Requires complex DNS/BGP routing orchestration far beyond the single-service triage charter. |

---

## 4. Team Capacity & Velocity Planning

```
================================================================================
                    CAPACITY & WORKLOAD BALANCE
================================================================================
Team: Harsh Ramesh Nerkar (Intern, 1.0 FTE) + Dr. Elena Rostova (Mentor, 0.25 FTE)
Available Working Hours (Day 17 - Day 18): 32.0 Engineering Hours
Planned Sprint Load:
  • Must-Have Tasks  : 21 Story Points (~18.0 Hours)  -->  56.3% Capacity
  • Should-Have Tasks: 13 Story Points (~11.0 Hours)  -->  34.4% Capacity
  • Contingency Buffer:  —              (~3.0 Hours)  -->   9.3% Buffer
  • Total Planned    : 34 Story Points (~29.0 Hours)  -->  90.7% Total Load
================================================================================
```

---

## 5. Pre-Code 30-Case Evaluation Set Architecture

The evaluation set [`eval_dataset_30.json`](eval_dataset_30.json) was authored **prior to any agent implementation** across three critical test vectors:

```
+-------------------------------------------------------------------------------+
|                       30-CASE EVALUATION SET COMPOSITION                      |
+-------------------------------------------------------------------------------+
| 1. Static Runbook / Policy Queries (8 Cases / 26.7%):                         |
|    • Vault root token rotation, S3 lifecycle (SEC-DR-401), Twilio SMS retries |
|    • PagerDuty SLAs, TLS cert rotation, break-glass YubiKey, ArgoCD, SOX DB   |
|                                                                               |
| 2. Ephemeral Cluster Incidents (16 Cases / 53.3%):                            |
|    • ExitCode 137 OOMKilled, HikariCP pool exhaustion, Kafka partition 4 DLQ  |
|    • Missing ConfigMap keys, Redis KEYS * pegging CPU, Lucene storage evicted |
|    • Staging TLS cert overwrite, Alpine CGO segfault 139, Karpenter GPU quota |
|    • Postgres deadlocks, CoreDNS loops, Cloudflare rate limits, AMQP leaks     |
|    • SendGrid key desync, TCP SYN backlog drops, Istio sidecar mTLS 503 UC    |
|                                                                               |
| 3. Adversarial / Security Red Lines (6 Cases / 20.0%):                        |
|    • Prompt injections: DROP TABLE accounts override, 'rm -rf /' restore      |
|    • PII payroll exfiltration attempt, autonomous terraform destroy VPCs      |
|    • Unauthorized PKI certificate generation, corrupted JSON payload rejection|
+-------------------------------------------------------------------------------+
```

---

## 6. Mentor Sign-Off & Approval

> **Mentor Sign-Off Memo:**  
> **Reviewer:** Dr. Elena Rostova, Principal AI Systems Architect  
> **Status:** **APPROVED & BASELINED**  
> 
> *"This Sprint Planning Board and 30-case pre-code evaluation set satisfy the highest standards of production engineering.*  
> *Having 6 adversarial red-line cases embedded directly alongside the static and ephemeral cases ensures our safety boundaries are tested continuously from Day 1.*  
> *Harsh is cleared to begin Sprint 1 implementation."*
