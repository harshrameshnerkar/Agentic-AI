"""Master End-to-End Verification Runner for Week 5 Document Extraction Pipeline.

Executes all 5 verification suites in sequence:
- Day 1: Documents, Field Specification & Ground Truth (Criteria 1 & 2)
- Day 2: Parsing & The Extraction Schema (Criteria 3 & 4)
- Day 3: Field-Level Accuracy & Granular Benchmarking (Criteria 5 & 6)
- Day 4: Confidence Scoring & The Human Review Queue (Criteria 7 & 8)
- Day 5: Batch Pipeline, Cost Scaling & Handover (Criteria 9, 10 & 11)

Validates all 11 Acceptance Criteria and returns exit code 0.
"""

from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

VERIFICATION_STEPS = [
    {
        "day": "Day 1",
        "focus": "Documents, Field Spec & Ground Truth",
        "criteria": [
            "1. Written field specification exists with missing value rules",
            "2. Ground truth hand-keyed for 40 docs committed before code",
        ],
        "script": BASE_DIR / "day1" / "verify_day1.py",
    },
    {
        "day": "Day 2",
        "focus": "Parsing & The Extraction Schema",
        "criteria": [
            "3. Loader handles text PDFs, scanned PDFs and images without crashing",
            "4. Output is enforced by typed Pydantic schema with validation retry guards",
        ],
        "script": BASE_DIR / "day2" / "verify_day2.py",
    },
    {
        "day": "Day 3",
        "focus": "Field-Level Accuracy",
        "criteria": [
            "5. Accuracy is reported per field, not only per document",
            "6. Matching rules are sensible per field type and documented",
        ],
        "script": BASE_DIR / "day3" / "verify_day3.py",
    },
    {
        "day": "Day 4",
        "focus": "Confidence & Human Review Queue",
        "criteria": [
            "7. Confidence signal exists and routes low-confidence extractions to review",
            "8. Review threshold is tuned with evidence (0.80 optimal operating point)",
        ],
        "script": BASE_DIR / "day4" / "verify_day4.py",
    },
    {
        "day": "Day 5",
        "focus": "Batch Pipeline, Cost & Handover",
        "criteria": [
            "9. Batch pipeline survives bad documents mid-run without losing prior work",
            "10. Cost per document measured and projected to 10,000 documents",
            "11. README allows second person to run pipeline from clean clone + Streamlit UI",
        ],
        "script": BASE_DIR / "day5" / "verify_day5.py",
    },
]


def run_command(script_path: Path):
    env = os.environ.copy()
    repo_root = str(BASE_DIR.parent)
    week5_root = str(BASE_DIR)
    existing_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{repo_root}{os.pathsep}{week5_root}{os.pathsep}{existing_pp}" if existing_pp else f"{repo_root}{os.pathsep}{week5_root}"
    cmd = [sys.executable, str(script_path)]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(BASE_DIR.parent), env=env)
    return result.returncode == 0, result.stdout, result.stderr


def main():
    print("=" * 80)
    print("WEEK 5: COMPLETE END-TO-END ACCEPTANCE CRITERIA VERIFICATION GATE")
    print("Task 5: Production Document Extraction Pipeline (Days 1 to 5)")
    print("=" * 80)

    all_passed = True
    results = []

    for step in VERIFICATION_STEPS:
        day_name = step["day"]
        script = step["script"]
        print(f"\n[RUNNING {day_name}] {step['focus']} ({script.name})...")

        passed, stdout, stderr = run_command(script)
        results.append({
            "day": day_name,
            "focus": step["focus"],
            "criteria": step["criteria"],
            "passed": passed,
            "output": stdout,
            "error": stderr,
        })

        if passed:
            print(f"  --> {day_name} PASSED: All criteria verified.")
        else:
            print(f"  --> {day_name} FAILED!")
            print(f"STDOUT:\n{stdout}")
            print(f"STDERR:\n{stderr}")
            all_passed = False

    print("\n" + "=" * 80)
    print("MASTER ACCEPTANCE CRITERIA COMPLIANCE AUDIT (11/11 CRITERIA)")
    print("=" * 80)
    print(f"{'#':<4} {'Day':<8} {'Acceptance Criterion':<60} {'Status':<10}")
    print("-" * 80)

    criterion_idx = 1
    for r in results:
        day_status = "MET (Y)" if r["passed"] else "FAILED (N)"
        for crit in r["criteria"]:
            print(f"{criterion_idx:<4} {r['day']:<8} {crit:<60} {day_status:<10}")
            criterion_idx += 1

    print("=" * 80)
    if all_passed:
        print("RESULT: 100.0% OF ALL WEEK 5 ACCEPTANCE CRITERIA SATISFIED!")
        print("The Document Extraction Pipeline is production-grade, hardened, and ready for deployment.")
        sys.exit(0)
    else:
        print("RESULT: FAILED! One or more verification criteria were not satisfied.")
        sys.exit(1)


if __name__ == "__main__":
    main()
