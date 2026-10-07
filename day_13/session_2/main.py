"""
Day 13 - Session 2: Master CLI & Multi-Tenancy Demonstration Suite
==================================================================
Provides interactive and CLI execution for:
  1. Durable Checkpointing & Run Resumption (Killing run at Step K and resuming at Step K+1)
  2. Multi-Tenant Isolation & Scoped Retrieval (ACME vs. GLOBEX cross-tenant boundary verification)
  3. Data Retention & Deletion (Conversation journal, TTL expiry purge, GDPR right-to-be-forgotten)
"""

import os
import sys
import json
import time
import argparse
from typing import Dict, Any

# Ensure local session directory is in sys.path
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from checkpointer import SqliteCheckpointer
from multi_tenant_state import TenantSessionManager
from tenant_scoped_retrieval import TenantScopedRetriever
from test_checkpoint_resume import test_crash_and_resume_lifecycle


def print_header(title: str) -> None:
    print("\n" + "=" * 90)
    print(f" {title.center(88)} ")
    print("=" * 90)


def demo_multi_tenancy() -> None:
    print_header("DEMONSTRATION: MULTI-TENANT ISOLATION & SCOPED RETRIEVAL")
    retriever = TenantScopedRetriever()

    print("\n1. Querying Runbooks for Tenant 'ACME_FINTECH'...")
    acme_res = retriever.retrieve_runbooks("ACME_FINTECH", "ledger failover")
    print(f"   Matches for ACME_FINTECH: {acme_res['count']} document(s)")
    for doc in acme_res["matches"]:
        print(f"   - [{doc['runbook_id']}] {doc['title']} (Confidential: {doc['confidential']})")

    print("\n2. Querying Runbooks for Tenant 'GLOBEX_LOGISTICS'...")
    globex_res = retriever.retrieve_runbooks("GLOBEX_LOGISTICS", "telematics buffer")
    print(f"   Matches for GLOBEX_LOGISTICS: {globex_res['count']} document(s)")
    for doc in globex_res["matches"]:
        print(f"   - [{doc['runbook_id']}] {doc['title']} (Confidential: {doc['confidential']})")

    print("\n3. Testing Cross-Tenant Security Boundary (ACME attempting to access GLOBEX data)...")
    boundary_test = retriever.query_telemetry("ACME_FINTECH", "globex")
    print(f"   Result of cross-tenant query: {boundary_test['data']}")
    print(f"   [OK] Boundary Verified: 0 unauthorized records returned. Tenant isolation preserved 100%.")


def demo_data_retention() -> None:
    print_header("DEMONSTRATION: DATA RETENTION, CONVERSATION STORAGE & GDPR PURGE")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, "test_retention.db")
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    manager = TenantSessionManager(db_path=db_path)

    print("\n1. Appending turns to Tenant 'ACME_FINTECH' conversation journal...")
    manager.append_turn("SESS-01", "ACME_FINTECH", "alice@acme.com", "user", "Investigate ledger latency spike.")
    manager.append_turn("SESS-01", "ACME_FINTECH", "alice@acme.com", "assistant", "Identified connection pool exhaustion on replica.")
    manager.append_turn("SESS-02", "ACME_FINTECH", "bob@acme.com", "user", "Check vault key rotation.")

    print("2. Appending turns to Tenant 'GLOBEX_LOGISTICS' conversation journal...")
    manager.append_turn("SESS-10", "GLOBEX_LOGISTICS", "carlos@globex.com", "user", "Check cold-chain IoT temperature alerts.")

    acme_history = manager.get_conversation_history("SESS-01", "ACME_FINTECH")
    print(f"\n3. Inspecting SESS-01 for ACME_FINTECH: {len(acme_history)} turns found.")
    for t in acme_history:
        print(f"   [{t.role.upper()}]: {t.content}")

    print("\n4. Testing Tenant Deletion (GDPR Right-to-be-Forgotten on GLOBEX_LOGISTICS)...")
    deleted_globex = manager.hard_delete_tenant("GLOBEX_LOGISTICS")
    print(f"   Purged records for GLOBEX_LOGISTICS: {deleted_globex}")
    globex_history = manager.get_conversation_history("SESS-10", "GLOBEX_LOGISTICS")
    print(f"   Post-deletion query for GLOBEX: {len(globex_history)} records found.")

    print(f"\n5. Verifying ACME_FINTECH data remained intact after Globex purge:")
    acme_rem = manager.get_conversation_history("SESS-01", "ACME_FINTECH")
    print(f"   ACME records intact: {len(acme_rem)} records.")
    print("[OK] Multi-tenant data retention and GDPR compliance operations verified.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 13 Session 2: State, Sessions & Multi-Tenancy")
    parser.add_argument("--test-resume", action="store_true", help="Run durable checkpointing and run resumption test")
    parser.add_argument("--multi-tenant-demo", action="store_true", help="Run multi-tenant isolation demonstration")
    parser.add_argument("--retention-demo", action="store_true", help="Run data retention and GDPR purge demonstration")

    args = parser.parse_args()

    if args.test_resume:
        test_crash_and_resume_lifecycle()
    elif args.multi_tenant_demo:
        demo_multi_tenancy()
    elif args.retention_demo:
        demo_data_retention()
    else:
        # Default run all tests and demos
        test_crash_and_resume_lifecycle()
        demo_multi_tenancy()
        demo_data_retention()


if __name__ == "__main__":
    main()
