"""
Evaluation Runner & Failure Taxonomy Generator for Role B (Data Service).

Scores the complete 40-question benchmark set against the live service pipeline,
categorises all discrepancies into the failure taxonomy, and prints the report
(UNIFIED-BUSINESS-ASSISTAN.md §4.6 Day 4, Acceptance Criteria 5 & 6).
"""
import json
import os
import sys
import time
from typing import Dict, List

# Ensure data_service root is on sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from evaluation.failure_taxonomy import FailureCategory, FailureTaxonomyClassifier
from safety.validator import SQLSafetyValidator
from sql.generator import sql_generator
from correction.self_correction import correction_engine

TEST_QUERIES_PATH = os.path.join(os.path.dirname(__file__), "test_queries.json")
REPORT_OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "EVAL_REPORT.json")


def run_benchmark():
    with open(TEST_QUERIES_PATH, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    total_count = len(test_cases)
    passed_count = 0
    taxonomy_counts: Dict[str, int] = {cat.value: 0 for cat in FailureCategory}
    results = []

    print("=" * 70)
    print(f"ROLE B: DATA SERVICE BENCHMARK EVALUATION ({total_count} QUESTIONS)")
    print("=" * 70)

    for tc in test_cases:
        qid = tc["id"]
        question = tc["question"]
        expected_ans = tc["expected_answerable"]

        start_time = time.perf_counter()
        # 1. Generate SQL
        sql, is_ans, gen_note = sql_generator.generate_sql(question)

        exec_ok = False
        exec_err = None
        rows = []
        columns = []

        if is_ans and sql:
            # 2. Safety Validation Gate
            try:
                _, validated_sql, _ = SQLSafetyValidator.validate(sql)
                # 3. Execution with Self-Correction
                columns, rows, final_sql, exec_ok, exec_err, _ = (
                    correction_engine.execute_with_self_correction(
                        question=question,
                        initial_sql=validated_sql,
                    )
                )
            except Exception as e:
                exec_ok = False
                exec_err = str(e)
        else:
            exec_ok = False
            exec_err = gen_note

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        actual_answerable = is_ans and exec_ok

        # Check match with expectation
        is_pass = (actual_answerable == expected_ans)
        if is_pass:
            passed_count += 1
            status_str = "PASS"
        else:
            status_str = "FAIL"
            # Classify discrepancy
            cat = FailureTaxonomyClassifier.classify(
                question=question,
                sql=sql,
                error_message=exec_err,
                is_answerable=actual_answerable,
            )
            taxonomy_counts[cat.value] += 1

        print(f"[{qid}] {status_str:<4} | Exp Ans: {str(expected_ans):<5} | Act Ans: {str(actual_answerable):<5} | {duration_ms:>6.1f}ms | {question[:45]}...")

        results.append({
            "id": qid,
            "question": question,
            "expected_answerable": expected_ans,
            "actual_answerable": actual_answerable,
            "passed": is_pass,
            "sql": sql,
            "error": exec_err,
            "rows_returned": len(rows),
            "duration_ms": duration_ms,
        })

    accuracy = round((passed_count / total_count) * 100, 2)
    # Identify largest failure category
    sorted_failures = sorted(taxonomy_counts.items(), key=lambda x: x[1], reverse=True)
    largest_category, largest_count = sorted_failures[0]

    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_questions": total_count,
        "passed": passed_count,
        "failed": total_count - passed_count,
        "accuracy_pct": accuracy,
        "taxonomy_counts": taxonomy_counts,
        "largest_failure_category": {
            "category": largest_category,
            "count": largest_count,
        },
        "details": results,
    }

    with open(REPORT_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 70)
    print("BENCHMARK EVALUATION SUMMARY")
    print("=" * 70)
    print(f"Total Test Cases   : {total_count}")
    print(f"Passed             : {passed_count}")
    print(f"Failed             : {total_count - passed_count}")
    print(f"Overall Accuracy   : {accuracy}%")
    print("-" * 70)
    print("FAILURE TAXONOMY BREAKDOWN:")
    for cat_name, count in sorted_failures:
        pct = round((count / total_count) * 100, 1) if total_count > 0 else 0
        print(f"  • {cat_name:<28}: {count:>2} ({pct:>4}%)")
    print("-" * 70)
    print(f"Largest Category   : {largest_category} ({largest_count} occurrences)")
    print(f"Saved Report to    : {REPORT_OUTPUT_PATH}")
    print("=" * 70)

    return report


if __name__ == "__main__":
    run_benchmark()
