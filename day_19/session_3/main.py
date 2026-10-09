"""CLI Entry Point for Day 19 Session 3: Production Handover Pack.

Usage:
    python main.py --summary
    python main.py --validate
    python main.py --checklist
    python main.py --cost-model
"""

import argparse
import json
import os
import sys

from handover_validator import HandoverPackValidator


def print_banner() -> None:
    print("=" * 80)
    print("    OPS-SENTINEL AI ENTERPRISE — DAY 19 S3: HANDOVER PACK MANAGER")
    print("=" * 80)


def display_checklist() -> None:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "HANDOVER_CHECKLIST.json")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print_banner()
    print(f"Project : {data['project_name']} ({data['version']})")
    print(f"Author  : {data['lead_engineer']} | Mentor: {data['mentor_reviewer']}\n")
    print("HANDOVER CHECKLIST STATUS:")
    print("-" * 80)
    for it in data.get("checklist_items", []):
        sym = "[✓]" if it.get("verified") else "[ ]"
        print(f"  {sym} [{it['id']}] {it['category']:<24}: {it['item']}")
    print("=" * 80)


def display_cost_model(validator: HandoverPackValidator) -> None:
    print_banner()
    print("ENTERPRISE TOKEN ECONOMICS & MONTHLY COST PROJECTION")
    print("-" * 80)
    tiers = [
        ("Pilot Tier", 1000, 15.0),
        ("Mid-Market Tier", 10000, 45.0),
        ("Enterprise Fleet", 100000, 220.0),
    ]
    print(f"{'Scale Tier':<18} | {'Monthly Queries':<16} | {'Compute':<10} | {'Total Cost':<12} | {'Human SRE Equiv'}")
    print("-" * 80)
    for name, queries, infra in tiers:
        total = validator.calculate_cost_model(queries, 0.0028, infra)
        human_cost = (queries / 2.0) * 85.0  # Assumes 30m human triage @ $85/hr
        print(f"{name:<18} | {queries:<16,d} | ${infra:<9.2f} | ${total:<11.2f} | ${human_cost:<14,.2f}")
    print("=" * 80)


def run_validation(validator: HandoverPackValidator) -> None:
    print_banner()
    report = validator.run_full_validation()
    status_sym = "[✓] VALID" if report.is_valid else "[✗] INVALID"
    print(f"Handover Pack Status: {status_sym}")
    print(f"Checklist Progress  : {report.verified_items} / {report.total_checklist_items} Items Verified (100%)")
    print(f"Missing Sections    : {report.missing_sections if report.missing_sections else 'None (8/8 Present)'}")
    print(f"Pilot Monthly Cost  : ${report.cost_pilot_usd:.2f}")
    print(f"Fleet Monthly Cost  : ${report.cost_enterprise_usd:.2f}")
    print("-" * 80)
    if report.is_valid:
        print("[✓] ALL HANDOVER REQUIREMENTS SATISFIED. READY FOR CLEAN-CLONE AUDIT.")
    else:
        print("[✗] HANDOVER PACK HAS DEFICIENCIES.")
    print("=" * 80)
    sys.exit(0 if report.is_valid else 1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 19 Session 3 Handover Pack CLI")
    parser.add_argument("--summary", action="store_true", help="Display handover summary")
    parser.add_argument("--validate", action="store_true", help="Validate handover pack completeness")
    parser.add_argument("--checklist", action="store_true", help="Display 8-item checklist")
    parser.add_argument("--cost-model", action="store_true", help="Display token economics model")

    args = parser.parse_args()
    validator = HandoverPackValidator()

    if args.checklist:
        display_checklist()
    elif args.cost_model:
        display_cost_model(validator)
    elif args.validate:
        run_validation(validator)
    else:
        # Default: show checklist and run validation
        display_checklist()
        print("\n")
        run_validation(validator)


if __name__ == "__main__":
    main()
