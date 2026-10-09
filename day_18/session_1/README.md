# Day 18 - Session 1: Standup & Replan

## 📌 Syllabus & Session Objectives
- **Session:** Day 18 - Session 1: Standup & Replan
- **Topic:** Build Sprint 2 & Code Review — Honest Re-Estimation & Scope Pruning
- **Timebox:** 09:30 - 10:00 (0.5 hours)
- **What to Learn:** Standup, then honest re-estimation. Cutting scope deliberately rather than silently missing it. Deciding what moves from Must to Could.
- **Task:** Updated Sprint Board with a documented scope decision.
- **Resources:** Intern (Harsh Ramesh Nerkar) + Mentor (Dr. Elena Rostova).

---

## 🎯 Engineering Principle: "Cutting Scope Deliberately"

> *"A junior engineer stays silent, tries to build everything, and quietly misses the delivery deadline or ships broken security gates.*  
> *"A staff engineer conducts honest re-estimation early, makes a deliberate scope cut in writing, and protects the core production invariants.*  
> *"Cutting scope deliberately rather than silently missing it is a professional superpower."*  
> — **Dr. Elena Rostova, Principal AI Systems Architect**

---

## 📋 The Updated Sprint 2 Board & Scope Decision

```text
========================================================================================
                  UPDATED SPRINT 2 BOARD (POST-REPLAN)
========================================================================================
Total Available Capacity: 16.0 Engineering Hours
Committed Must-Have Load: 13.5 Hours (16 Story Points) -> 84.4% Utilization
Contingency Buffer      :  2.5 Hours (15.6% Safe Buffer)
========================================================================================

[1] MUST HAVE (P0 - Non-Negotiable Core Delivery):
  • [TASK-2.1] REST Delivery Surface & Universal CLI      | 5 SP (4.0h)
  • [TASK-2.2] PII Redaction & Security Guardrails        | 3 SP (3.0h)
  • [TASK-2.3] HMAC-SHA256 Cryptographic HITL Gate        | 5 SP (4.0h)
  • [TASK-2.5] Automated CI Regression Test Gate          | 3 SP (2.5h)

[2] SHOULD HAVE (P1 - Performance Hardening):
  • [TASK-2.6] Redis Cluster State Cache (30s TTL)        | 3 SP (2.5h)
  • [TASK-2.7] SHA-256 Merkle Audit Log Chain             | 2 SP (2.0h)

[3] COULD HAVE (P2 - Demoted Scope / Contingent Stretch):
  • [TASK-2.4] Bidirectional Slack/Teams Bot              | 5 SP (4.5h) [DEMOTED FROM MUST]
  • [TASK-2.8] Auto-Generated Markdown Postmortem         | 3 SP (2.5h)
========================================================================================
```

### Documented Scope Cut Rationale:
- **Demoted Task:** `TASK-2.4: Bidirectional Slack/Teams Bot` (5 SP, 4.5h) demoted from `MUST_HAVE` to `COULD_HAVE`.
- **Reason:** Building bidirectional Slack OAuth2 and interactive buttons consumes 4.5h and risks jeopardizing the HMAC cryptographic gateway and automated CI regression gates within the 16.0h Sprint 2 timebox.
- **Capacity Impact:** Pre-replan Must-Have load was 18.0h (a 2.0h deficit). Post-replan Must-Have load is **13.5h**, freeing **4.5h** and leaving a healthy **2.5h contingency buffer**.

---

## 📂 Deliverables & File Directory

- [STANDUP_REPLAN_NOTES.md](STANDUP_REPLAN_NOTES.md): 15-minute standup notes, capacity re-estimation analysis, and mentor approval memo.
- [UPDATED_SPRINT_BOARD.md](UPDATED_SPRINT_BOARD.md): Updated Sprint 2 board with post-replan task allocations and scope migration audit.
- [REPLAN_DATA.json](REPLAN_DATA.json): Machine-readable capacity telemetry before and after scope cut.
- [replan_manager.py](replan_manager.py): Python engine computing capacity metrics and scope migration deltas.
- [main.py](main.py): Interactive CLI supporting `--board` and `--scope-cut`.
- [test_replan.py](test_replan.py): Unit test suite verifying capacity calculations and scope migration records.
- [requirements.txt](requirements.txt): Environment configuration.

---

## 🚀 Execution & Verification

### 1. View Updated Board & Capacity
```bash
python day_18/session_1/main.py
```

### 2. View Documented Scope Cut Decision
```bash
python day_18/session_1/main.py --scope-cut
```

### 3. Run Test Suite
```bash
python day_18/session_1/test_replan.py
```
*Expected: 4 tests passing in < 0.01 seconds with 100% assertions satisfied.*
