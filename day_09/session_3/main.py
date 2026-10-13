"""
Day 09 - Session 03: Automated Agent Evaluation Benchmark
Runs a 30-case evaluation test suite measuring:
1. Trajectory correctness (tool selection, argument precision, ordering).
2. Final answer semantic accuracy.
3. Pass rate by category and failure taxonomy breakdown.
"""

from __future__ import annotations
import time
from typing import List
from collections import Counter
from dotenv import load_dotenv

load_dotenv()

from agent import EvaluatedAgent
from test_cases import TEST_CASES_SUITE
from evaluator import AgentEvaluator, EvaluationResult


def main():
    print("Running 30-case automated agent evaluation suite...\n")
    agent = EvaluatedAgent(mode="optimized")
    results: List[EvaluationResult] = []

    for idx, tc in enumerate(TEST_CASES_SUITE, 1):
        try:
            run_data = agent.run(tc.prompt)
            eval_res = AgentEvaluator.evaluate_case(tc, run_data)
        except Exception as e:
            eval_res = EvaluationResult(
                case_id=tc.case_id,
                category=tc.category,
                prompt=tc.prompt,
                passed=False,
                trajectory_passed=False,
                final_answer_passed=False,
                tools_called=[],
                expected_tools=tc.expected_tools,
                steps_taken=0,
                max_allowed_steps=tc.max_allowed_steps,
                failure_category="PREMATURE_TERMINATION",
                failure_reason=str(e),
            )

        results.append(eval_res)
        badge = "PASS" if eval_res.passed else f"FAIL ({eval_res.failure_category})"
        print(f"[{idx:02d}/{len(TEST_CASES_SUITE)}] Case {tc.case_id} ({tc.category}): {badge}")
        time.sleep(1.0)

    total = len(results)
    passed = sum(1 for r in results if r.passed)
    pass_rate = (passed / total) * 100

    print(f"\n--- Evaluation Results ---")
    print(f"Total Cases: {total}")
    print(f"Passed:      {passed}/{total} ({pass_rate:.1f}%)")
    print(f"Trajectory Accuracy:   {sum(1 for r in results if r.trajectory_passed)}/{total}")
    print(f"Final Answer Accuracy: {sum(1 for r in results if r.final_answer_passed)}/{total}")

    failures = [r for r in results if not r.passed]
    if failures:
        print("\nFailure Taxonomy Breakdown:")
        counts = Counter(r.failure_category for r in failures)
        for cat, count in counts.items():
            print(f"  • {cat}: {count}")
    else:
        print("\nAll 30 test cases passed successfully.")


if __name__ == "__main__":
    main()
