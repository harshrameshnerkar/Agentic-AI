"""
Master Test Runner for Capstone OpsSentinel AI.
Executes the 20-case test suite end-to-end and outputs:
1. Live execution log with turn count, tools invoked, and verdict.
2. Agent Evaluation Scorecard table.
3. Category-level performance breakdown.
4. Failure taxonomy analysis.
"""

import sys
import time
from typing import List, Dict, Any

# Ensure UTF-8 output on Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from capstone_agent import CapstoneAgent
from memory_manager import MemoryManager
from test_suite import CAPSTONE_TEST_CASES, CapstoneTestCase


def check_keywords(answer: str, expected_keywords: List[str]) -> bool:
    """Verifies that generated answer contains at least one of the expected keywords."""
    if not expected_keywords:
        return bool(answer)
    clean_ans = answer.lower().replace(",", "")
    return any(
        kw.lower() in answer.lower() or kw.lower().replace(",", "") in clean_ans
        for kw in expected_keywords
    )


def check_tools(tools_called: List[str], expected_tools: List[str]) -> bool:
    """Verifies that expected tools were called."""
    if not expected_tools:
        return True
    return any(tool in tools_called for tool in expected_tools)


def format_table_row(cols: List[str], widths: List[int]) -> str:
    cells = [c[: widths[i]].ljust(widths[i]) for i, c in enumerate(cols)]
    return "| " + " | ".join(cells) + " |"


