"""
Master Test Runner: 30-Case Agent Evaluation Benchmark.
Executes the automated 30-case regression test suite, scoring:
1. Trajectory Verification (Tool selection, arguments, prerequisite ordering, step efficiency).
2. Final-Answer Evaluation (Semantic correctness and factual grounding).
3. Overall Task Success Rate.
4. Comprehensive Failure Taxonomy Breakdown.
"""

import sys
import time
from typing import Dict, List, Any
from collections import Counter

# Ensure UTF-8 output on Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from agent import EvaluatedAgent
from test_cases import TEST_CASES_SUITE, TestCase
from evaluator import AgentEvaluator, EvaluationResult


def format_table_row(cols: List[str], widths: List[int]) -> str:
    """Formats columns into a clean ASCII table row."""
    cells = [c[: widths[i]].ljust(widths[i]) for i, c in enumerate(cols)]
    return "| " + " | ".join(cells) + " |"


def main():
    print("=" * 90)
    print(" DAY 9 - SESSION 3: AUTOMATED AGENT EVALUATION BENCHMARK")
    print(" 30-Case Test Suite: Trajectory Auditing, Tool Accuracy & Failure Taxonomy")
    print("=" * 90)

    try:
        agent = EvaluatedAgent(mode="optimized")
    except Exception as e:
        print(f"[!] Initialization Error: {e}")
        sys.exit(1)

    results: List[EvaluationResult] = []
    total_cases = len(TEST_CASES_SUITE)

    print(f"\nExecuting {total_cases} Automated Evaluation Cases across 6 Operational Domains...\n")

    for idx, tc in enumerate(TEST_CASES_SUITE, 1):
        print(f"[{idx:02d}/{total_cases}] Case {tc.case_id} ({tc.category}): \"{tc.prompt[:55]}...\"")
        t0 = time.time()
        
        try:
            agent_run = agent.run(tc.prompt)
            eval_res = AgentEvaluator.evaluate_case(tc, agent_run)
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
                failure_reason=f"Runtime Exception: {str(e)}",
            )
        
        t_el = time.time() - t0
        results.append(eval_res)

        badge = "[✓ PASS]" if eval_res.passed else f"[✗ FAIL - {eval_res.failure_category}]"
        tools_str = ", ".join(eval_res.tools_called) if eval_res.tools_called else "None"
        print(f"       Outcome: {badge} (Turns: {eval_res.steps_taken}, Tools: [{tools_str}], Latency: {t_el:.2f}s)")

        # Pacing to adhere cleanly to API rate limits
        time.sleep(2.5)

    # =======================================================================
    # 1. SUMMARY SCORECARD
    # =======================================================================
    print("\n" + "=" * 90)
    print("                         AGENT EVALUATION SCORECARD")
    print("=" * 90)

    headers = ["Case ID", "Category", "Tools Called", "Steps", "Traj", "Ans", "Verdict"]
    widths = [8, 22, 24, 6, 6, 6, 8]
    sep = "+-" + "-+-".join(["-" * w for w in widths]) + "-+"

    print(sep)
    print(format_table_row(headers, widths))
    print(sep)

    for r in results:
        tools_disp = ",".join(r.tools_called) if r.tools_called else "None"
        traj_str = "OK" if r.trajectory_passed else "FAIL"
        ans_str = "OK" if r.final_answer_passed else "FAIL"
        status_str = "PASS" if r.passed else "FAIL"

        row = [
            r.case_id,
            r.category[:22],
            tools_disp[:24],
            str(r.steps_taken),
            traj_str,
            ans_str,
            status_str,
        ]
        print(format_table_row(row, widths))

    print(sep)

    # =======================================================================
    # 2. AGGREGATE PERFORMANCE METRICS
    # =======================================================================
    passed_count = sum(1 for r in results if r.passed)
    traj_pass_count = sum(1 for r in results if r.trajectory_passed)
    ans_pass_count = sum(1 for r in results if r.final_answer_passed)
    overall_pass_rate = (passed_count / total_cases) * 100
    traj_pass_rate = (traj_pass_count / total_cases) * 100
    ans_pass_rate = (ans_pass_count / total_cases) * 100
    avg_steps = sum(r.steps_taken for r in results) / total_cases

    print("\n" + "=" * 90)
    print("                       EXECUTIVE EVALUATION METRICS")
    print("=" * 90)
    print(f" • Total Test Cases Evaluated   : {total_cases}")
    print(f" • Overall Task Success Rate    : {passed_count}/{total_cases} ({overall_pass_rate:.1f}%)")
    print(f" • Trajectory Pass Rate         : {traj_pass_count}/{total_cases} ({traj_pass_rate:.1f}%)")
    print(f" • Final-Answer Pass Rate       : {ans_pass_count}/{total_cases} ({ans_pass_rate:.1f}%)")
    print(f" • Average Steps / Turns Taken  : {avg_steps:.2f} turns per task")
    print("=" * 90)

    # =======================================================================
    # 3. CATEGORY-BY-CATEGORY BREAKDOWN
    # =======================================================================
    print("\n" + "=" * 90)
    print("                       CATEGORY PERFORMANCE BREAKDOWN")
    print("=" * 90)
    cat_headers = ["Category Domain", "Total Cases", "Passed", "Failed", "Success Rate"]
    cat_widths = [28, 12, 10, 10, 14]
    cat_sep = "+-" + "-+-".join(["-" * w for w in cat_widths]) + "-+"

    categories = list(dict.fromkeys(r.category for r in results))
    print(cat_sep)
    print(format_table_row(cat_headers, cat_widths))
    print(cat_sep)

    for cat in categories:
        cat_results = [r for r in results if r.category == cat]
        cat_total = len(cat_results)
        cat_passed = sum(1 for r in cat_results if r.passed)
        cat_failed = cat_total - cat_passed
        cat_rate = (cat_passed / cat_total) * 100

        row = [
            cat[:28],
            str(cat_total),
            str(cat_passed),
            str(cat_failed),
            f"{cat_rate:.1f}%",
        ]
        print(format_table_row(row, cat_widths))

    print(cat_sep)

    # =======================================================================
    # 4. FAILURE TAXONOMY BREAKDOWN
    # =======================================================================
    print("\n" + "=" * 90)
    print("                       FAILURE TAXONOMY BREAKDOWN")
    print("=" * 90)

    failures = [r for r in results if not r.passed]
    if not failures:
        print(" 🎉 Zero Failures Recorded! All 30 test cases passed with 100% accuracy.")
    else:
        failure_counts = Counter(r.failure_category for r in failures)
        print(f" Total Failures: {len(failures)} out of {total_cases} cases ({100 - overall_pass_rate:.1f}% error rate)\n")
        print(f" {'Failure Classification':<32} | {'Count':<6} | {'% of Failures':<14} | {'Visual Distribution'}")
        print("-" * 90)
        for cat, cnt in failure_counts.most_common():
            pct = (cnt / len(failures)) * 100
            bar = "█" * int(pct / 5)
            print(f" {cat:<32} | {cnt:<6} | {pct:>5.1f}%        | {bar}")

        print("\n Granular Failure Details:")
        for f in failures:
            print(f"   • [{f.case_id}] {f.category} -> {f.failure_category}: {f.failure_reason}")

    print("=" * 90)


if __name__ == "__main__":
    main()
