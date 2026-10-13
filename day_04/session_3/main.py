"""
Day 04 - Session 03: Multi-Step Tool Use & Context Compaction
Demonstrates:
  1. Multi-step tool chaining (DB query -> File read -> Calculator -> Email)
  2. Turn-by-turn agent loop logging
  3. Token growth curve analysis across conversational turns
"""

from multi_step_agent import MultiStepToolAgent


def main():
    print("=== Day 4 Session 3: Multi-Step Tool Agent ===")
    agent = MultiStepToolAgent(enable_compaction=True)

    query = (
        "Find the highest-paid engineer in the database, calculate their monthly bonus (15% of annual salary / 12), "
        "and email them the bonus notification."
    )
    print(f"Goal: '{query}'\n")

    telemetry = agent.run(query)

    print("\nExecution Summary:")
    print(f"  Turns executed: {len(telemetry.step_logs)}")
    print(f"  Final answer:   {telemetry.final_answer.strip()}")

    print("\nToken Growth Curve:")
    for entry in telemetry.token_growth_curve:
        print(f"  Step #{entry['step']}: {entry['message_count']} messages, {entry['total_tokens']} tokens ({entry['event']})")


if __name__ == "__main__":
    main()
