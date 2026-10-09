# Updated Sprint 2 Board: Post-Replan Scope Allocation

**Sprint:** Sprint 2 — Delivery Integration, Safety Hardening & Code Review  
**Session:** Day 18 — Session 1: Standup & Replan  
**Date:** October 9, 2026  
**Artifact ID:** `USB-DAY18-S1-001`  

---

## 1. Updated MoSCoW Sprint Board

```text
========================================================================================
                  UPDATED SPRINT 2 BOARD (AFTER DELIBERATE SCOPE REPLAN)
========================================================================================
Total Available Capacity: 16.0 Engineering Hours
Committed Must-Have Load: 13.5 Hours (16 Story Points) -> 84.4% Utilization
Contingency Buffer      :  2.5 Hours (15.6% Safe Buffer)
========================================================================================
```

### 🟢 MUST HAVE (P0 — Committed Core Delivery)
| Task ID | Task Title | Story Points | Hours | Status | Assignee | Acceptance Criteria |
|:---:|---|:---:|:---:|:---:|:---:|---|
| **TASK-2.1** | **REST Delivery Surface & Universal CLI** | 5 | 4.0h | `[IN PROGRESS]` | Harsh | FastAPI `/triage` endpoint + CLI processing alerts and returning structured diagnosis. |
| **TASK-2.2** | **PII Redaction & Security Guardrails** | 3 | 3.0h | `[TO DO]` | Harsh | Automatic redaction of SSNs, emails, credit cards, JWT tokens, and API secrets from logs. |
| **TASK-2.3** | **HMAC-SHA256 Cryptographic HITL Gate** | 5 | 4.0h | `[TO DO]` | Harsh | Require cryptographically verified HMAC signatures before executing any Tier 3 action. |
| **TASK-2.5** | **Automated CI Regression Test Gate** | 3 | 2.5h | `[TO DO]` | Harsh | One-command CLI regression runner that exits with code 1 if accuracy falls below 95%. |
| **TOTAL** | **Must-Have Committed Total** | **16 SP** | **13.5h** | — | — | **84.4% Capacity Load** |

---

### 🟡 SHOULD HAVE (P1 — Performance Hardening)
| Task ID | Task Title | Story Points | Hours | Status | Assignee | Acceptance Criteria |
|:---:|---|:---:|:---:|:---:|:---:|---|
| **TASK-2.6** | **Redis Cluster State Cache (30s TTL)** | 3 | 2.5h | `[TO DO]` | Harsh | Prevent external cloud API rate limiting during outage cascades. |
| **TASK-2.7** | **SHA-256 Merkle Audit Log Chain** | 2 | 2.0h | `[TO DO]` | Harsh | Immutable append-only audit trail guaranteeing non-repudiation for incident actions. |

---

### 🔵 COULD HAVE (P2 — Contingent Stretch / Demoted Scope)
| Task ID | Task Title | Story Points | Hours | Status | Prior Status | Reason for Demotion |
|:---:|---|:---:|:---:|:---:|:---:|---|
| **TASK-2.4** | **Bidirectional Slack/Teams Bot** | 5 | 4.5h | `[DEFERRED]` | `MUST HAVE` | **Scope cut:** Requires complex OAuth2 and modal UI. Demoted to protect safety gates. |
| **TASK-2.8** | **Auto-Generated Markdown Postmortem** | 3 | 2.5h | `[DEFERRED]` | `COULD HAVE` | Non-blocking post-incident convenience feature. |

---

### 🔴 WON'T HAVE (P3 — Explicitly Cut)
| Task ID | Task Title | Reason for Exclusion |
|:---:|---|---|
| **TASK-2.9** | **Full Multi-Region Autonomous Active-Active Failover** | Far exceeds single-service triage charter; high blast radius. |
| **TASK-2.10**| **Custom LLM Fine-Tuning** | Unnecessary compute expenditure ($>50k); in-context tooling achieves 100%. |

---

## 2. Scope Migration Audit Log

```json
{
  "replan_timestamp": "2026-10-09T10:00:00Z",
  "scope_migrations": [
    {
      "task_id": "TASK-2.4",
      "task_name": "Bidirectional Slack/Teams Bot",
      "previous_classification": "MUST_HAVE",
      "new_classification": "COULD_HAVE",
      "story_points": 5,
      "estimated_hours": 4.5,
      "decision_driver": "Protect 16-hour Sprint 2 timebox for HMAC cryptographic safety and automated regression testing",
      "approver": "Dr. Elena Rostova (Mentor)"
    }
  ],
  "capacity_delta": {
    "previous_committed_hours": 18.0,
    "new_committed_hours": 13.5,
    "hours_freed": 4.5,
    "contingency_buffer_hours": 2.5
  }
}
```
