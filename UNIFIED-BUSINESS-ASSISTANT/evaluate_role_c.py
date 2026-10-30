"""
Role C Master Evaluation Suite
Benchmarks Interface 3 Routing Accuracy, Contract Compliance, and Answer Synthesis
against all project test sets:
- sql_test.json (Data queries)
- test_set.json (Knowledge queries)
- hybrid_test_set.json (Ambiguous / Cross-Domain & Unanswerable queries)
"""

import os
import sys
import json
import time
from typing import Dict, Any, List

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from orchestrator import RoleCOrchestrator
from router import RouteType

def load_json(filepath: str) -> Any:
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def evaluate_role_c():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    orchestrator = RoleCOrchestrator(prefer_mock=True)

    print("=" * 80)
    print(" ROLE C (ORCHESTRATOR & ROUTER) - MASTER EVALUATION SUITE")
    print("=" * 80)

    total_tests = 0
    passed_tests = 0
    results_summary = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "suites": {}
    }

    # ──────────────────────────────────────────────────────────────────────────
    # Suite 1: Structured Data Queries (sql_test.json)
    # Expected route: 'data'
    # ──────────────────────────────────────────────────────────────────────────
    sql_file = os.path.join(base_dir, "sql_test.json")
    sql_data = load_json(sql_file)
    if sql_data and "test_cases" in sql_data:
        test_cases = sql_data["test_cases"]
        print(f"\n[SUITE 1] Evaluating Structured Data Queries ({len(test_cases)} cases)...")
        suite_passed = 0
        for tc in test_cases:
            total_tests += 1
            q = tc["question"]
            res = orchestrator.process_query(q)
            route = res["route"]
            # Valid data response should have SQL and data_rows or valid error
            is_valid = (route == RouteType.DATA.value) and (res.get("sql") is not None)
            if is_valid:
                passed_tests += 1
                suite_passed += 1
                status = "PASS"
            else:
                status = f"FAIL (Got route='{route}')"
            print(f"  [{status}] ID {tc['id']}: {q[:55]}...")

        acc = round((suite_passed / len(test_cases)) * 100, 1)
        print(f"  => Suite 1 Accuracy: {acc}% ({suite_passed}/{len(test_cases)})")
        results_summary["suites"]["structured_data"] = {
            "total": len(test_cases),
            "passed": suite_passed,
            "accuracy": f"{acc}%"
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Suite 2: Hybrid & Unanswerable Queries (hybrid_test_set.json)
    # Expected routes: 'both' (Ambiguous) and 'none' (Unanswerable)
    # ──────────────────────────────────────────────────────────────────────────
    hybrid_file = os.path.join(base_dir, "hybrid_test_set.json")
    hybrid_data = load_json(hybrid_file)
    if hybrid_data and "test_cases" in hybrid_data:
        test_cases = hybrid_data["test_cases"]
        print(f"\n[SUITE 2] Evaluating Hybrid & Guardrail Queries ({len(test_cases)} cases)...")
        suite_passed = 0
        for tc in test_cases:
            total_tests += 1
            q = tc["question"]
            cat = tc.get("category", "")
            res = orchestrator.process_query(q)
            route = res["route"]

            if cat == "Ambiguous":
                expected = RouteType.BOTH.value
            elif cat == "Unanswerable":
                expected = RouteType.NONE.value
            else:
                expected = RouteType.KNOWLEDGE.value

            is_valid = (route == expected)
            if is_valid:
                passed_tests += 1
                suite_passed += 1
                status = "PASS"
            else:
                status = f"FAIL (Expected '{expected}', got '{route}')"
            print(f"  [{status}] ID {tc['id']} [{cat}]: {q[:50]}...")

        acc = round((suite_passed / len(test_cases)) * 100, 1)
        print(f"  => Suite 2 Accuracy: {acc}% ({suite_passed}/{len(test_cases)})")
        results_summary["suites"]["hybrid_and_guardrails"] = {
            "total": len(test_cases),
            "passed": suite_passed,
            "accuracy": f"{acc}%"
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Suite 3: Corporate Policy Knowledge Queries (test_set.json)
    # Expected route: 'knowledge'
    # ──────────────────────────────────────────────────────────────────────────
    knowledge_file = os.path.join(base_dir, "test_set.json")
    knowledge_data = load_json(knowledge_file)
    if knowledge_data and isinstance(knowledge_data, list):
        print(f"\n[SUITE 3] Evaluating Knowledge Service Policy Queries ({len(knowledge_data)} cases)...")
        suite_passed = 0
        for tc in knowledge_data:
            total_tests += 1
            q = tc["question"]
            res = orchestrator.process_query(q)
            route = res["route"]
            is_valid = (route == RouteType.KNOWLEDGE.value)
            if is_valid:
                passed_tests += 1
                suite_passed += 1
                status = "PASS"
            else:
                status = f"FAIL (Got route='{route}')"
            print(f"  [{status}] ID {tc.get('id', '?')}: {q[:55]}...")

        acc = round((suite_passed / len(knowledge_data)) * 100, 1)
        print(f"  => Suite 3 Accuracy: {acc}% ({suite_passed}/{len(knowledge_data)})")
        results_summary["suites"]["policy_knowledge"] = {
            "total": len(knowledge_data),
            "passed": suite_passed,
            "accuracy": f"{acc}%"
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Suite 4: Contract Compliance & Fallback Handling Verification
    # ──────────────────────────────────────────────────────────────────────────
    print(f"\n[SUITE 4] Verifying Contract Flags & Fallback Guarantees...")
    c_passed = 0
    c_total = 3

    # Check 1: no_match prevents hallucination
    res1 = orchestrator.invoke_knowledge_service("xyzrandomunrelatedword12345")
    if res1.get("no_match") is True:
        c_passed += 1
        print("  [PASS] Interface 1 no_match=True returned when query has zero matches.")
    else:
        print("  [FAIL] Interface 1 did not return no_match=True for empty match.")

    # Check 2: answerable=False triggered on unanswerable SQL
    res2 = orchestrator.invoke_data_service("Find the profit margin from nonexistent table")
    if res2.get("answerable") is False:
        c_passed += 1
        print("  [PASS] Interface 2 answerable=False returned on unanswerable schema query.")
    else:
        print("  [FAIL] Interface 2 did not flag answerable=False.")

    # Check 3: Orchestrator Fallback logic handles answerable=False gracefully
    res3 = orchestrator.process_query("Find the average profit of nonexistent table")
    if "cannot answer" in res3["final_answer"].lower() or "could not answer" in res3["final_answer"].lower():
        c_passed += 1
        print("  [PASS] Role C Orchestrator produced safe refusal for unanswerable query.")
    else:
        print(f"  [FAIL] Role C Orchestrator did not handle unanswerable fallback properly: {res3['final_answer']}")

    total_tests += c_total
    passed_tests += c_passed
    results_summary["suites"]["contract_compliance"] = {
        "total": c_total,
        "passed": c_passed,
        "accuracy": f"{round((c_passed/c_total)*100, 1)}%"
    }

    # Overall Summary
    overall_acc = round((passed_tests / total_tests) * 100, 2)
    results_summary["overall"] = {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "accuracy": f"{overall_acc}%"
    }

    print("\n" + "=" * 80)
    print(f" FINAL ROLE C EVALUATION SCORE: {overall_acc}% ({passed_tests}/{total_tests} passed)")
    print("=" * 80)

    # Save evaluation report artifact
    report_path = os.path.join(base_dir, "role_c_evaluation_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2)
    print(f"\nSaved evaluation metrics report to: {report_path}")

    return overall_acc >= 90.0

if __name__ == "__main__":
    success = evaluate_role_c()
    sys.exit(0 if success else 1)
