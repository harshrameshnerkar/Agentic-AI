"""CLI Entry Point for Day 20 Session 2: Results & Limitations Report.

Usage:
    python main.py --summary
    python main.py --verify-sla
    python main.py --metrics
    python main.py --limitations
"""

import argparse
import json
import os
import sys

from report_generator import ResultsReportManager


def print_banner() -> None:
    print("=" * 85)
    print("    OPS-SENTINEL AI ENTERPRISE — DAY 20 S2: RESULTS & LIMITATIONS REPORT")
    print("=" * 85)


def display_summary(mgr: ResultsReportManager) -> None:
    metrics = mgr.load_metrics()
    charter = metrics.get("charter_comparison", {})

    print_banner()
    print(f"Title   : {metrics.get('report_title')}")
    print(f"Author  : {metrics.get('author')} | Lead Architect: {metrics.get('lead_architect')}\n")
    print("DAY 16 CHARTER SLA VS PRODUCTION BENCHMARK:")
    print("-" * 85)
    print(f"{'Metric Dimension':<28} | {'Target SLA':<14} | {'Measured Value':<16} | {'Status'}")
    print("-" * 85)
    for k, v in charter.items():
        dim_name = k.replace("_", " ").title()
        tgt = f"{v['target_sla']} {v['unit']}"
        meas = f"{v['measured_value']} {v['unit']}"
        print(f"{dim_name:<28} | {tgt:<14} | {meas:<16} | [✓] {v['status']}")
    print("-" * 85)
    print("STRATIFIED PASS RATE BY INCIDENT CATEGORY:")
    for cat in metrics.get("stratified_pass_rate", []):
        print(f"  • {cat['category']:<30}: {cat['passed_cases']}/{cat['total_cases']} cases ({cat['pass_rate_pct']}%)")
    print("=" * 85)


def display_limitations(mgr: ResultsReportManager) -> None:
    metrics = mgr.load_metrics()
    print_banner()
    print("HONEST OPERATIONAL LIMITATIONS & BOUNDARY DISCLOSURES:\n")
    for idx, lim in enumerate(metrics.get("honest_limitations", []), 1):
        print(f"  {idx}. {lim}")
    print("\nSCOPE VARIANCE (PRUNED COMPONENT):")
    sc = metrics.get("scope_cut_summary", {})
    print(f"  • Item       : {sc.get('item')}")
    print(f"  • Rationale  : {sc.get('rationale')}")
    print("=" * 85)


def verify_slas(mgr: ResultsReportManager) -> None:
    print_banner()
    res = mgr.verify_charter_slas()
    status_sym = "[✓] ALL SLAS SATISFIED" if res.all_slas_met else "[✗] SLA VIOLATION"
    print(f"Verification Verdict       : {status_sym}")
    print(f"Golden Cases Evaluated     : {res.total_golden_cases} cases across {res.stratified_categories} categories")
    print(f"Pass Rate SLA (>= 95.0%)   : {'PASS' if res.pass_rate_ok else 'FAIL'}")
    print(f"P95 Latency SLA (<= 90s)   : {'PASS' if res.latency_ok else 'FAIL'}")
    print(f"Cost Ceiling (<= $0.150)   : {'PASS' if res.cost_ok else 'FAIL'}")
    print(f"Zero Regressions Preserved : {'PASS' if res.regressions_ok else 'FAIL'}")
    print(f"Documented Limitations     : {res.limitations_count} items")
    print("=" * 85)
    sys.exit(0 if res.all_slas_met else 1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 20 Session 2 Results & Limitations CLI")
    parser.add_argument("--summary", action="store_true", help="Display executive charter summary")
    parser.add_argument("--verify-sla", action="store_true", help="Assert that all SLAs are satisfied")
    parser.add_argument("--limitations", action="store_true", help="Display honest limitations disclosures")
    parser.add_argument("--metrics", action="store_true", help="Display full metrics JSON")

    args = parser.parse_args()
    mgr = ResultsReportManager()

    if args.verify_sla:
        verify_slas(mgr)
    elif args.limitations:
        display_limitations(mgr)
    elif args.metrics:
        print(json.dumps(mgr.load_metrics(), indent=2))
    else:
        # Default: summary + limitations + SLA verification
        display_summary(mgr)
        print("\n")
        display_limitations(mgr)
        print("\n")
        verify_slas(mgr)


if __name__ == "__main__":
    main()