def main():
    print("=" * 96)
    print(" DAY 10 - SESSION 1: CAPSTONE AGENT ASSEMBLY BENCHMARK")
    print(" Evaluating OpsSentinel AI: Unified RAG + Tools + Memory + Guardrails + Blast-Radius Gates")
    print("=" * 96)

    results = []
    total_cases = len(CAPSTONE_TEST_CASES)

    for idx, tc in enumerate(CAPSTONE_TEST_CASES, 1):
        # Fresh memory instance per test case to avoid state bleed
        mem = MemoryManager()
        if tc.setup_role:
            mem.entity_store.set_entity("user_role", tc.setup_role)
        if tc.setup_token is not None:
            mem.entity_store.set_entity("approval_token", tc.setup_token)

        # Preload multi-turn conversation history if requested
        if tc.multi_turn_history:
            for u_msg, a_resp in tc.multi_turn_history:
                mem.record_interaction(query=u_msg, response=a_resp, tools=[], timestamp=time.time())

        agent = CapstoneAgent(memory=mem)

        t0 = time.time()
        res = agent.run(tc.prompt)
        latency_s = (time.time() - t0)

        # Verification logic
        if tc.expect_blocked:
            passed_guardrail = res["is_blocked_by_guardrail"] is True
            passed_ans = check_keywords(res["final_answer"], tc.expected_keywords)
            passed_tools = len(res["tools_called"]) == 0
            verdict = passed_guardrail and passed_ans and passed_tools
            traj_status = "OK (BLOCKED)" if passed_guardrail else "FAIL (BYPASSED)"
            ans_status = "OK" if passed_ans else "FAIL"
        else:
            passed_tools = check_tools(res["tools_called"], tc.expected_tools)
            passed_ans = check_keywords(res["final_answer"], tc.expected_keywords)
            verdict = passed_tools and passed_ans
            traj_status = "OK" if passed_tools else "FAIL"
            ans_status = "OK" if passed_ans else "FAIL"

        status_badge = "[✓ PASS]" if verdict else "[✗ FAIL]"
        tool_str = ", ".join(res["tools_called"]) if res["tools_called"] else "none"

        print(
            f"[{idx:02d}/{total_cases}] Case {tc.test_id} ({tc.category:<22}): \"{tc.prompt[:48]}...\"\n"
            f"       Outcome: {status_badge} (Tools: [{tool_str}], Latency: {latency_s:.2f}s, Tokens: {res['tokens_used']})"
        )

        results.append({
            "test_id": tc.test_id,
            "category": tc.category,
            "tools_called": tool_str,
            "traj_status": traj_status,
            "ans_status": ans_status,
            "verdict": "PASS" if verdict else "FAIL",
            "latency_s": latency_s,
            "tokens_used": res["tokens_used"],
        })

        # Pacing sleep for API rate limit
        if not res["is_blocked_by_guardrail"]:
            time.sleep(2.5)

    # =======================================================================
    # AGENT EVALUATION SCORECARD
    # =======================================================================
    print("\n" + "=" * 96)
    print("                         CAPSTONE AGENT EVALUATION SCORECARD")
    print("=" * 96)

    headers = ["Case ID", "Category", "Tools Called", "Traj", "Ans", "Verdict"]
    widths = [8, 24, 30, 10, 8, 8]
    sep = "+-" + "-+-".join(["-" * w for w in widths]) + "-+"

    print(sep)
    print(format_table_row(headers, widths))
    print(sep)

    for r in results:
        cols = [r["test_id"], r["category"], r["tools_called"], r["traj_status"], r["ans_status"], r["verdict"]]
        print(format_table_row(cols, widths))
    print(sep)

    # =======================================================================
    # EXECUTIVE EVALUATION METRICS
    # =======================================================================
    total_passed = sum(1 for r in results if r["verdict"] == "PASS")
    pass_rate = (total_passed / total_cases) * 100.0
    traj_passed = sum(1 for r in results if "OK" in r["traj_status"])
    ans_passed = sum(1 for r in results if r["ans_status"] == "OK")
    avg_tokens = sum(r["tokens_used"] for r in results) / total_cases
    avg_latency = sum(r["latency_s"] for r in results) / total_cases

    print("\n" + "=" * 96)
    print("                       EXECUTIVE CAPSTONE METRICS")
    print("=" * 96)
    print(f" • Total Capstone Cases Evaluated : {total_cases}")
    print(f" • Overall Agent Pass Rate        : {total_passed}/{total_cases} ({pass_rate:.1f}%)")
    print(f" • Trajectory & Tool Pass Rate    : {traj_passed}/{total_cases} ({(traj_passed/total_cases)*100.0:.1f}%)")
    print(f" • Grounded Answer Accuracy       : {ans_passed}/{total_cases} ({(ans_passed/total_cases)*100.0:.1f}%)")
    print(f" • Average Tokens per Interaction : {avg_tokens:.1f} tokens")
    print(f" • Average Latency per Query      : {avg_latency:.2f} seconds")
    print("=" * 96)

    # =======================================================================
    # CATEGORY PERFORMANCE BREAKDOWN
    # =======================================================================
    categories = sorted(list(set(r["category"] for r in results)))
    print("\n" + "=" * 96)
    print("                       CATEGORY PERFORMANCE BREAKDOWN")
    print("=" * 96)

    cat_headers = ["Category Pillar", "Total Cases", "Passed", "Failed", "Success Rate"]
    cat_widths = [32, 12, 10, 10, 16]
    cat_sep = "+-" + "-+-".join(["-" * w for w in cat_widths]) + "-+"

    print(cat_sep)
    print(format_table_row(cat_headers, cat_widths))
    print(cat_sep)

    for cat in categories:
        cat_cases = [r for r in results if r["category"] == cat]
        c_tot = len(cat_cases)
        c_pass = sum(1 for r in cat_cases if r["verdict"] == "PASS")
        c_fail = c_tot - c_pass
        c_rate = (c_pass / c_tot) * 100.0
        cols = [cat, str(c_tot), str(c_pass), str(c_fail), f"{c_rate:.1f}%"]
        print(format_table_row(cols, cat_widths))
    print(cat_sep)

    # =======================================================================
    # FAILURE TAXONOMY BREAKDOWN
    # =======================================================================
    print("\n" + "=" * 96)
    print("                       FAILURE TAXONOMY BREAKDOWN")
    print("=" * 96)

    failures = [r for r in results if r["verdict"] == "FAIL"]
    if not failures:
        print(" 🎉 Zero Failures Recorded! All 20 capstone test cases passed with 100% accuracy.")
    else:
        for f in failures:
            print(f" [!] Failure in {f['test_id']} ({f['category']}): Traj={f['traj_status']}, Ans={f['ans_status']}")
    print("=" * 96)

    if pass_rate >= 90.0:
        print("\n🎉 SUCCESS: Full Capstone Agent successfully wired end-to-end and passed the test suite!\n")
    else:
        print("\n[!] Warning: Test suite pass rate fell below target threshold.\n")


if __name__ == "__main__":
    main()
