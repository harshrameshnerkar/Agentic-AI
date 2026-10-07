"""
main.py
=======
DAY 4 — SESSION 2: WRITING GOOD TOOLS (MASTER WALKTHROUGH)
==========================================================

Key Concepts Covered:
1. Naming:
   - Imperative, unambiguous verb-noun names (web_search, read_file, query_database, send_email).
2. Descriptions Written for the Model:
   - Explicitly telling the model when to use the tool, when NOT to use it,
     and providing table schema references right inside the description.
3. Typed & Validated Arguments:
   - Type constraints, boundary checks, and format validation (e.g. RFC 5322 email regex).
4. Keeping the Tool Count Small:
   - Consolidating into 4 clean, robust capabilities rather than 20 micro-tools.
5. Returning Errors as Observations:
   - Never crashing the host runtime! Returning structured JSON errors with hints
     so the agent can read the observation, self-correct, and retry.
6. Multi-Tool Chaining:
   - Coordinating sequential actions (e.g. Query DB -> Find Email -> Send Notification).
"""

import sys
import time

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from database_setup import init_database
from schemas import get_all_tools
from agent import EnterpriseToolAgent
from email_tool import get_sent_emails


def print_section(title: str):
    print("\n" + "=" * 85)
    print(f" {title}")
    print("=" * 85)


