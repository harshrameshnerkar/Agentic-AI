# Day 13 - Session 2: State, Sessions & Multi-Tenancy

Welcome to **Session 2** of **Day 13** in the **Agentic AI Engineering Curriculum**.

This session establishes production durability and multi-tenancy for the Capstone OpsSentinel SRE Agent, implementing **LangGraph-style durable checkpointing**, **crash-resilient run resumption**, **tenant-scoped retrieval**, and **GDPR/TTL data retention policies**.

---

## 1. Architectural Highlights

### Durable Checkpointing & Resumption Lifecycle
In mission-critical agentic systems, worker nodes crash, pods are evicted due to spot instance preemption, or network partitions disconnect long-running runs. Without checkpointing, restarting from Step 0 re-executes destructive or expensive tools (e.g. restarts, cloud queries, LLM token bills).

```
[ Step 1: Intake ] ──> Commit Checkpoint 1 (SQLite)
          │
[ Step 2: Diagnose ] ──> Commit Checkpoint 2 (SQLite)
          │
[ Step 3: Execute Tools ] ──> Commit Checkpoint 3 (SQLite)
          │
    💥 [ PROCESS CRASH / UNHANDLED SIGKILL / OOM ]
          │
    🔄 [ COLD POD RESTART & RECOVERY ]
          │
Load Latest Checkpoint (Step 3: Execute Tools)
          │
[ Step 4: Synthesize ] (Resumes directly without re-running Steps 1-3!)
          │
[ Step 5: Resolve ] ──> Commit Checkpoint 5 (Incident Resolved)
```

---

## 2. Checkpoint Resumption Verification Results

Verified via automated test suite (`test_checkpoint_resume.py`):

```text
===============================================================================================
            DAY 13 - SESSION 2: DURABLE CHECKPOINTING & RUN RESUMPTION VERIFICATION            
===============================================================================================

[PART 1: RUN INITIATION] Starting Agent Run for Session 'SESSION-PROD-INC-842'...
  - Tenant ID: ACME_FINTECH
  - User ID  : oncall-alice@acme.internal
  - Query    : 'Acme high-frequency ledger failover protocol triggered.'
  - Injected Kill Condition: CRASH IMMEDIATELY AFTER STEP 3 (EXECUTE_TOOLS)

  [ALERT] [SIMULATED CRASH] Agent process crashed/killed at Step 3 (EXECUTE_TOOLS)! Checkpoint CHK-79A46AB8DB0A saved to SQLite.

[PART 2: STATE AUDIT IN SQLITE] Inspecting Checkpoint Database (3 records found):
-----------------------------------------------------------------------------------------------
| Step | Node Name     | Checkpoint ID      | Tools Executed | State Preserved |
-----------------------------------------------------------------------------------------------
|   1  | INTAKE        | CHK-F2232BB91573   |              0 | [YES] SQLite Committed |
|   2  | DIAGNOSE      | CHK-3D8493927D9E   |              0 | [YES] SQLite Committed |
|   3  | EXECUTE_TOOLS | CHK-79A46AB8DB0A   |              2 | [YES] SQLite Committed |
-----------------------------------------------------------------------------------------------

[PART 3: COLD RESTART] Spawning new Agent instance (simulating recovered pod)...
[PART 3: RESUME] Invoking resume_run('SESSION-PROD-INC-842', 'ACME_FINTECH')...

[PART 4: RESUMPTION VERIFICATION RESULTS]:
  - Resumed Starting Step        : Step 4 (SYNTHESIZE)
  - Final Execution Status       : RESOLVED
  - Steps Recorded in History    : STEP_1_INTAKE, STEP_2_DIAGNOSE, STEP_3_EXECUTE_TOOLS, STEP_4_SYNTHESIZE, STEP_5_RESOLVE
  - Prior Step Re-executions     : ZERO (Steps 1..3 skipped on resumption)
  - State & Tools Recovered      : 100% Fidelity from SQLite
-----------------------------------------------------------------------------------------------
[PASS] DURABLE CHECKPOINTING VERIFIED: Killed run resumed from last step without restarting!
===============================================================================================
```

---

## 3. Multi-Tenancy & Data Retention

1. **Tenant-Scoped Partitioning**: All database records, sessions, and state checkpoints are indexed by `(tenant_id, session_id)`.
2. **Tenant-Scoped Retrieval (`tenant_scoped_retrieval.py`)**: Knowledge bases and telemetry stores are segregated at the data layer. Any cross-tenant query (e.g., Acme trying to read Globex Logistics runbooks) returns zero results and triggers a boundary violation alert.
3. **Conversation Journaling (`multi_tenant_state.py`)**: Append-only storage of all chat and tool turns.
4. **Data Retention & GDPR Purge**:
   - `purge_expired_sessions(max_age_seconds)` automatically deletes sessions exceeding corporate TTL.
   - `hard_delete_tenant(tenant_id)` executes right-to-be-forgotten purges across all tables while leaving other tenants' data intact.

---

## 4. How to Run

```powershell
# 1. Run the Crash & Resumption Test
python day_13/session_2/main.py --test-resume

# 2. Run the Multi-Tenant Isolation Demonstration
python day_13/session_2/main.py --multi-tenant-demo

# 3. Run the Data Retention & GDPR Deletion Demonstration
python day_13/session_2/main.py --retention-demo

# 4. Run all Session 2 demonstrations
python day_13/session_2/main.py
```
