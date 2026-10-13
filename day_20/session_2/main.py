"""
Day 20 - Session 02: Results & Limitations Report
Compares the production benchmark results against the signed-off Day 16 Charter SLAs,
disclosing measured metrics and honest operational limitations.
"""

from __future__ import annotations
from report_generator import ResultsReportManager


def main():
    print("Day 20 Session 02: Results & SLA Verification Report\n")
    mgr = ResultsReportManager()
    metrics = mgr.load_metrics()
    charter = metrics.get("charter_comparison", {})

    print("Day 16 Charter SLA vs Production Benchmark:")
    for k, v in charter.items():
        dim = k.replace("_", " ").title()
        print(f"  • {dim:<26}: Target={v['target_sla']} {v['unit']}, Measured={v['measured_value']} {v['unit']} -> [{v['status']}]")

    is_compliant, failures = mgr.verify_all_slas()
    print(f"\nSLA Compliance Result: {'ALL SLAS SATISFIED' if is_compliant else 'SLA BREACHES'}")
    assert is_compliant is True, f"SLA verification failed: {failures}"


if __name__ == "__main__":
    main()
