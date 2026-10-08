# Day 16 - Session 2: Constraints & Success Metrics

## 📌 Syllabus & Session Objectives
- **Session:** Day 16 - Session 2: Constraints & Success Metrics
- **Topic:** Scoping a Real Problem — Engineering Constraints
- **What to Learn:** Accuracy bar, acceptable latency, cost per query ceiling, data sensitivity, what must never be automated. Deciding where a human stays in the loop. Turning a vague ask into a measurable target.
- **Task:** A signed-off success metric with a number, plus the human-in-the-loop boundary agreed in writing.
- **Resources:** Intern (Harsh Ramesh Nerkar) + Stakeholder (Marcus Vance, VP Infrastructure).

---

## 🎯 Turning a Vague Ask into Measurable Targets

In Session 1, the stakeholder asked to:
> *"Make incident response faster and stop fat-finger human mistakes under pressure."*

In this session, we formalized this into **six mathematically verifiable success metrics** with signed-off thresholds:

```
VAGUE ASK: "Make incident response faster and safer"
       │
       ▼ [MATHEMATICAL TRANSLATION]
  • M1 (Accuracy)      : >= 95.0% on 100-case Golden Suite (Floor: 92.0%)
  • M2 (Latency)       : p50 <= 45.0s, p95 <= 60.0s (Hard Ceiling: <= 90.0s)
  • M3 (Cost Ceiling)  : <= $0.10 target, <= $0.15 hard ceiling per triage
  • M4 (Safety)        : 0.0% unattended destructive writes (Zero Tolerance)
  • M5 (Data Privacy)  : 100.0% of API keys, tokens, and PII masked
  • M6 (MTTR)          : >= 80.0% reduction in Mean Time to Recovery
```

---

## 📊 The 6 Signed-Off Success Metrics (With Exact Numbers)

| Metric ID | Metric Name | Exact Target Threshold | Hard Floor / Ceiling | Human Baseline | Status |
|:---:|---|:---:|:---:|:---:|:---:|
| **M1** | **Diagnostic Accuracy** | **$\ge 95.0\%$** | Floor: **$92.0\%$** | 82.4% (Fatigue) | **SIGNED OFF** |
| **M2** | **p95 Triage Latency** | **$\le 60.0\text{ sec}$** | Ceiling: **$\le 90.0\text{ sec}$** | 78.5 mins | **SIGNED OFF** |
| **M3** | **Cost Per Triage Run** | **$\le \$0.10\text{ USD}$** | Ceiling: **$\le \$0.15\text{ USD}$** | $134.50 Toil | **SIGNED OFF** |
| **M4** | **Unattended Destructive Writes** | **$0.0\%$ (Zero)** | Absolute: **$0$ Tolerance** | Manual error risk | **SIGNED OFF** |
| **M5** | **Secret & PII Scrubbing** | **$100.0\%$** | Absolute: **$100.0\%$** | Leak exposure | **SIGNED OFF** |
| **M6** | **MTTR Reduction Ratio** | **$\ge 80.0\%$** | Floor: **$75.0\%$** | ~85.5 mins | **SIGNED OFF** |

---

## 🛡️ The Human-in-the-Loop (HITL) Boundary Agreement

### 1. The 3-Tier Blast-Radius Classification

```
                        Inbound Incident Alert
                                  │
                                  ▼
                    [ Blast-Radius Classifier ]
                                  │
       ┌──────────────────────────┼──────────────────────────┐
       ▼                          ▼                          ▼
[ Tier 1: Read-Only ]     [ Tier 2: Low-Risk ]       [ Tier 3: High-Blast ]
• Log Querying            • Traffic Rebalancing      • Pod Delete / Restart
• Metric Scraping         • Read-Replica Drain       • Deploy Rollback
• Git Commit Diffs        • Cache Pre-Warming        • Cache Flush / Scale Down
       │                          │                          │
       ▼                          ▼                          ▼
 100% Autonomous            Autonomous +               HALTED: HITL Gate
(No Human Waiting)        Rollback Hooks        (Requires Cryptographic HMAC Token)
```

### 2. The 5 Absolute "NEVER AUTOMATE" Red Lines

The following operations are **permanently forbidden** from ever being proposed or executed by an automated agent:

1. **PROHIBITION 1: Drop Database / Truncate Table / Drop Schema** (`DROP TABLE`, `TRUNCATE`, `DROP DATABASE`).
2. **PROHIBITION 2: Persistent Volume (PV/PVC) or Cloud EBS Storage Deletion**.
3. **PROHIBITION 3: Modifying IAM Root Keys, IAM Policies, or ClusterRoleBindings**.
4. **PROHIBITION 4: Direct Git Force-Push to Protected `main` / `master` Branches**.
5. **PROHIBITION 5: Disabling Audit Logging or the Emergency Kill-Switch Watchdog**.

---

## 🔐 The Cryptographic HMAC-SHA256 Approval Protocol

When the agent identifies a Tier-3 destructive remediation:
1. **Packaging**: Compiles proposed command, blast radius analysis, and rollback command.
2. **HMAC Signature**: Creates a tamper-evident token:
   $$\text{HMAC}(\text{IncidentID} \parallel \text{Action} \parallel \text{Parameters} \parallel \text{ExpiresAt}, \text{SecretKey})$$
3. **15-Minute Expiration**: Token automatically expires after 15 minutes; expired tokens cannot clear the gate.
4. **Verification & Audit Ledger**: Validated via constant-time comparison (`hmac.compare_digest`) and recorded into an immutable audit ledger with engineer ID.

---

## 📂 Deliverables & File Directory

- [SIGNED_OFF_SUCCESS_METRICS.md](SIGNED_OFF_SUCCESS_METRICS.md): Official signed charter turning vague asks into 6 mathematical metrics with formal sign-off.
- [HITL_BOUNDARY_AGREEMENT.md](HITL_BOUNDARY_AGREEMENT.md): Operational boundary agreement, 3-tier classification, 5 Never Automate red lines, and cryptographic protocol.
- [constraints_validator.py](constraints_validator.py): Enforcement engine implementing PII/credential masking, blacklist enforcement, blast-radius classification, HMAC token gateway, and batch compliance evaluation.
- [main.py](main.py): Interactive CLI reviewing metrics, HITL boundaries, demoing HMAC approval tokens, and running batch compliance checks.
- [test_constraints.py](test_constraints.py): 7 unit/integration tests verifying all metric thresholds, secret masking, blacklist blocking, HMAC lifecycle, and compliance evaluation.
- [requirements.txt](requirements.txt): Session environment requirements.

---

## 🚀 Execution & Verification

### 1. Run Executive Constraints CLI
```bash
python day_16/session_2/main.py
```

### 2. Demonstrate Cryptographic HITL Token Approval
```bash
python day_16/session_2/main.py --demo-token
```

### 3. Run Compliance Evaluation Against Signed-Off Metrics
```bash
python day_16/session_2/main.py --validate
```

### 4. Run Test Suite
```bash
python day_16/session_2/test_constraints.py
```
*Expected: 7 tests passing in < 0.05 seconds with 100% assertions satisfied.*
