"""
Quick test runner for Week 5 Document Extraction Pipeline.
Can be executed from any directory:
    python run_tests.py
"""
import sys
from pathlib import Path
import unittest

def main():
    # Resolve week5 root directory regardless of current working directory
    week5_dir = Path(__file__).resolve().parent
    tests_dir = week5_dir / "tests"

    if not tests_dir.exists():
        print(f"Error: tests directory not found at {tests_dir}")
        sys.exit(1)

    print(f"Running Document Extraction Pipeline tests from: {tests_dir}")
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=str(tests_dir), pattern="test_*.py", top_level_dir=str(week5_dir))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    sys.exit(0 if result.wasSuccessful() else 1)

if __name__ == "__main__":
    main()
