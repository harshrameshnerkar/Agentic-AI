"""
Day 19 - Session 02: Break Your Own System (Adversarial Chaos Suite)
Executes red-teaming chaos scenarios against the system to verify that
adversarial attacks, malicious injections, and network failures are contained.
"""

from __future__ import annotations
from adversarial_chaos_engine import ChaosHarness


def main():
    print("Day 19 Session 02: Adversarial Chaos & Security Testing\n")
    harness = ChaosHarness()
    results = harness.run_all_vectors()

    contained = sum(1 for r in results if r.contained)
    total = len(results)

    print(f"Chaos Vectors Tested: {total}")
    for r in results:
        status = "CONTAINED" if r.contained else "BREACHED"
        print(f"  [{r.vector_id}] {r.vector_name:<30}: {status}")

    assert contained == total, f"Only {contained}/{total} vectors were contained!"
    print(f"\nAll {total} adversarial attack vectors contained successfully.")


if __name__ == "__main__":
    main()
