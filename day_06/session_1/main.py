"""
Day 06 - Session 01: How Tool Calling Works
Demonstrates:
  1. Single tool call execution loop (get_time)
  2. Parallel tool calling (get_time + calculator in one turn)
  3. tool_choice modes ('auto', 'none', and forced function)
"""

import time
from tool_loop import ToolLoopTracer


def main():
    print("=== Day 6 Session 1: Tool Calling Lifecycle ===")
    tracer = ToolLoopTracer()

    # 1. Single tool call
    print("\n1. Single Tool Execution (get_time):")
    p1 = "What is the current time in Tokyo, Japan, and what day of the week is it?"
    r1 = tracer.run_trace(user_prompt=p1, tool_choice="auto")
    print(f"   Tools requested: {r1.tool_calls_requested}")

    time.sleep(1.0)

    # 2. Parallel tool calling (Time + Calculator in one turn)
    print("\n2. Parallel Tool Calling (Time + Calculator):")
    p2 = "What is the current time in New York and what is (8500 * 1.18) - 450?"
    r2 = tracer.run_trace(user_prompt=p2, tool_choice="auto")
    print(f"   Tools requested: {r2.tool_calls_requested}")

    time.sleep(1.0)

    # 3. Tool choice controls
    print("\n3. Testing tool_choice='none' (No tools allowed):")
    p3 = "What is 150 * 12 + 400?"
    r3 = tracer.run_trace(user_prompt=p3, tool_choice="none")
    print(f"   Tools requested: {r3.tool_calls_requested} (Expected: 0)")


if __name__ == "__main__":
    main()
