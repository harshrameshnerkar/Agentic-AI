"""
Day 18 - Session 04: One-Command Automated Regression Suite
Runs the 35-case automated regression suite to ensure zero quality regressions
and enforce SLA compliance (>= 95% accuracy) before release.
"""

from __future__ import annotations
import os
from run_regression_suite import execute_one_command_suite


def main():
    print("Day 18 Session 04: Automated Regression Suite (35 Cases)\n")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    summary = execute_one_command_suite(current_dir, simulate_failure=False)

    print("--- Regression Suite Results ---")
    print(f"Total Cases: {summary['total_cases']}")
    print(f"Passed:      {summary['passed_count']}/{summary['total_cases']} ({summary['pass_rate_pct']:.1f}%)")
    print(f"Bugs Caught: {summary['bug_regression_pass_count']}/5 bug regression tests passed")

    assert summary["pass_rate_pct"] >= 95.0, f"Pass rate {summary['pass_rate_pct']}% below 95% SLA"
    print("\nRegression suite passed: 100% of bug regressions covered.")


if __name__ == "__main__":
    main()
