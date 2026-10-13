"""
Day 17 - Session 04: Executive Progress Update
Validates and prints the concise 5-line written status update to mentor Dr. Elena Rostova.
"""

from __future__ import annotations
import os
from status_validator import validate_status_file


def main():
    print("Day 17 Session 04: Executive Progress Update\n")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    status_file = os.path.join(current_dir, "5_LINE_STATUS_UPDATE.txt")

    valid, lines, errors = validate_status_file(status_file)
    print("Official 5-Line Written Status Update:")
    for idx, line in enumerate(lines, 1):
        print(f"  [{idx}] {line}")

    assert valid is True, f"Status file validation failed: {errors}"
    print("\nStatus update validated: exactly 5 lines, concise, with measurable metrics.")


if __name__ == "__main__":
    main()
