"""CLI Entry Point for Day 19 Session 4: Clean-Clone Sandbox Verification.

Usage:
    python main.py --summary
    python main.py --run-test
    python main.py --doc-bugs
"""

import argparse
import json
import os
import sys

from clean_clone_runner import CleanCloneSandboxRunner


def print_banner() -> None:
    print("=" * 80)
    print("   OPS-SENTINEL AI ENTERPRISE — DAY 19 S4: CLEAN-CLONE AUDIT RUNNER")
    print("=" * 80)


def display_doc_bugs() -> None:
    runner = CleanCloneSandboxRunner()
    meta = runner.load_audit_metadata()
    bugs = meta.get("documentation_bugs_found", [])

    print_banner()
    print(f"DOCUMENTATION BUGS CAUGHT & RESOLVED DURING UNAIDED TRIAL ({len(bugs)} Items):\n")
    for b in bugs:
        print(f"  • [{b['id']}] Severity: {b['severity']:<6} | Status: {b['status']}")
        print(f"    Issue : {b['description']}")
        print(f"    Fix   : {b['resolution']}\n")
    print("=" * 80)


def run_simulation() -> None:
    print_banner()
    runner = CleanCloneSandboxRunner()
    result = runner.run_sandbox_simulation()

    status_sym = "[✓] SUCCESS" if result.is_success else "[✗] FAILURE"
    print(f"Sandbox Simulation Status : {status_sym}")
    print(f"Files Audited in Day 19   : {result.files_audited} files")
    print(f"Blocking Prompts (input()): {result.interactive_prompts_found} (Required: 0)")
    print(f"Doc Bugs Cataloged/Fixed  : {result.doc_bugs_resolved}")
    print(f"Simulated Setup Time      : {result.setup_duration_sec}s")
    print(f"Regression Pass Rate      : {result.eval_pass_rate}%")
    print(f"Final Audit Verdict       : {result.verdict}")
    print("-" * 80)
    if result.is_success:
        print("[✓] CLEAN-CLONE AUDIT PASSED. ZERO UNAIDED DEPENDENCY ISSUES.")
    else:
        print("[✗] CLEAN-CLONE AUDIT FAILED.")
    print("=" * 80)
    sys.exit(0 if result.is_success else 1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 19 Session 4 Clean-Clone Runner CLI")
    parser.add_argument("--summary", action="store_true", help="Display audit summary")
    parser.add_argument("--run-test", action="store_true", help="Run clean clone sandbox simulation")
    parser.add_argument("--doc-bugs", action="store_true", help="Display cataloged documentation bugs")

    args = parser.parse_args()

    if args.doc_bugs:
        display_doc_bugs()
    elif args.run_test:
        run_simulation()
    else:
        # Default: display doc bugs and run simulation
        display_doc_bugs()
        print("\n")
        run_simulation()


if __name__ == "__main__":
    main()
