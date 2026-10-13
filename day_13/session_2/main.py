"""
Day 13 - Session 02: Multi-Tenant State & Crash Resumption
Demonstrates:
1. Multi-tenant isolation: strictly scoped retrieval per tenant boundary.
2. Durable checkpointing: surviving mid-run process crashes and resuming at step K+1.
3. Data retention and GDPR deletion.
"""

from __future__ import annotations
from tenant_scoped_retrieval import TenantScopedRetriever
from test_checkpoint_resume import test_crash_and_resume_lifecycle


def demo_multi_tenancy():
    print("\n--- 1. Multi-Tenant Scoped Retrieval ---")
    retriever = TenantScopedRetriever()

    acme = retriever.retrieve_runbooks("ACME_FINTECH", "ledger")
    print(f"ACME_FINTECH matches: {acme['count']} runbook(s)")

    globex = retriever.retrieve_runbooks("GLOBEX_LOGISTICS", "telematics")
    print(f"GLOBEX_LOGISTICS matches: {globex['count']} runbook(s)")

    # Boundary test: ACME query trying to access GLOBEX data
    boundary = retriever.query_telemetry("ACME_FINTECH", "globex")
    print(f"Cross-tenant access attempt: {len(boundary['data'])} records returned (0 expected)")
    assert len(boundary["data"]) == 0
    print("Pass: Multi-tenant boundary enforced.")


def main():
    print("Day 13 Session 02: Resilient Multi-Tenant Agent State\n")
    demo_multi_tenancy()

    print("\n--- 2. Durable Checkpoint & Crash Resumption Test ---")
    test_crash_and_resume_lifecycle()
    print("Pass: Crash at step K resumed cleanly at step K+1.")


if __name__ == "__main__":
    main()
