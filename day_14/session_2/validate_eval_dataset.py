"""
Day 14 - Session 2: Dedicated Golden Dataset Validator
======================================================
Strictly audits and validates the 100-case evaluation dataset:
  1. Exactly 100 cases
  2. Zero duplicate case IDs
  3. All required fields present (case_id, stratum, incident_query, ground_truth_tool, is_destructive, mandatory_approval, expected_root_cause_tags, production_frequency_weight, source_trace_id)
  4. Query type / stratum present and valid
  5. Trace / source information present
  6. Valid structure & types
  7. Non-empty incident queries
  8. Uncorrupted records
"""

import os
import sys
import json
from typing import Dict, List, Any

EXPECTED_STRATA = {
    "INFRA_DIAGNOSTIC": 25,
    "DESTRUCTIVE_REMEDIATION": 25,
    "DATABASE_STORAGE": 20,
    "NETWORK_INGRESS": 15,
    "SECURITY_ADVERSARIAL": 15,
}

REQUIRED_FIELDS = [
    "case_id",
    "stratum",
    "incident_query",
    "ground_truth_tool",
    "is_destructive",
    "mandatory_approval",
    "expected_root_cause_tags",
    "production_frequency_weight",
    "source_trace_id",
]


def validate_dataset(filepath: str) -> bool:
    print("\n" + "=" * 90)
    print(" DAY 14 - SESSION 2: 100-CASE EVALUATION DATASET INTEGRITY VALIDATOR ".center(90))
    print("=" * 90)
    print(f"Target Dataset Path: {filepath}")

    if not os.path.exists(filepath):
        print(f"[FAIL] Dataset file does not exist at '{filepath}'.")
        return False

    with open(filepath, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"[FAIL] JSON parsing error: {e}")
            return False

    if not isinstance(data, list):
        print(f"[FAIL] Expected JSON list at root, got {type(data)}.")
        return False

    # Check 1: Exactly 100 Cases
    total_cases = len(data)
    print(f"Total Cases Count: {total_cases} (Expected: 100)")
    if total_cases != 100:
        print(f"[FAIL] Dataset case count {total_cases} != 100.")
        return False

    seen_ids = set()
    strata_counts = {k: 0 for k in EXPECTED_STRATA}
    violations = []

    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            violations.append(f"Item #{idx} is not a JSON object.")
            continue

        # Check required fields
        for field in REQUIRED_FIELDS:
            if field not in item:
                violations.append(f"Item #{idx} missing required field '{field}'.")

        # Check case ID uniqueness
        cid = item.get("case_id")
        if not cid or not isinstance(cid, str):
            violations.append(f"Item #{idx} has invalid case_id: {cid}")
        elif cid in seen_ids:
            violations.append(f"Duplicate case_id detected: {cid}")
        else:
            seen_ids.add(cid)

        # Check query non-empty
        q = item.get("incident_query", "")
        if not q or not isinstance(q, str) or len(q.strip()) < 10:
            violations.append(f"Case '{cid}' has empty or too short query: '{q}'")

        # Check stratum validity
        st = item.get("stratum")
        if st not in EXPECTED_STRATA:
            violations.append(f"Case '{cid}' has unknown stratum: '{st}'")
        else:
            strata_counts[st] += 1

        # Check source trace provenance
        trace_id = item.get("source_trace_id")
        if not trace_id or not isinstance(trace_id, str):
            violations.append(f"Case '{cid}' missing source trace provenance.")

    # Check Stratification Distribution
    print("\nStratification Distribution Breakdown:")
    print("-" * 90)
    print(f"| {'Stratum':<28} | {'Count':<8} | {'Expected':<10} | {'Status':<8} |")
    print("-" * 90)
    strata_ok = True
    for st, expected_count in EXPECTED_STRATA.items():
        actual_count = strata_counts.get(st, 0)
        status = "OK" if actual_count == expected_count else "MISMATCH"
        if status != "OK":
            strata_ok = False
        print(f"| {st:<28} | {actual_count:<8} | {expected_count:<10} | {status:<8} |")
    print("-" * 90)

    if violations:
        print(f"\n[FAIL] Found {len(violations)} validation violations:")
        for v in violations[:10]:
            print(f"  - {v}")
        return False

    if not strata_ok:
        print("\n[FAIL] Stratification distribution mismatch.")
        return False

    print("\n[PASS] All 8 dataset validation checks passed with 100% compliance!")
    print("=" * 90)
    return True


if __name__ == "__main__":
    dataset_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "golden_dataset_100.json")
    success = validate_dataset(dataset_path)
    sys.exit(0 if success else 1)
