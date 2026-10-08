# Day 16 - Session 2: Human-in-the-Loop (HITL) Boundary Agreement

**Document Version:** 1.0.0  
**Effective Date:** October 8, 2026  
**Compliance Standard:** SOC-2 Type II, ISO 27001, Enterprise Change Management Policy  
**Parties:**  
- **Lead AI Systems Engineer:** Harsh Ramesh Nerkar  
- **VP of Cloud Infrastructure & Reliability:** Marcus Vance  

---

## 1. Executive Purpose

Autonomous AI agents possess extraordinary diagnostic speed, but unconstrained autonomy in production cloud environments poses catastrophic blast-radius risks.

This document establishes the **binding operational boundary** governing where the agent operates autonomously and where a human engineer **must remain in the loop (HITL)**.

---

## 2. The 3-Tier Blast-Radius Classification Framework

Every tool, diagnostic script, and remediation command available to the agent is categorized into one of three strict tiers:

```
                            Inbound Incident Alert
                                      │
                                      ▼
                        [ Blast-Radius Classifier ]
                                      │
           ┌──────────────────────────┼──────────────────────────┐
           ▼                          ▼                          ▼
   [ Tier 1: Read-Only ]      [ Tier 2: Low-Risk ]       [ Tier 3: High-Blast ]
   • Log Aggregation          • Traffic Rebalancing      • Pod Deletion/Restart
   • Metric Querying          • Read-Replica Drain       • Deploy Rollback
   • Git Diff Inspection      • Cache Warm-Up            • Scale-Down / Flush
           │                          │                          │
           ▼                          ▼                          ▼
     100% Autonomous            Autonomous +               HALTED: HITL Gate
   (No Human Required)         Rollback Hooks         (Requires Cryptographic
                                                            HMAC Token Sign-Off)
```

### Detailed Tier Specifications

| Tier | Category Name | Permitted Operations | Autonomy Level | Safety Controls |
|:---:|---|---|:---:|---|
| **Tier 1** | **Read-Only Diagnostics** | • `query_metrics(service, window)`<br>• `fetch_logs(service, filter)`<br>• `get_pod_status(namespace)`<br>• `get_git_diff(sha)`<br>• `search_runbooks(query)` | **100% Autonomous** | • Read-only service credentials.<br>• Query timeout of 10s.<br>• Automatic PII/Secret scrubbing. |
| **Tier 2** | **Low-Risk Automated Remediation** | • `drain_read_replica(node)`<br>• `warm_cache(keyspace)`<br>• `scale_up_replicas(service, +2)`<br>• `update_routing_weight(canary, 0%)` | **Autonomous with Rollback** | • Automated pre-flight health check.<br>• Automatic compensating rollback if p99 latency degrades within 60s.<br>• Notification dispatched to Slack `#ops-audit`. |
| **Tier 3** | **High-Blast Destructive Remediation** | • `restart_pod(pod_id, namespace)`<br>• `rollback_deployment(app, rev)`<br>• `flush_redis_cache(cluster)`<br>• `scale_down_service(app, replicas)`<br>• `execute_sql_fix(query)` | **STRICT HUMAN GATE (HITL)** | • Execution halted immediately.<br>• Structured remediation brief generated.<br>• Cryptographic HMAC-SHA256 token issued.<br>• Requires single-click approval from verified on-call engineer within 15 mins. |

---

## 3. The Absolute "NEVER AUTOMATE" Blacklist (5 Red Lines)

The following operations are **strictly prohibited** from ever being proposed or executed by an automated agent, regardless of confidence scores or human approval:

1. **PROHIBITION 1: Drop Database / Truncate Table / Drop Schema**  
   - Any SQL command containing `DROP TABLE`, `TRUNCATE`, `DROP DATABASE`, or `ALTER TABLE ... DROP COLUMN` is permanently blacklisted.
   - Guardrail: Hard regex filter and database user lacking DDL permissions.

2. **PROHIBITION 2: Persistent Volume (PV/PVC) Deletion**  
   - Deleting cloud storage volumes, AWS EBS snapshots, or Kubernetes PVCs is permanently forbidden.

3. **PROHIBITION 3: Root Credential / IAM Policy Modification**  
   - The agent cannot alter IAM roles, rotate root AWS keys, or edit Kubernetes RBAC ClusterRoleBindings.

4. **PROHIBITION 4: Production Direct Git Force-Push**  
   - The agent cannot execute `git push --force` or commit directly to protected `main` / `master` branches without pull request reviews.

5. **PROHIBITION 5: Bypassing Audit Logging or Kill-Switch Disable**  
   - The agent cannot disable its own logging subsystem, alter the audit SQLite database, or bypass the emergency kill switch.

---

## 4. The Cryptographic Human-in-the-Loop Protocol

When a Tier-3 destructive remediation is identified:
1. **Remediation Packaging**: The agent compiles the proposed command, blast radius assessment, expected recovery time, and rollback command.
2. **Token Generation**: The system creates a tamper-evident HMAC-SHA256 signature containing:
   $$\text{HMAC}(\text{IncidentID} \parallel \text{Action} \parallel \text{Parameters} \parallel \text{ExpiresAt}, \text{SecretKey})$$
3. **Delivery**: Delivered to the on-call engineer via Slack interactive button and secure CLI.
4. **Validation**: The command executes **only** if the engineer's cryptographic token is valid and verified within a 15-minute Time-To-Live (TTL) window.
5. **Audit Chaining**: The approval timestamp, engineer ID, and execution output are permanently logged in an immutable SHA-256 audit ledger.

---

## 5. Emergency Kill Switch

- An instantaneous, multi-channel kill switch is deployed at `http://ops-sentinel:8000/kill-switch`.
- When triggered by any engineer, on-call lead, or automated watchdog:
  - All pending and active agent actions are immediately cancelled (`SIGTERM`).
  - The system switches to **100% Manual Fallback Mode**.
  - All alerts bypass the agent and route directly to standard human PagerDuty rotations.

---

## 6. Formal Human-in-the-Loop Boundary Sign-Off

```
================================================================================
                     HUMAN-IN-THE-LOOP BOUNDARY SIGN-OFF
================================================================================

We hereby accept and establish the above 3-Tier Classification, the 5 "Never
Automate" Red Lines, and the Cryptographic Approval Protocol as the binding
operational boundary for the OpsSentinel Autonomous System.

Lead AI Systems Engineer:
  Signature: Harsh Ramesh Nerkar
  Title:     Lead Autonomous AI Systems Architect
  Date:      October 8, 2026

VP of Cloud Infrastructure & Reliability:
  Signature: Marcus Vance
  Title:     VP of Infrastructure & Reliability Engineering
  Date:      October 8, 2026
================================================================================
```
