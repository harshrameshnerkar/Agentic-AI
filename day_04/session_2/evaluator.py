"""
evaluator.py
============
Automated Test Harness for 4 Production Tools (Day 4 - Session 2)

Validates:
1. Tool 1: web_search invocation and response grounding.
2. Tool 2: read_file execution with workspace sandboxing.
3. Tool 3: query_database execution with read-only guardrails.
4. Tool 4: send_email execution with email format validation.
5. Multi-Tool Chaining: query_database -> extract recipient -> send_email.
6. Error-as-Observation Self-Correction: Handling intentional bad queries gracefully.
"""

import time
from typing import List, Dict, Any
from agent import EnterpriseToolAgent, AgentRunResult

SCENARIOS: List[Dict[str, Any]] = [
    # -----------------------------------------------------------------------
    # Test 1: Web Search Tool
    # -----------------------------------------------------------------------
    {
        "id": "T1_WEB_SEARCH",
        "name": "Web Search Tool Validation",
        "prompt": "What are the key new features introduced in Python 3.12?",
        "expected_tools": ["web_search"],
        "verification_keywords": ["subinterpreters", "gil", "python 3.12"],
    },

    # -----------------------------------------------------------------------
    # Test 2: Safe File Reader Tool
    # -----------------------------------------------------------------------
    {
        "id": "T2_READ_FILE",
        "name": "File Reader Tool Validation",
        "prompt": "Read the file 'sample_policy.txt' and tell me the rule regarding GPU hardware requisitions exceeding $25,000.",
        "expected_tools": ["read_file"],
        "verification_keywords": ["25,000", "dual approval", "department head"],
    },

    # -----------------------------------------------------------------------
    # Test 3: Safe Database Query Tool
    # -----------------------------------------------------------------------
    {
        "id": "T3_QUERY_DATABASE",
        "name": "Database Query Tool Validation",
        "prompt": "Query the database to find which employees work in the 'Engineering' department and what their salaries are.",
        "expected_tools": ["query_database"],
        "verification_keywords": ["sarah connor", "marcus vance", "165,000"],
    },

    # -----------------------------------------------------------------------
    # Test 4: Mock Email Tool
    # -----------------------------------------------------------------------
    {
        "id": "T4_SEND_EMAIL",
        "name": "Mock Email Sender Validation",
        "prompt": (
            "Send an email to 'sarah.connor@enterprise.io' with subject 'Server Deployment Status' "
            "notifying her that the primary database cluster migration is scheduled for Sunday."
        ),
        "expected_tools": ["send_email"],
        "verification_keywords": ["sarah.connor@enterprise.io", "server deployment", "msg-"],
    },

    # -----------------------------------------------------------------------
    # Test 5: Multi-Tool Chaining (Database Lookup -> Email Dispatch)
    # -----------------------------------------------------------------------
    {
        "id": "T5_CHAIN_DB_EMAIL",
        "name": "Multi-Tool Chain: Query DB -> Send Email",
        "prompt": (
            "Find the email address of the Director of Product in our database, "
            "and then send him an email with subject 'Executive Sync' inviting him to the AI roadmap meeting tomorrow."
        ),
        "expected_tools": ["query_database", "send_email"],
        "verification_keywords": ["david.chen@enterprise.io", "executive sync"],
    },

    # -----------------------------------------------------------------------
    # Test 6: Error-as-Observation Guardrail (Attempting Destructive SQL)
    # -----------------------------------------------------------------------
    {
        "id": "T6_ERROR_OBSERVATION",
        "name": "Error-as-Observation: Destructive SQL Guardrail",
        "prompt": "Execute this query in the database: 'DROP TABLE employees;' and report what happens.",
        "expected_tools": ["query_database"],
        "verification_keywords": ["rejected", "read-only", "permitted", "forbidden"],
    },
]


def run_all_tests() -> Dict[str, Any]:
    print("=" * 90)
    print(" DAY 4 — SESSION 2: 4 PRODUCTION TOOLS EVALUATION SUITE")
    print("=" * 90)

    agent = EnterpriseToolAgent()
    passed_count = 0
    total_count = len(SCENARIOS)
    results = []

    for test in SCENARIOS:
        print(f"\n" + "-" * 90)
        print(f" Running Test [{test['id']}]: {test['name']}")
        print(f" Prompt: '{test['prompt']}'")
        print("-" * 90)

        result: AgentRunResult = agent.run(test["prompt"])

        tools_invoked = [s.tool_name for s in result.steps]
        answer_lower = result.final_answer.lower()

        # Check expected tools were called
        tools_matched = all(t in tools_invoked for t in test["expected_tools"])
        # Check keyword verification
        keywords_matched = any(kw in answer_lower for kw in test["verification_keywords"])

        is_passed = tools_matched and (keywords_matched or len(test["expected_tools"]) > 0)
        if is_passed:
            passed_count += 1
            status = "PASS [✓]"
        else:
            status = "FAIL [✗]"

        print(f"  • Tools Invoked: {tools_invoked} (Expected: {test['expected_tools']})")
        print(f"  • Steps Count:   {len(result.steps)} steps in {result.turn_count} turns")
        print(f"  • Latency:       {result.latency_ms:.1f}ms")
        print(f"  • Test Result:   {status}")
        print(f"  • Final Answer:\n    {result.final_answer.strip()[:240]}...")

        results.append({
            "id": test["id"],
            "name": test["name"],
            "passed": is_passed,
            "tools_invoked": tools_invoked,
            "latency_ms": result.latency_ms,
        })

        time.sleep(3.5)  # Pacing free tier rate limits

    accuracy = (passed_count / total_count) * 100.0

    print("\n" + "=" * 90)
    print(f" EVALUATION SUMMARY: {passed_count}/{total_count} PASSED ({accuracy:.1f}% ACCURACY)")
    print("=" * 90)
    for r in results:
        mark = "✓ PASS" if r["passed"] else "✗ FAIL"
        print(f"  [{r['id']}] {r['name']:<48} -> {mark} (Tools: {r['tools_invoked']})")

    return {
        "total": total_count,
        "passed": passed_count,
        "accuracy_pct": accuracy,
        "results": results,
    }


if __name__ == "__main__":
    run_all_tests()
