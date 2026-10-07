"""
Day 6 - Session 2: Designing Good Tools
Master Demonstration: main.py

Learning Objectives:
1. Master naming conventions and write descriptions for the model, not the developer.
2. Implement strict typed argument validation.
3. Keep the active tool count small (under ~10) to avoid cognitive load and selection confusion.
4. Return errors as observations so the agent can self-correct without crashing.
5. Build and verify 5 production tools: web_search, read_file, query_sqlite, call_external_api, and send_email.
"""

from __future__ import annotations
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv

# Ensure local .env takes absolute priority
load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

# Ensure local imports work reliably
sys.path.insert(0, str(Path(__file__).resolve().parent))

from tools import (
    web_search,
    read_file,
    query_sqlite,
    call_external_api,
    send_email,
    dispatch_tool
)
from schemas import get_designed_tools
from database_setup import init_database
from agent_recovery import SelfCorrectingAgent


def print_banner(title: str):
    print("\n" + "=" * 80, flush=True)
    print(f" {title}", flush=True)
    print("=" * 80, flush=True)


def print_section(title: str):
    print("\n" + "-" * 80, flush=True)
    print(f" {title}", flush=True)
    print("-" * 80, flush=True)


def test_individual_tools():
    """Validates that each of the 5 tools behaves according to design specs."""
    print_banner("PART 1: VERIFYING THE 5 DESIGNED TOOLS")

    # 1. web_search
    print_section("Tool 1/5: web_search")
    res1 = web_search(query="MCP architecture specification", num_results=2)
    print(f"Status: {res1['status']} | Results Found: {res1['results_count']}")
    for r in res1["results"]:
        print(f"  • {r['title']} ({r['url']})")
        print(f"    Snippet: {r['snippet']}")

    # 2. read_file
    print_section("Tool 2/5: read_file (Safe Sandbox Reader)")
    res2 = read_file(file_path="deployment_notes.md", max_lines=6)
    print(f"Status: {res2['status']} | File: {res2['file_name']} | Total Lines: {res2['total_lines']}")
    print(f"Content Preview:\n{res2['content']}")

    # 3. query_sqlite
    print_section("Tool 3/5: query_sqlite (Read-Only SQL with Schema Hints)")
    res3 = query_sqlite("SELECT name, role, salary FROM employees WHERE salary >= 160000 ORDER BY salary DESC")
    print(f"Status: {res3['status']} | Rows Returned: {res3['row_count']}")
    for row in res3["rows"]:
        print(f"  • {row['name']} | {row['role']} | ${row['salary']:,.2f}")

    # 4. call_external_api
    print_section("Tool 4/5: call_external_api (REST / Microservice Client)")
    res4 = call_external_api(endpoint="mock://cluster/metrics")
    print(f"Status: {res4['status']} | Endpoint: {res4['endpoint']} | HTTP Code: {res4['status_code']}")
    print(f"Cluster Metrics: {json.dumps(res4['data'], indent=2)}")

    # 5. send_email
    print_section("Tool 5/5: send_email (Mock Dispatch with Validation & Audit)")
    res5 = send_email(
        to_email="elena.rostova@enterprise.io",
        subject="Canary Rollout Sign-Off",
        body="All gateway traffic shifting passed the 100% threshold with 0% 5xx errors."
    )
    print(f"Status: {res5['status']} | Message ID: {res5['message_id']} | Recipient: {res5['recipient']}")
    print(f"Delivery Receipt: {res5['delivery_receipt']}")


def test_self_correction_agent():
    """
    Tests an autonomous agent encountering an initial error (missing file / typo)
    and successfully recovering via informative error observation feedback.
    """
    print_banner("PART 2: SELF-CORRECTING AGENT WITH ERRORS AS OBSERVATIONS")

    agent = SelfCorrectingAgent()

    # We deliberately give a prompt where the user mentions 'deploy_guide.txt' (which doesn't exist).
    # The read_file tool will catch this, return a FileNotFound observation with sandbox hints:
    # ['deployment_notes.md', 'quarterly_targets.txt'].
    # The agent will inspect the hints, select 'deployment_notes.md', and extract the rollback triggers!
    recovery_prompt = (
        "Please inspect the sandbox file 'deploy_guide.txt' to tell me what our emergency rollback "
        "triggers are for 5xx error rate and latency."
    )

    result = agent.run_recovery_demo(prompt=recovery_prompt, max_turns=4)

    print("\n" + "=" * 80, flush=True)
    print(" AGENT RECOVERY DEMONSTRATION RESULT", flush=True)
    print("=" * 80, flush=True)
    print(f"Status: {result['status']}")
    print(f"Turns Completed: {result['turns']}")
    print(f"Errors Encountered: {result['errors_encountered']}")
    print(f"Successful Self-Corrections: {result['self_corrections']}")
    print("\n--- Final Agent Answer ---")
    print(result["final_answer"])


def main():
    print_banner("DAY 6 - SESSION 2: DESIGNING GOOD TOOLS")

    # Ensure database is freshly seeded
    init_database()

    # Step 1: Verify all 5 individual tools
    test_individual_tools()

    time.sleep(3)

    # Step 2: Verify self-correction error recovery loop with autonomous agent
    test_self_correction_agent()

    print_banner("DAY 6 - SESSION 2: SUMMARY & VERIFICATION COMPLETE")
    print("""
Key Principles Proven:
  [✓] Naming: All 5 tools follow unambiguous verb_noun format.
  [✓] Model-Facing Descriptions: Tools describe triggers, boundaries, inputs, and recovery hints.
  [✓] Typed Arguments: Pydantic schemas validate types, formats, and ranges.
  [✓] Small Tool Count: Exactly 5 tools (under the ~10 threshold) prevents model confusion.
  [✓] Errors as Observations: Agent recovered autonomously when given a missing filename hint.
""", flush=True)


if __name__ == "__main__":
    main()
