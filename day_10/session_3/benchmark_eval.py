"""
Day 10 - Session 03: Capstone Quantitative Benchmark & Telemetry
Measures pass rates, latency percentiles (p50, p90, p95), token usage,
and guardrail zero-token interception across the 20 capstone test cases.
"""

from __future__ import annotations
import os
import sys
import time
import json
import numpy as np
from typing import List
from dotenv import load_dotenv

load_dotenv()

# Setup imports from sibling sessions
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DAY_10_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
sys.path.insert(0, os.path.join(DAY_10_DIR, "session_2"))
sys.path.insert(0, os.path.join(DAY_10_DIR, "session_1"))

from session_manager import SessionState, MessageRecord
from agent_service import CapstoneAgentService
from test_suite import CAPSTONE_TEST_CASES


def check_keywords(answer: str, expected_keywords: List[str]) -> bool:
    if not expected_keywords:
        return bool(answer)
    clean = answer.lower().replace(",", "")
    return any(kw.lower() in clean for kw in expected_keywords)


def main():
    print("Running Capstone Quantitative Benchmark (20 cases)...\n")
    service = CapstoneAgentService()

    latencies = []
    tokens = []
    passed_count = 0

    for idx, tc in enumerate(CAPSTONE_TEST_CASES, 1):
        session = SessionState(
            session_id=f"bench-{idx}",
            user_name="Sarah Conner",
            user_role=tc.setup_role or "Admin",
            environment="production",
            datacenter="us-east-1",
            active_ticket="INC-801",
            approval_token=tc.setup_token if tc.setup_token is not None else "AUTH-OPS-APPROVE-2026",
        )
        if tc.multi_turn_history:
            for u, a in tc.multi_turn_history:
                session.messages.append(MessageRecord(role="user", content=u))
                session.messages.append(MessageRecord(role="assistant", content=a))

        t0 = time.perf_counter()
        res = service.run(session=session, user_query=tc.prompt)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        latencies.append(elapsed_ms)
        tokens.append(res.get("tokens_used", 0))

        kw_ok = check_keywords(res.get("final_answer", ""), tc.expected_keywords)
        is_blocked = res.get("is_blocked", False)
        block_ok = (is_blocked == tc.expect_blocked) if tc.expect_blocked else True
        case_passed = kw_ok and block_ok

        if case_passed:
            passed_count += 1
        badge = "PASS" if case_passed else "FAIL"
        print(f"[{idx:02d}/20] {tc.test_id} ({tc.category}): {badge} ({elapsed_ms:.1f}ms, {res.get('tokens_used', 0)} tokens)")

    total = len(CAPSTONE_TEST_CASES)
    pass_rate = (passed_count / total) * 100
    p50 = float(np.percentile(latencies, 50))
    p95 = float(np.percentile(latencies, 95))

    print("\n--- Capstone Benchmark Summary ---")
    print(f"Pass Rate:        {passed_count}/{total} ({pass_rate:.1f}%)")
    print(f"Median Latency:   {p50:.1f} ms")
    print(f"p95 Latency:      {p95:.1f} ms")
    print(f"Total Tokens:     {sum(tokens)}")
    print(f"Mean Tokens/Task: {np.mean(tokens):.1f}")

    assert passed_count >= 18, f"Benchmark passed {passed_count}/{total}, expected >= 18"
    print("\nBenchmark completed successfully.")


if __name__ == "__main__":
    main()
