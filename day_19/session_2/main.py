"""CLI Entry Point for Day 19 Session 2: Break Your Own System.

Usage:
    python main.py --table
    python main.py --run-chaos
    python main.py --vector FM-01
"""

import argparse
import json
import os
import sys

from adversarial_chaos_engine import ChaosHarness


def print_banner() -> None:
    print("=" * 85)
    print("   OPS-SENTINEL AI ENTERPRISE — DAY 19 S2: ADVERSARIAL CHAOS TEST HARNESS")
    print("=" * 85)


def display_table() -> None:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "FAILURE_MODE_DATA.json")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print_banner()
    print(f"{'ID':<6} | {'Attack Vector':<32} | {'Blast Radius':<10} | {'Status':<7} | {'Defense Mechanism'}")
    print("-" * 85)
    for fm in data.get("failure_modes", []):
        print(f"{fm['id']:<6} | {fm['vector_name']:<32} | {fm['blast_radius'].split()[0]:<10} | {fm['status']:<7} | {fm['guardrail_implemented'][:30]}...")
    print("=" * 85)


def run_chaos_suite(target_vector: str = None) -> None:
    print_banner()
    harness = ChaosHarness()
    results = harness.run_all_vectors()

    if target_vector:
        results = [r for r in results if r.vector_id.upper() == target_vector.upper()]
        if not results:
            print(f"[!] Error: Vector '{target_vector}' not found. Available: FM-01 to FM-06")
            sys.exit(1)

    print(f"Executing {len(results)} Adversarial Chaos Scenarios...\n")
    all_passed = True
    for r in results:
        status_sym = "[✓] CONTAINED" if r.contained else "[✗] BREACHED"
        if not r.contained:
            all_passed = False
        print(f"{status_sym} [{r.vector_id}] {r.vector_name}")
        print(f"      Attack Input : {r.attack_input[:60]}...")
        print(f"      Agent Action : {r.agent_response}")
        print(f"      Mitigation   : {r.mitigation}\n")

    print("-" * 85)
    if all_passed:
        print("[✓] ALL ADVERSARIAL CHAOS ATTACKS SAFELY CONTAINED (6/6). ZERO CRASHES.")
    else:
        print("[✗] ONE OR MORE CHAOS ATTACKS CAUSED UNHANDLED FAILURE.")
    print("=" * 85)
    sys.exit(0 if all_passed else 1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 19 Session 2 Adversarial Chaos CLI")
    parser.add_argument("--table", action="store_true", help="Display 8-column failure mode matrix")
    parser.add_argument("--run-chaos", action="store_true", help="Execute all 6 chaos test vectors")
    parser.add_argument("--vector", type=str, help="Execute specific failure mode (FM-01 through FM-06)")

    args = parser.parse_args()

    if args.table:
        display_table()
    elif args.vector:
        run_chaos_suite(args.vector)
    elif args.run_chaos:
        run_chaos_suite()
    else:
        # Default: display table and run chaos
        display_table()
        print("\n")
        run_chaos_suite()


if __name__ == "__main__":
    main()
