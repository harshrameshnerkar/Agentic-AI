"""
Day 6 - Session 3: Multi-Step Tool Use
Master Demonstration: main.py

Learning Objectives:
1. Chaining Calls: Output of Tool N strictly feeds into Tool N+1.
2. Feeding Results Back into Context: Role='tool' observations enable the next turn reasoning.
3. Conversation History Growth: Tracking token expansion turn-by-turn.
4. When to Summarise or Truncate: Mitigating context bloat through payload truncation and compaction.
5. Partial Failure Handling & Recovery: Graceful fallback observations.
6. Idempotency: Proof that side-effecting financial actions cannot duplicate on retry.

Task:
Ask a question requiring 4 sequential tools and log every thought, action, and observation.
"""

from __future__ import annotations
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import os
import json
import time
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

# Ensure local .env takes absolute priority
load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

# Ensure local imports work reliably
sys.path.insert(0, str(Path(__file__).resolve().parent))

from database_setup import init_database, DB_PATH
from multi_step_agent import MultiStepIncidentAgent
from tools import record_credit_memo


def print_banner(title: str):
    print("\n" + "=" * 80, flush=True)
    print(f" {title}", flush=True)
    print("=" * 80, flush=True)


def test_idempotency_protection(ticket_id: str, customer_id: str, credit_amount: float, manager_email: str):
    """
    Demonstrates side-effect protection: re-issuing a financial transaction with the
    same idempotency key guarantees that no duplicate crediting or double-posting occurs.
    """
    print_banner("PHASE 2: VERIFYING IDEMPOTENCY SAFETY UNDER RETRIES")
    idempotency_key = f"IDEM-{ticket_id}-{customer_id}"

    print(f"[Simulation] Re-sending the same settlement request to record_credit_memo with key: '{idempotency_key}'...", flush=True)
    replay_result = record_credit_memo(
        idempotency_key=idempotency_key,
        customer_id=customer_id,
        ticket_id=ticket_id,
        net_credit_usd=credit_amount,
        manager_email=manager_email
    )

    print("\n--- Replay Call Observation ---", flush=True)
    print(json.dumps(replay_result, indent=2), flush=True)

    # Verify against database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM credit_ledger WHERE idempotency_key = ?;", (idempotency_key,))
    ledger_entries = cursor.fetchone()[0]

    cursor.execute("SELECT credit_balance_usd FROM customers WHERE customer_id = ?;", (customer_id,))
    final_balance = cursor.fetchone()[0]
    conn.close()

    print("\n--- Idempotency Ledger Audit Verification ---", flush=True)
    print(f"  • Total Ledger Records for Key '{idempotency_key}': {ledger_entries} (Must equal exactly 1!)")
    print(f"  • Duplicate Prevented Flag: {replay_result.get('duplicate_prevented')}")
    print(f"  • Idempotent Replay Flag: {replay_result.get('idempotent_replay')}")
    print(f"  • Final Customer Account Balance: ${final_balance:,.2f}")

    assert ledger_entries == 1, "IDEMPOTENCY FAILURE: Multiple records created in ledger!"
    assert replay_result.get("idempotent_replay") is True, "IDEMPOTENCY FAILURE: Replay not detected!"
    print("  ✅ IDEMPOTENCY CONTRACT VERIFIED: ZERO DOUBLE-CREDITING!", flush=True)


def display_history_growth_audit(history_growth: list):
    """Prints a structured audit table of token expansion across the turns."""
    print_banner("PHASE 3: CONVERSATION HISTORY GROWTH & TOKEN TELEMETRY")
    print(f"{'Turn':<6} | {'Messages':<10} | {'Total Chars':<14} | {'Est. Tokens':<14} | {'Compaction Flag'}")
    print("-" * 70)
    for idx, metric in enumerate(history_growth, 1):
        print(
            f"{idx:<6} | {metric['message_count']:<10} | {metric['total_chars']:<14} | "
            f"{metric['estimated_tokens']:<14} | {metric['compaction_recommended']}"
        )
    print("-" * 70)
    print("Insight: As observations feed back into context, prompt size expands linearly.")
    print("Intelligent truncation and compaction prevent context overflow during 10+ step workflows.")


def main():
    print_banner("DAY 6 - SESSION 3: MULTI-STEP TOOL USE MASTER RUN")

    # Step 0: Initialize database
    init_database()

    # Step 1: Instantiate multi-step agent
    agent = MultiStepIncidentAgent()

    # Step 2: The complex user question requiring 4 sequential tools
    sequential_prompt = (
        "Process critical incident ticket INC-8042: look up the incident details and impacted customer "
        "from our database, check the live SLA policy and compensation formula via our policy API, "
        "compute the exact penalty credit and service waiver adjustment, and record the audited credit memo "
        "with idempotency protection. Report every detail."
    )

    print_banner("PHASE 1: EXECUTING 4-TOOL SEQUENTIAL CHAIN WITH REACT LOGGING")
    result = agent.execute_multi_step_workflow(user_prompt=sequential_prompt, max_turns=6)

    print_banner("WORKFLOW RESOLUTION SUMMARY")
    print(f"Status: {result['status']}")
    print(f"Turns Taken: {result['turns_taken']}")
    print(f"Total Latency: {result['total_duration_sec']:.2f}s")
    print(f"Tools Executed in Sequence: {' -> '.join(result['tools_executed'])}")

    print("\n--- Final Executive Settlement Summary ---")
    print(result["final_answer"])

    # Step 3: Test Idempotency under simulated retry
    test_idempotency_protection(
        ticket_id="INC-8042",
        customer_id="CUST-901",
        credit_amount=1062.50,
        manager_email="ops-lead@apexlogistics.com"
    )

    # Step 4: Display Context Growth Telemetry
    display_history_growth_audit(result["history_growth"])

    print_banner("DAY 6 - SESSION 3: VERIFICATION COMPLETE")
    print("""
Key Principles Proven:
  [✓] Chaining Calls: Tool 1 output fed into Tool 2 -> Tool 3 -> Tool 4 in strict sequence.
  [✓] Feeding Results into Context: Observations passed via role='tool' messages.
  [✓] Conversation History Growth: Token expansion audited per turn.
  [✓] When to Summarise/Truncate: Compaction triggers protect context windows.
  [✓] Idempotency: Re-submitting financial mutations returned cached receipts with zero double-charge.
""", flush=True)


if __name__ == "__main__":
    main()
