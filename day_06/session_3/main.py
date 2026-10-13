"""
Day 06 - Session 03: Multi-Step Tool Use & Idempotency
Demonstrates:
  1. Chaining 4 tools sequentially (DB query -> Policy API -> Calculator -> Credit Memo)
  2. Feeding observations back into agent context
  3. Financial idempotency: preventing double-posting on retries
"""

import sqlite3
from dotenv import load_dotenv

load_dotenv()

from database_setup import init_database, DB_PATH
from multi_step_agent import MultiStepIncidentAgent
from tools import record_credit_memo


def main():
    print("=== Day 6 Session 3: Multi-Step Tool Chain & Idempotency ===")
    init_database()
    agent = MultiStepIncidentAgent()

    # 1. Complex incident resolution requiring sequential tools
    prompt = (
        "Process incident INC-8042: look up incident and customer in database, check SLA policy, "
        "compute penalty credit, and record audited credit memo with idempotency."
    )
    print(f"\n1. Executing 4-tool workflow for ticket INC-8042...")
    result = agent.execute_multi_step_workflow(prompt, max_turns=6)

    print(f"   Status:         {result['status']}")
    print(f"   Tools Executed: {' -> '.join(result['tools_executed'])}")
    print(f"   Final Answer:\n   {result['final_answer'].strip()}")

    # 2. Verify financial idempotency (retry must not double-credit)
    print("\n2. Verifying financial idempotency on retry...")
    key = "IDEM-INC-8042-CUST-901"
    replay = record_credit_memo(key, "CUST-901", "INC-8042", 1062.50, "ops-lead@apex.com")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM credit_ledger WHERE idempotency_key = ?;", (key,))
    ledger_count = cursor.fetchone()[0]
    conn.close()

    print(f"   Ledger count for {key}: {ledger_count} (Expected: 1)")
    print(f"   Duplicate prevented: {replay.get('duplicate_prevented')}")


if __name__ == "__main__":
    main()
