"""
Day 19 - Session 03: Production Handover Pack
Validates the operational handover pack: operations runbooks,
troubleshooting guides, architecture diagrams, and cost models.
"""

from __future__ import annotations
from handover_validator import HandoverPackValidator


def main():
    print("Day 19 Session 03: Production Handover Pack Validation\n")
    validator = HandoverPackValidator()
    results = validator.validate_all_artifacts()

    print("Handover Pack Artifacts:")
    for a in results:
        status = "PASSED" if a.passed else "FAILED"
        print(f"  • {a.name:<25}: {status} ({a.details})")

    all_passed = all(a.passed for a in results)
    assert all_passed is True, "One or more handover artifacts failed validation!"
    print("\nHandover pack complete and validated for operations team.")


if __name__ == "__main__":
    main()
