"""
Day 19 - Session 04: Clean-Clone Sandbox Verification
Verifies that the repository can be cleanly cloned, set up, and verified
without interactive prompts or missing dependencies.
"""

from __future__ import annotations
from clean_clone_runner import CleanCloneSandboxRunner


def main():
    print("Day 19 Session 04: Clean-Clone Sandbox Audit\n")
    runner = CleanCloneSandboxRunner()
    result = runner.run_sandbox_simulation()

    print(f"Files Audited:               {result.files_audited}")
    print(f"Blocking Interactive Prompts: {result.interactive_prompts_found} (Expected: 0)")
    print(f"Doc Bugs Resolved:           {result.doc_bugs_resolved}")
    print(f"Setup Simulation Duration:   {result.setup_duration_sec}s")
    print(f"Audit Verdict:               {result.verdict}")

    assert result.is_success is True, "Clean clone audit failed!"
    print("\nClean-clone verification passed: Repository is 100% reproducible.")


if __name__ == "__main__":
    main()
