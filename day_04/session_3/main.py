"""
main.py
=======
Master Walkthrough for Day 4 - Session 3: Multi-Step Tool Use.

Demonstrates:
1. Chaining 3+ tools in sequence (query_database -> read_file -> calculator -> send_email).
2. Turn-by-turn logging of the entire agent loop.
3. Token growth curve analysis.
4. Demonstration of Conversation History Management & Context Compaction.
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import time
from multi_step_agent import MultiStepToolAgent, ExecutionTelemetry


def print_step_table(telemetry: ExecutionTelemetry):
    print("\n" + "=" * 95)
    print("COMPLETE AGENT EXECUTION AUDIT LOG")
    print("=" * 95)
    print(f"{'STEP':<6} | {'TYPE':<18} | {'TOOL / ACTION':<18} | {'TOKENS':<8} | {'DETAILS'}")
    print("-" * 95)

    for log in telemetry.step_logs:
        step_str = f"#{log.step_number}"
        ttype = log.turn_type
        tool = log.tool_name or "-"
        tok = str(log.tokens_at_step)

        if log.arguments:
            detail = f"Args: {str(log.arguments)[:42]}"
        elif log.observation_snippet:
            detail = f"Obs: {log.observation_snippet[:42].replace(chr(10), ' ')}"
        else:
            detail = "-"

        print(f"{step_str:<6} | {ttype:<18} | {tool:<18} | {tok:<8} | {detail}")
    print("=" * 95)


def print_token_growth_curve(telemetry: ExecutionTelemetry):
    print("\n" + "=" * 80)
    print("TOKEN GROWTH TRAJECTORY (Context Expansion Across Turns)")
    print("=" * 80)
    print(f"{'STEP':<6} | {'MESSAGES':<10} | {'TOTAL TOKENS':<14} | {'EVENT'}")
    print("-" * 80)

    for entry in telemetry.token_growth_curve:
        step = f"#{entry['step']}"
        msgs = str(entry['message_count'])
        tokens = str(entry['total_tokens'])
        event = entry['event']
        print(f"{step:<6} | {msgs:<10} | {tokens:<14} | {event}")

    initial = telemetry.token_growth_curve[0]['total_tokens']
    final = telemetry.token_growth_curve[-1]['total_tokens']
    net_growth = final - initial
    print("-" * 80)
    print(f"Initial Context: {initial} tokens -> Final Context: {final} tokens (+{net_growth} tokens growth)")
    print("=" * 80)


def main():
    print("=" * 80)
    print("DAY 4 - SESSION 3: MULTI-STEP TOOL USE & HISTORY MANAGEMENT")
    print("=" * 80)

    # Question requiring at least 3 tools in sequence:
    # 1. query_database: get Marcus Vance's role, department, salary
    # 2. read_file: read bonus_policy.txt to find bonus percentage
    # 3. calculator: calculate 135,000 * multiplier
    # 4. send_email: send notification to finance.payroll@enterprise.io
    chained_query = (
        "Check employee Marcus Vance in the enterprise database to determine his exact role, "
        "department, and annual salary. Next, read 'bonus_policy.txt' to identify the eligible "
        "bonus multiplier percentage for his department and role. Then calculate his exact Q3 "
        "bonus dollar amount using the calculator. Finally, send an approval notification email "
        "to 'finance.payroll@enterprise.io' with the full breakdown (employee name, salary, "
        "bonus percentage, and final bonus amount), and provide a concise final summary."
    )

    agent = MultiStepToolAgent(
        max_turns=8,
        enable_compaction=False
    )

    telemetry = agent.run(chained_query)

    # 1. Print structured audit table of every step in the loop
    print_step_table(telemetry)

    # 2. Print token growth curve
    print_token_growth_curve(telemetry)

    # 3. Verification of Chained Execution
    print("\nVERIFICATION SCORECARD:")
    print(f"  * Tools Executed In Sequence: {' -> '.join(telemetry.tools_executed)}")
    print(f"  * Total Tools Used: {len(telemetry.tools_executed)} (Requirement: >= 3 tools)")
    print(f"  * Total Step Audits: {telemetry.total_steps}")
    print(f"  * Execution Latency: {telemetry.execution_time_sec}s")

    assert len(telemetry.tools_executed) >= 3, "Failed: Fewer than 3 tools were executed!"
    print("  [OK] SUCCESS: Chained multi-step tool sequence executed and verified!")


if __name__ == "__main__":
    main()
