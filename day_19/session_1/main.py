"""CLI entry point for Day 19 Session 1: Standup & Feature Freeze.

Usage:
    python main.py --summary
    python main.py --audit
    python main.py --check-commit "feat: add discord bot"
    python main.py --check-task "HARDENING"
"""

import argparse
import json
import os
import sys

from freeze_auditor import FeatureFreezeAuditor


def print_banner() -> None:
    print("=" * 80)
    print("    OPS-SENTINEL AI ENTERPRISE — DAY 19 S1: FEATURE FREEZE AUDITOR")
    print("=" * 80)


def display_summary(auditor: FeatureFreezeAuditor) -> None:
    print_banner()
    state = auditor.audit_system_state()
    print(f"Status           : {state['policy_status']}")
    print(f"Release Tag      : {state['release_tag']}")
    print(f"Baseline Commit  : {state['baseline_commit']}")
    print(f"Zero-Feature Rule: {'ENFORCED' if state['zero_new_features_enforced'] else 'DISABLED'}")
    print(f"Policy SHA-256   : {state['policy_sha256'][:16]}...")
    print("-" * 80)
    print("Approved Day 19 Work Backlog:")
    for task in auditor.policy.approved_backlog:
        print(f"  • [{task['id']}] {task['title']} ({task['category']}) -> {task['status']}")
    print("-" * 80)
    print("Allowed Commit Prefixes: " + ", ".join(auditor.policy.allowed_prefixes))
    print("Disallowed Prefixes    : " + ", ".join(auditor.policy.disallowed_prefixes))
    print("=" * 80)


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 19 Feature Freeze CLI")
    parser.add_argument("--summary", action="store_true", help="Display freeze summary")
    parser.add_argument("--audit", action="store_true", help="Run full policy audit")
    parser.add_argument("--check-commit", type=str, help="Validate commit message against freeze rules")
    parser.add_argument("--check-task", type=str, help="Validate task category against freeze rules")

    args = parser.parse_args()
    auditor = FeatureFreezeAuditor()

    if args.check_commit:
        allowed, reason = auditor.is_commit_allowed(args.check_commit)
        status_sym = "[✓]" if allowed else "[✗]"
        print(f"{status_sym} Commit: '{args.check_commit}'")
        print(f"    Result: {reason}")
        sys.exit(0 if allowed else 1)

    if args.check_task:
        allowed, reason = auditor.is_task_allowed(args.check_task)
        status_sym = "[✓]" if allowed else "[✗]"
        print(f"{status_sym} Task Category: '{args.check_task}'")
        print(f"    Result: {reason}")
        sys.exit(0 if allowed else 1)

    if args.audit:
        state = auditor.audit_system_state()
        print(json.dumps(state, indent=2))
        return

    # Default to summary
    display_summary(auditor)


if __name__ == "__main__":
    main()
