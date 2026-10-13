"""
Day 10 - Session 01: Capstone Agent Assembly
Runs the test benchmark for OpsSentinel AI, validating unified RAG, tools,
memory, guardrails, and blast-radius gates across 20 operational scenarios.
"""

from __future__ import annotations
import time
from typing import List
from dotenv import load_dotenv

load_dotenv()

from capstone_agent import CapstoneAgent
from memory_manager import MemoryManager
from test_suite import CAPSTONE_TEST_CASES


def check_keywords(answer: str, expected_keywords: List[str]) -> bool:
    if not expected_keywords:
        return bool(answer)
    clean = answer.lower().replace(",", "")
    return any(kw.lower() in clean for kw in expected_keywords)


def main():
    print("Testing Capstone OpsSentinel AI across 20 test cases...\n")
    results = []

    for idx, tc in enumerate(CAPSTONE_TEST_CASES, 1):
        mem = MemoryManager()
        if tc.setup_role:
            mem.entity_store.set_entity("user_role", tc.setup_role)
        if tc.setup_token is not None:
            mem.entity_store.set_entity("approval_token", tc.setup_token)
        for role, text in tc.setup_history:
            mem.short_term.add_message(role, text)

        agent = CapstoneAgent(memory_manager=mem)
        start = time.time()
        res = agent.run(tc.user_query)
        duration = time.time() - start

        # Check conditions
        ans_pass = check_keywords(res.final_answer, tc.expected_keywords)
        tools_pass = not tc.expected_tools or any(t in res.tools_called for t in tc.expected_tools)
        blocked_pass = tc.expected_blocked is None or (res.is_blocked == tc.expected_blocked)
        passed = ans_pass and tools_pass and blocked_pass

        results.append(passed)
        badge = "PASS" if passed else "FAIL"
        print(f"[{idx:02d}/20] Case {tc.case_id} ({tc.category}): {badge} ({duration:.2f}s)")

    passed_count = sum(1 for r in results if r)
    total = len(results)
    print(f"\n--- OpsSentinel AI Assembly Scorecard ---")
    print(f"Total Cases: {total}")
    print(f"Passed:      {passed_count}/{total} ({(passed_count/total)*100:.1f}%)")

    assert passed_count >= 18, f"Only {passed_count}/{total} passed (expected >= 18)"
    print("\nOpsSentinel assembly verified successfully.")


if __name__ == "__main__":
    main()
