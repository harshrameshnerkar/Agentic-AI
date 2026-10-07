"""
Day 13 - Session 2: Checkpoint & Run Resumption Verification Test
=================================================================
Automated verification proving:
  1. An agent run killed mid-execution (e.g. Step 3) saves its exact state to SQLite.
  2. A cold-started agent resumes from Step 4 rather than restarting from Step 1.
  3. Completed tools and prior steps are NEVER re-executed (zero duplicated side-effects).
  4. The run successfully reaches final incident resolution.
"""

import os
import sys
import json
import time
from typing import Dict, Any

# Ensure local session directory is in sys.path
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from checkpointer import SqliteCheckpointer
from resilient_agent import ResilientGraphAgent, SimulatedCrashException


def test_crash_and_resume_lifecycle() -> Dict[str, Any]:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_db = os.path.join(current_dir, "test_checkpoints.db")
    if os.path.exists(test_db):
        try:
            os.remove(test_db)
        except Exception:
            pass

    checkpointer = SqliteCheckpointer(db_path=test_db)
    agent = ResilientGraphAgent(checkpointer=checkpointer)

    session_id = "SESSION-PROD-INC-842"
    tenant_id = "ACME_FINTECH"
    user_id = "oncall-alice@acme.internal"
    query = "Acme high-frequency ledger failover protocol triggered. Check replica database and route traffic."

    print("\n" + "=" * 95)
    print(" DAY 13 - SESSION 2: DURABLE CHECKPOINTING & RUN RESUMPTION VERIFICATION ".center(95))
    print("=" * 95)

    # -------------------------------------------------------------------------
    # PART 1: INITIATE RUN & SIMULATE HARD PROCESS KILL AT STEP 3
    # -------------------------------------------------------------------------
    print(f"\n[PART 1: RUN INITIATION] Starting Agent Run for Session '{session_id}'...")
    print(f"  - Tenant ID: {tenant_id}")
    print(f"  - User ID  : {user_id}")
    print(f"  - Query    : '{query}'")
    print(f"  - Injected Kill Condition: CRASH IMMEDIATELY AFTER STEP 3 (EXECUTE_TOOLS)")

    crash_occurred = False
    try:
        agent.run(
            session_id=session_id,
            tenant_id=tenant_id,
            user_id=user_id,
            query=query,
            kill_at_step=3,
        )
    except SimulatedCrashException as crash_err:
        crash_occurred = True
        print(f"\n  [ALERT] {crash_err}")

    assert crash_occurred, "Test failure: Agent was expected to crash at Step 3."

    # Inspect Checkpoint Store
    checkpoints = checkpointer.list_checkpoints(session_id, tenant_id)
    print(f"\n[PART 2: STATE AUDIT IN SQLITE] Inspecting Checkpoint Database ({len(checkpoints)} records found):")
    print("-" * 95)
    print(f"| Step | Node Name     | Checkpoint ID      | Tools Executed | State Preserved |")
    print("-" * 95)
    for chk in checkpoints:
        tools_cnt = len(chk.state.get("tool_results", []))
        print(
            f"|   {chk.step_index:<2} | {chk.node_name:<13} | {chk.checkpoint_id:<18} | "
            f"{tools_cnt:>14} | [YES] SQLite Committed |"
        )
    print("-" * 95)

    assert len(checkpoints) == 3, f"Expected exactly 3 checkpoints, found {len(checkpoints)}"
    latest_chk = checkpointer.load_latest(session_id, tenant_id)
    assert latest_chk is not None
    assert latest_chk.step_index == 3
    assert latest_chk.node_name == "EXECUTE_TOOLS"
    print(f"  -> Latest Checkpoint Verified: Step 3 ({latest_chk.node_name})")

    # -------------------------------------------------------------------------
    # PART 3: COLD-START RECOVERY & RESUME EXECUTION
    # -------------------------------------------------------------------------
    print("\n[PART 3: COLD RESTART] Spawning new Agent instance (simulating recovered pod)...")
    recovered_agent = ResilientGraphAgent(checkpointer=checkpointer)

    print(f"[PART 3: RESUME] Invoking resume_run('{session_id}', '{tenant_id}')...")
    final_state, resumed_at_step = recovered_agent.resume_run(session_id, tenant_id)

    print(f"\n[PART 4: RESUMPTION VERIFICATION RESULTS]:")
    print(f"  - Resumed Starting Step        : Step {resumed_at_step} ({final_state.current_node})")
    print(f"  - Final Execution Status       : {'RESOLVED' if final_state.is_resolved else 'UNRESOLVED'}")
    print(f"  - Steps Recorded in History    : {', '.join(final_state.steps_executed)}")
    print(f"  - Root Cause Formulated        : {final_state.root_cause_hypothesis}")
    print(f"  - Remediation Action           : {final_state.remediation_action}")
    print(f"  - Runbook Citation             : {final_state.runbook_citation}")

    # Verifications
    assert resumed_at_step == 4, f"Expected resumption at Step 4, resumed at {resumed_at_step}"
    assert final_state.is_resolved, "Expected final state to be resolved."
    # Ensure Step 1, 2, 3 were executed only once!
    assert final_state.steps_executed.count("STEP_1_INTAKE") == 1
    assert final_state.steps_executed.count("STEP_2_DIAGNOSE") == 1
    assert final_state.steps_executed.count("STEP_3_EXECUTE_TOOLS") == 1
    assert final_state.steps_executed.count("STEP_4_SYNTHESIZE") == 1
    assert final_state.steps_executed.count("STEP_5_RESOLVE") == 1

    all_checkpoints = checkpointer.list_checkpoints(session_id, tenant_id)
    print(f"  - Total Lifetime Checkpoints   : {len(all_checkpoints)} (Steps 1 -> 2 -> 3 -> 4 -> 5)")

    print("-" * 95)
    print("[PASS] DURABLE CHECKPOINTING VERIFIED: Killed run resumed from last step without restarting!")
    print("=" * 95)

    return {
        "session_id": session_id,
        "tenant_id": tenant_id,
        "killed_at_step": 3,
        "resumed_at_step": resumed_at_step,
        "steps_executed_order": final_state.steps_executed,
        "is_resolved": final_state.is_resolved,
        "total_checkpoints": len(all_checkpoints),
        "status": "PASS",
    }


if __name__ == "__main__":
    test_crash_and_resume_lifecycle()
