"""
Day 15 - Session 01: OpsSentinel Enterprise SRE Copilot CLI
Command-line interface to execute SRE queries, inspect checkpoints,
and verify cryptographic audit trail integrity.
"""

from __future__ import annotations
import argparse
import asyncio
import sys
from pathlib import Path

_script_dir = Path(__file__).resolve().parent
_workspace_root = _script_dir.parent.parent
if str(_workspace_root) not in sys.path:
    sys.path.insert(0, str(_workspace_root))

from day_15.session_1.async_engine import AsyncAgentEngine
from day_15.session_1.durable_state import DurableStateCheckpointer
from day_15.session_1.hitl_gateway import HITLApprovalGateway, AuditTrailLogger


def parse_args():
    parser = argparse.ArgumentParser(description="OpsSentinel Enterprise SRE Copilot CLI")
    parser.add_argument("--query", "-q", type=str, help="SRE inquiry or diagnostic query")
    parser.add_argument("--session", "-s", type=str, help="Session ID to inspect or resume")
    parser.add_argument("--approve", type=str, help="Approval ID to authorize")
    parser.add_argument("--operator", type=str, default="sre-operator", help="Operator ID")
    parser.add_argument("--list-sessions", action="store_true", help="List active sessions")
    parser.add_argument("--audit-check", action="store_true", help="Verify cryptographic audit chain")
    return parser.parse_args()


async def async_main():
    args = parse_args()
    checkpointer = DurableStateCheckpointer()
    audit_logger = AuditTrailLogger()
    approval_gateway = HITLApprovalGateway(audit_logger)
    engine = AsyncAgentEngine(checkpointer, approval_gateway, audit_logger)

    if args.audit_check:
        valid = audit_logger.verify_integrity()
        print(f"Cryptographic SHA-256 chain integrity: {'VALID (Intact)' if valid else 'COMPROMISED'}")
        return

    if args.list_sessions:
        sessions = checkpointer.list_active_sessions(limit=10)
        print(f"\nActive Sessions ({len(sessions)}):")
        for s in sessions:
            print(f"  [{s['status']}] {s['session_id']}: {s['query'][:50]}")
        return

    if args.approve and args.session:
        print(f"Authorizing approval {args.approve} for session {args.session}...")
        approval_gateway.approve(args.approve, args.operator, "Approved via CLI")
        res = await engine.resume_after_approval(args.session, args.approve, args.operator)
        print(f"Status: {res.status.value} ({res.latency_ms:.1f}ms)")
        print(res.final_output)
        return

    query = args.query
    if not query and not sys.stdin.isatty():
        query = "Inspect telemetry status for payment-api service."

    if query:
        print(f"\nRunning Query: '{query}'")
        res = await engine.run(query, session_id=args.session)
        print(f"Category: {res.routing_category} | Status: {res.status.value} ({res.latency_ms:.1f}ms)")
        print(f"\nResponse:\n{res.final_output}")
        if res.pending_approval:
            print(f"Pending Approval ID: {res.pending_approval['approval_id']}")
        return

    # Interactive Shell
    print("OpsSentinel Enterprise Interactive Shell (type 'exit' to quit)\n")
    while True:
        try:
            line = input("ops-sentinel> ").strip()
            if not line or line.lower() in ["exit", "quit", "q"]:
                break
            res = await engine.run(line)
            print(f"[{res.routing_category}] ({res.latency_ms:.1f}ms):\n{res.final_output}\n")
        except (KeyboardInterrupt, EOFError):
            break


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
