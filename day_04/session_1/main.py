"""
Day 04 - Session 01: Tool & Function Calling Walkthrough
Demonstrates:
  1. JSON Schema tool registration
  2. 3-Turn execution loop (Model request -> Local Python execution -> Model response)
  3. tool_choice modes ('auto', 'none', 'required', and forced specific function)
"""

import time
from tool_caller import ToolCallingAgent
from tool_choice_demo import run_tool_choice_comparisons
from evaluator import run_evaluation


def main():
    print("=== Day 4 Session 1: Tool & Function Calling ===")
    agent = ToolCallingAgent()

    # 1. Math query requiring calculator
    q_math = "A client booked a conference room for $4,500. With a 15% service tax, what is the total cost?"
    print(f"\n1. Math Query: '{q_math}'")
    tel_math = agent.run(q_math)
    print(f"   Tool called: {tel_math.tool_called}")
    print(f"   Args:        {tel_math.tool_arguments}")
    print(f"   Output:      {tel_math.tool_raw_output}")
    print(f"   Answer:      {tel_math.final_answer.strip()}")

    time.sleep(1.0)

    # 2. Time query requiring clock tool
    q_time = "What is the current time in IST right now?"
    print(f"\n2. Time Query: '{q_time}'")
    tel_time = agent.run(q_time)
    print(f"   Tool called: {tel_time.tool_called}")
    print(f"   Answer:      {tel_time.final_answer.strip()}")

    time.sleep(1.0)

    # 3. Conversational query (no tool needed)
    q_chat = "What is the difference between a synchronous and asynchronous function?"
    print(f"\n3. Conversational Query: '{q_chat}'")
    tel_chat = agent.run(q_chat)
    print(f"   Answer: {tel_chat.final_answer.strip()[:100]}...")

    time.sleep(1.0)

    # 4. Compare tool_choice modes
    print("\n4. Running tool_choice mode comparisons (auto vs none vs required)...")
    run_tool_choice_comparisons()

    # 5. Routing accuracy scorecard
    print("\n5. Running tool selection evaluation...")
    scorecard = run_evaluation()
    print(f"Routing Accuracy: {scorecard['accuracy_pct']:.1f}%")


if __name__ == "__main__":
    main()
