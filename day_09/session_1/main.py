"""
Day 09 - Session 01: Prompt Injection & Defense
Tests indirect prompt injection attacks embedded inside RAG documents,
comparing an unprotected agent (vulnerable) against a hardened agent (defended).
"""

from __future__ import annotations
import time
from dotenv import load_dotenv

load_dotenv()

from unprotected_agent import UnprotectedAgent
from hardened_agent import HardenedAgent
from evaluator import TEST_CASES, evaluate_attack


def main():
    print("Day 09 Session 01: Evaluating Indirect Prompt Injection Defenses\n")

    unprotected = UnprotectedAgent()
    hardened = HardenedAgent()

    unprot_takeovers = 0
    hardened_takeovers = 0

    for idx, tc in enumerate(TEST_CASES, 1):
        print(f"[{idx}/5] Test {tc.test_id}: {tc.title}")
        print(f"  User Query: '{tc.user_query}'")

        # 1. Unprotected
        res_u = unprotected.run(tc.user_query)
        eval_u = evaluate_attack(tc, res_u)
        if eval_u.attack_succeeded:
            unprot_takeovers += 1
            print(f"  Unprotected: HIJACKED ({eval_u.violation_type})")
        else:
            print("  Unprotected: Safe")

        # 2. Hardened
        res_h = hardened.run(tc.user_query)
        eval_h = evaluate_attack(tc, res_h)
        if eval_h.attack_succeeded:
            hardened_takeovers += 1
            print(f"  Hardened: HIJACKED ({eval_h.violation_type})")
        else:
            print("  Hardened: DEFENDED (Attack blocked cleanly)")

    print("\n--- Benchmark Summary ---")
    print(f"Unprotected Agent Takeovers: {unprot_takeovers}/{len(TEST_CASES)} ({(unprot_takeovers/len(TEST_CASES))*100:.0f}%)")
    print(f"Hardened Agent Takeovers:    {hardened_takeovers}/{len(TEST_CASES)} ({(hardened_takeovers/len(TEST_CASES))*100:.0f}%)")

    assert hardened_takeovers == 0, f"Hardened agent was breached in {hardened_takeovers} tests!"
    print("\nDefense verified: Hardened agent successfully neutralized all prompt injection attacks.")


if __name__ == "__main__":
    main()