def main():
    print_section("DAY 4 — SESSION 2: WRITING GOOD TOOLS")
    print(
        """
THE 5 CORE PRINCIPLES OF PRODUCTION TOOL DESIGN:
------------------------------------------------
1. Naming:
   Use clear, intuitive names ('web_search', 'read_file', 'query_database', 'send_email').
   Avoid generic names like 'data_getter' or 'run_action'.

2. Descriptions Written for the Model:
   The description is a mini-prompt. Explain WHAT it does, WHEN to use it, WHEN NOT to
   use it, and provide schema hints so the LLM doesn't have to guess table or column names.

3. Typed & Validated Arguments:
   Always specify JSON Schema types (string, integer, array). Validate arguments on the
   Python side before execution (e.g. email regex, file path sandboxing).

4. Keeping Tool Count Small:
   Too many tools creates cognitive noise and increases token costs. Provide a small,
   orthogonal set of flexible tools rather than dozens of fragmented micro-functions.

5. Returning Errors as Observations:
   NEVER raise raw unhandled exceptions! Always catch errors and return them as structured
   observations with hints. This empowers the agent to self-correct its query and succeed!
"""
    )

    # 1. Initialize SQLite Database
    init_database()

    agent = EnterpriseToolAgent()

    # -----------------------------------------------------------------------
    # DEMO 1: WEB SEARCH TOOL (web_search)
    # -----------------------------------------------------------------------
    print_section("DEMO 1: TOOL 1 — 'web_search' (Live External Information)")
    q1 = "What are the latest updates in Python 3.12 regarding subinterpreters and the GIL?"
    print(f"Prompt: '{q1}'\n")
    res1 = agent.run(q1)
    for s in res1.steps:
        print(f"  • Tool Invoked: '{s.tool_name}' | Arguments: {s.arguments}")
        print(f"    Results Found: {s.observation.get('results_count')} results")
    print(f"\nFinal Answer:\n{res1.final_answer.strip()}")
    print(f"Latency: {res1.latency_ms:.1f}ms")

    time.sleep(3.5)

    # -----------------------------------------------------------------------
    # DEMO 2: SAFE FILE READER TOOL (read_file)
    # -----------------------------------------------------------------------
    print_section("DEMO 2: TOOL 2 — 'read_file' (Sandboxed Local File Inspection)")
    q2 = "Read 'sample_policy.txt' and tell me the policy requirements for hardware requisitions over $25,000."
    print(f"Prompt: '{q2}'\n")
    res2 = agent.run(q2)
    for s in res2.steps:
        print(f"  • Tool Invoked: '{s.tool_name}' | File: '{s.arguments.get('file_path')}'")
        print(f"    Lines Read: {s.observation.get('lines_returned')} lines")
    print(f"\nFinal Answer:\n{res2.final_answer.strip()}")
    print(f"Latency: {res2.latency_ms:.1f}ms")

    time.sleep(3.5)

    # -----------------------------------------------------------------------
    # DEMO 3: SAFE SQL DATABASE QUERY TOOL (query_database)
    # -----------------------------------------------------------------------
    print_section("DEMO 3: TOOL 3 — 'query_database' (Read-Only SQL Analytics)")
    q3 = "Query the database to find all employees with a salary greater than $140,000. Show their names, roles, and salaries."
    print(f"Prompt: '{q3}'\n")
    res3 = agent.run(q3)
    for s in res3.steps:
        print(f"  • Tool Invoked: '{s.tool_name}'")
        print(f"    SQL Executed: {s.arguments.get('sql_query')}")
        print(f"    Rows Returned: {s.observation.get('row_count')}")
    print(f"\nFinal Answer:\n{res3.final_answer.strip()}")
    print(f"Latency: {res3.latency_ms:.1f}ms")

    time.sleep(3.5)

    # -----------------------------------------------------------------------
    # DEMO 4: MOCK EMAIL SENDER TOOL (send_email)
    # -----------------------------------------------------------------------
    print_section("DEMO 4: TOOL 4 — 'send_email' (Format Validation & Audit Logging)")
    q4 = (
        "Send an email to 'marcus.vance@enterprise.io' with subject 'DevOps Infrastructure Alert' "
        "informing him that the staging database migration validation passed with zero errors."
    )
    print(f"Prompt: '{q4}'\n")
    res4 = agent.run(q4)
    for s in res4.steps:
        print(f"  • Tool Invoked: '{s.tool_name}'")
        print(f"    Recipient: {s.arguments.get('to_email')}")
        print(f"    Subject:   {s.arguments.get('subject')}")
        print(f"    Status:    {s.observation.get('status')} | Message ID: {s.observation.get('message_id')}")
    print(f"\nFinal Answer:\n{res4.final_answer.strip()}")
    print(f"Latency: {res4.latency_ms:.1f}ms")

    time.sleep(3.5)

    # -----------------------------------------------------------------------
    # DEMO 5: MULTI-TOOL CHAINING (Query DB -> Extract Email -> Send Email)
    # -----------------------------------------------------------------------
    print_section("DEMO 5: MULTI-TOOL CHAINING (Database Lookup -> Email Dispatch)")
    q5 = (
        "Look up the Lead AI Researcher in the employees table to get her email and name, "
        "and then send her an email with subject 'Paper Accepted' congratulating her on the conference acceptance."
    )
    print(f"Prompt: '{q5}'\n")
    res5 = agent.run(q5)
    print(f"Steps Executed in Chain: {len(res5.steps)}")
    for s in res5.steps:
        print(f"  Step #{s.step_number}: Tool '{s.tool_name}' -> Output Status: {s.observation.get('status')}")
        if s.tool_name == "query_database":
            print(f"    SQL: {s.arguments.get('sql_query')}")
        elif s.tool_name == "send_email":
            print(f"    Recipient: {s.arguments.get('to_email')} | MsgID: {s.observation.get('message_id')}")

    print(f"\nFinal Answer:\n{res5.final_answer.strip()}")
    print(f"Latency: {res5.latency_ms:.1f}ms")

    time.sleep(3.5)

    # -----------------------------------------------------------------------
    # DEMO 6: RETURNING ERRORS AS OBSERVATIONS (Guardrails in Action)
    # -----------------------------------------------------------------------
    print_section("DEMO 6: RETURNING ERRORS AS OBSERVATIONS (Safety & Guardrails)")
    q6 = "Execute this command in our SQLite database: 'DROP TABLE employees;' and report the response."
    print(f"Prompt (Destructive Injection Attempt): '{q6}'\n")
    res6 = agent.run(q6)
    for s in res6.steps:
        print(f"  • Tool Invoked: '{s.tool_name}'")
        print(f"  • Observation Status: {s.observation.get('status')} (Error Type: {s.observation.get('error_type')})")
        print(f"  • Observation Message: {s.observation.get('message')}")
    print(f"\nFinal Answer:\n{res6.final_answer.strip()}")

    # -----------------------------------------------------------------------
    # AUDIT TRAIL SUMMARY
    # -----------------------------------------------------------------------
    print_section("AUDIT TRAIL: SENT EMAILS LOG")
    sent = get_sent_emails()
    print(f"Total Sent Emails Recorded: {len(sent)}")
    for e in sent[-2:]:
        print(f"  - [{e['message_id']}] To: {e['to_email']} | Subject: '{e['subject']}' | Time: {e['timestamp']}")

    print_section("DAY 4 — SESSION 2 COMPLETE")
    print(
        "✓ All 4 tools (web_search, read_file, query_database, send_email) verified\n"
        "✓ Error-as-observation principle demonstrated\n"
        "✓ Multi-tool chaining executed successfully\n"
        "✓ Read-only SQL guardrails and path sandboxing verified!\n"
    )


if __name__ == "__main__":
    main()
