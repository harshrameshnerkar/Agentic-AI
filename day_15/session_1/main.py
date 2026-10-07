"""
Command-Line Interface (CLI) for OpsSentinel Enterprise (Day 15).
Allows direct execution of queries, session inspection, and health auditing from terminal.
"""

import argparse
import asyncio
import sys
import json
from pathlib import Path

_script_dir = Path(__file__).resolve().parent
_workspace_root = _script_dir.parent.parent
if str(_workspace_root) not in sys.path:
    sys.path.insert(0, str(_workspace_root))

from day_15.session_1.config import config
from day_15.session_1.async_engine import AsyncAgentEngine
from day_15.session_1.durable_state import DurableStateCheckpointer
from day_15.session_1.hitl_gateway import HITLApprovalGateway, AuditTrailLogger

def parse_args():
    parser = argparse.ArgumentParser(description="OpsSentinel Enterprise SRE Copilot CLI")
    parser.add_argument("--query", "-q", type=str, help="Run an SRE inquiry, diagnostic, or remediation command")
    parser.add_argument("--session", "-s", type=str, help="Session ID to inspect or resume")
    parser.add_argument("--approve", type=str, help="Approval ID to authorize")
    parser.add_argument("--operator", type=str, default="sre-cli-operator", help="Operator ID for approval")
    parser.add_argument("--list-sessions", action="store_true", help="List active checkpointed sessions")
    parser.add_argument("--audit-check", action="store_true", help="Verify cryptographic audit chain integrity")
    return parser.parse_args()

async def async_main():
    args = parse_args()

    checkpointer = DurableStateCheckpointer()
    audit_logger = AuditTrailLogger()
    approval_gateway = HITLApprovalGateway(audit_logger)
    engine = AsyncAgentEngine(checkpointer, approval_gateway, audit_logger)

    if args.audit_check:
        valid = audit_logger.verify_integrity()
        print(f"[AUDIT] Cryptographic SHA-256 chain integrity: {'VALID (Intact)' if valid else 'COMPROMISED'}")
        return

    if args.list_sessions:
        sessions = checkpointer.list_active_sessions(limit=20)
        print(f"\n--- ACTIVE SESSIONS ({len(sessions)}) ---")
        for s in sessions:
            print(f"[{s['status']}] {s['session_id']} (Step {s['current_step']}): {s['query'][:60]}")
        print("------------------------------------------\n")
        return

    if args.approve and args.session:
        print(f"\n[APPROVAL] Authorizing {args.approve} for session {args.session} by {args.operator}...")
        approval_gateway.approve(args.approve, args.operator, "Approved via CLI")
        res = await engine.resume_after_approval(args.session, args.approve, args.operator)
        print(f"[RESULT] Status: {res.status.value} ({res.latency_ms:.1f}ms)")
        print(res.final_output)
        return

    if args.query:
        print(f"\n[QUERY] Submitting: '{args.query}'")
        res = await engine.run(args.query, session_id=args.session)
        print(f"[COMPLETED] Category: {res.routing_category} | Status: {res.status.value} | Latency: {res.latency_ms:.1f}ms")
        print(f"[OUTPUT]\n{res.final_output}\n")
        if res.pending_approval:
            print(f"[PENDING APPROVAL] Approval ID: {res.pending_approval['approval_id']}")
        return

    # Interactive Prompt
    print("=======================================================")
    print("🛡️  OpsSentinel Enterprise SRE Interactive Shell")
    print("Type your query or 'exit' to quit.")
    print("=======================================================\n")

    while True:
        try:
            line = input("ops-sentinel> ").strip()
            if not line:
                continue
            if line.lower() in ["exit", "quit", "q"]:
                break
            res = await engine.run(line)
            print(f"\n--- [{res.routing_category}] ({res.latency_ms:.1f}ms) ---")
            print(res.final_output)
            print("-------------------------------------------------------\n")
        except (KeyboardInterrupt, EOFError):
            break

def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
