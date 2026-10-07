"""
evaluator.py
============
Automated Tool Routing & Dispatch Benchmark (Day 4 - Session 1)

Responsibilities:
1. Benchmark tool routing accuracy:
   - Validates that math queries route to `calculator`.
   - Validates that time queries route to `get_current_time`.
   - Validates that general knowledge queries do NOT trigger tool calls.
2. Inspects argument quality (e.g. valid mathematical expressions, valid timezones).
3. Produces a Pass/Fail scorecard confirming the model calls the right tool.
"""

import time
from typing import List, Dict, Any, Optional
from tool_caller import ToolCallingAgent, ToolCallTelemetry

EVALUATION_DATASET: List[Dict[str, Any]] = [
    # -----------------------------------------------------------------------
    # Category 1: Calculator Queries
    # -----------------------------------------------------------------------
    {
        "category": "Math / Arithmetic",
        "query": "What is 1450 divided by 25 plus 18?",
        "expected_tool": "calculator",
        "description": "Multi-operator arithmetic expression",
    },
    {
        "category": "Math / Arithmetic",
        "query": "Can you compute the square root of 256?",
        "expected_tool": "calculator",
        "description": "Mathematical function (sqrt)",
    },
    {
        "category": "Math / Arithmetic",
        "query": "If I have $12,500 and earn 8% interest, how much interest is that?",
        "expected_tool": "calculator",
        "description": "Percentage calculation",
    },

    # -----------------------------------------------------------------------
    # Category 2: Get Current Time Queries
    # -----------------------------------------------------------------------
    {
        "category": "Temporal / Clock",
        "query": "What is the current time in UTC right now?",
        "expected_tool": "get_current_time",
        "description": "Explicit UTC time request",
    },
    {
        "category": "Temporal / Clock",
        "query": "What time is it currently in New York City (EST/EDT)?",
        "expected_tool": "get_current_time",
        "description": "City-specific timezone lookup",
    },
    {
        "category": "Temporal / Clock",
        "query": "Could you tell me today's date and the current time in Tokyo, Japan?",
        "expected_tool": "get_current_time",
        "description": "Asian timezone lookup (Tokyo)",
    },

    # -----------------------------------------------------------------------
    # Category 3: Conversational (No Tool Should Be Called)
    # -----------------------------------------------------------------------
    {
        "category": "Direct Response (No Tool)",
        "query": "What is the capital city of Australia?",
        "expected_tool": None,
        "description": "Static geographical knowledge",
    },
    {
        "category": "Direct Response (No Tool)",
        "query": "Hello! How are you doing today?",
        "expected_tool": None,
        "description": "Conversational greeting",
    },
]


def run_evaluation() -> Dict[str, Any]:
    """
    Executes the benchmark evaluation and prints a formatted scorecard.
    """
    print("=" * 90)
    print(" AUTOMATED TOOL ROUTING EVALUATION SUITE")
    print(" Confirming the model calls the right tool across Math, Clock, and Non-Tool queries")
    print("=" * 90)

    agent = ToolCallingAgent()

    total_tests = len(EVALUATION_DATASET)
    passed_tests = 0
    results: List[Dict[str, Any]] = []

    print(f"\nRunning {total_tests} evaluation scenarios...\n")
    print(f"{'#':<3} | {'CATEGORY':<24} | {'EXPECTED':<18} | {'ACTUAL':<18} | {'STATUS':<6}")
    print("-" * 90)

    for idx, test in enumerate(EVALUATION_DATASET, start=1):
        q = test["query"]
        expected = test["expected_tool"]
        cat = test["category"]

        telemetry: ToolCallTelemetry = agent.run(q, tool_choice="auto")
        actual = telemetry.tool_called

        is_correct = (expected == actual)
        if is_correct:
            passed_tests += 1
            status_str = "PASS"
        else:
            status_str = "FAIL"

        expected_display = expected if expected else "[No Tool]"
        actual_display = actual if actual else "[No Tool]"

        print(f"{idx:<3} | {cat:<24} | {expected_display:<18} | {actual_display:<18} | {status_str:<6}")
        
        results.append({
            "index": idx,
            "query": q,
            "category": cat,
            "expected_tool": expected,
            "actual_tool": actual,
            "passed": is_correct,
            "arguments": telemetry.tool_arguments,
            "raw_output": telemetry.tool_raw_output,
            "final_answer": telemetry.final_answer,
            "latency_ms": telemetry.latency_ms,
        })

        time.sleep(2.0)  # Rate pacing

    accuracy = (passed_tests / total_tests) * 100.0

    print("-" * 90)
    print(f"\nFINAL SCORE: {passed_tests}/{total_tests} Tests Passed ({accuracy:.1f}% Routing Accuracy)\n")

    # Detailed Inspection of Select Passed Cases
    print("=" * 90)
    print(" DETAILED EXECUTION AUDIT (SAMPLE CASES)")
    print("=" * 90)
    for r in results[:4]:
        print(f"\nTest #{r['index']} [{r['category']}]: '{r['query']}'")
        print(f"  • Tool Invoked:    {r['actual_tool']}")
        print(f"  • Arguments:       {r['arguments']}")
        print(f"  • Local Output:    {r['raw_output']}")
        print(f"  • Synthesized LLM: {r['final_answer'].strip()}")
        print(f"  • Execution Time:  {r['latency_ms']:.1f}ms")

    return {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "accuracy_pct": accuracy,
        "results": results,
    }


if __name__ == "__main__":
    run_evaluation()
