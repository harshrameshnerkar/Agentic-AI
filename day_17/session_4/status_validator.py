"""
Day 17 - Session 4: Progress Update
Status Validator: Enforces strict adherence to the 5-line executive update format.
"""

import os
import sys
from typing import List, Tuple, Dict, Any

# Set UTF-8 encoding for Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def validate_status_file(filepath: str) -> Tuple[bool, List[str], List[str]]:
    """
    Validates that a file contains exactly 5 lines, each satisfying the required fields:
    Line 1: What shipped
    Line 2: Current pass rate
    Line 3: Cost per query
    Line 4: What is at risk
    Line 5: What decision is needed
    """
    if not os.path.exists(filepath):
        return False, [], [f"File '{filepath}' not found."]

    with open(filepath, "r", encoding="utf-8") as f:
        raw_lines = [line.strip() for line in f if line.strip()]

    errors = []
    if len(raw_lines) != 5:
        errors.append(f"Format violation: File must contain exactly 5 lines (found {len(raw_lines)}).")

    required_keywords = [
        ("shipped", "Line 1 must describe what shipped"),
        ("pass rate", "Line 2 must report current pass rate"),
        ("cost", "Line 3 must state cost per query"),
        ("risk", "Line 4 must identify what is at risk"),
        ("decision", "Line 5 must request a required decision")
    ]

    for idx, (kw, err_msg) in enumerate(required_keywords):
        if idx < len(raw_lines):
            if kw not in raw_lines[idx].lower():
                errors.append(f"{err_msg} (keyword '{kw}' missing from line {idx + 1}).")

    is_valid = len(errors) == 0
    return is_valid, raw_lines, errors


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    status_file = os.path.join(current_dir, "5_LINE_STATUS_UPDATE.txt")
    valid, lines, errors = validate_status_file(status_file)

    print("=" * 80)
    print(" DAY 17 - SESSION 4: 5-LINE EXECUTIVE STATUS UPDATE VALIDATOR")
    print("=" * 80)
    if valid:
        print("[✓] Status update passed all 5 strict validation checks:")
        print("-" * 80)
        for idx, line in enumerate(lines, 1):
            print(f"  Line {idx}: {line}")
        print("-" * 80)
        print("[✓] Exactly 5 lines verified. Ready for mentor sign-off.")
    else:
        print("[✗] Validation failed with errors:")
        for e in errors:
            print(f"  - {e}")
    print("=" * 80)
