"""
tool_choice_demo.py
===================
Deep-Dive on `tool_choice` Configuration Modes (Day 4 - Session 1)

Responsibilities:
Demonstrates and compares the 4 distinct behaviors of `tool_choice`:
1. `tool_choice="auto"`:
   - Default behavior.
   - Model autonomously decides whether to answer via text or request a tool.
2. `tool_choice="none"`:
   - Completely disables tool calling.
   - Forces the model to respond purely with its internal parametric weights,
     even if the user asks for real-time data or heavy math.
3. `tool_choice="required"`:
   - Mandates that the model MUST call at least one tool.
   - Model is forbidden from returning a plain text answer on Turn 1.
4. Forced Specific Tool `tool_choice={"type": "function", "function": {"name": "..."}}`:
   - Pinpoints exactly which tool must be invoked.
"""

import time
from typing import Dict, Any, Union
from tool_caller import ToolCallingAgent


def run_tool_choice_comparisons():
    print("=" * 85)
    print(" EXPERIMENT: COMPARING THE 4 MODES OF 'tool_choice'")
    print("=" * 85)

    agent = ToolCallingAgent()

    # -----------------------------------------------------------------------
    # Experiment 1: tool_choice="auto" (Adaptive Decision Making)
    # -----------------------------------------------------------------------
    print("\n" + "-" * 85)
    print(" 1. MODE: tool_choice='auto' (Default - Autonomous Routing)")
    print("-" * 85)
    
    q_math = "Calculate (450 * 12) + 85."
    print(f"Prompt A (Math): '{q_math}'")
    res_math = agent.run(q_math, tool_choice="auto")
    print(f"  -> Model Decision: Called tool '{res_math.tool_called}' with args {res_math.tool_arguments}")
    print(f"  -> Answer: {res_math.final_answer.strip()}")

    time.sleep(2.0)
    q_text = "What is photosynthesis in one short sentence?"
    print(f"\nPrompt B (General Knowledge): '{q_text}'")
    res_text = agent.run(q_text, tool_choice="auto")
    print(f"  -> Model Decision: Tool called = {res_text.tool_called} (Turn count = {res_text.turn_count})")
    print(f"  -> Answer: {res_text.final_answer.strip()}")

    # -----------------------------------------------------------------------
    # Experiment 2: tool_choice="none" (Tools Disabled)
    # -----------------------------------------------------------------------
    print("\n" + "-" * 85)
    print(" 2. MODE: tool_choice='none' (Tools Disabled - Parametric Weights Only)")
    print("-" * 85)
    q_force_text = "What is the exact square root of 987654321?"
    print(f"Prompt: '{q_force_text}' with tool_choice='none'")
    res_none = agent.run(q_force_text, tool_choice="none")
    print(f"  -> Tool called: {res_none.tool_called}")
    print(f"  -> Direct Response (Model cannot use calculator):\n     {res_none.final_answer.strip()[:180]}...")

    # -----------------------------------------------------------------------
    # Experiment 3: tool_choice="required" (Mandatory Tool Execution)
    # -----------------------------------------------------------------------
    print("\n" + "-" * 85)
    print(" 3. MODE: tool_choice='required' (Model Forced to Call A Tool)")
    print("-" * 85)
    q_simple = "Tell me a random fun fact."
    print(f"Prompt: '{q_simple}' with tool_choice='required'")
    res_req = agent.run(q_simple, tool_choice="required")
    print(f"  -> Tool called: '{res_req.tool_called}' (Arguments: {res_req.tool_arguments})")
    print(f"  -> Final Answer: {res_req.final_answer.strip()[:180]}...")

    # -----------------------------------------------------------------------
    # Experiment 4: Forced Specific Tool (Pinpointing Function)
    # -----------------------------------------------------------------------
    print("\n" + "-" * 85)
    print(" 4. MODE: Forced Specific Tool ('get_current_time')")
    print("-" * 85)
    forced_choice = {"type": "function", "function": {"name": "get_current_time"}}
    q_forced = "Tell me what you think of artificial intelligence."
    print(f"Prompt: '{q_forced}' with forced tool 'get_current_time'")
    res_forced = agent.run(q_forced, tool_choice=forced_choice)
    print(f"  -> Tool called: '{res_forced.tool_called}' (Arguments: {res_forced.tool_arguments})")
    print(f"  -> Final Answer: {res_forced.final_answer.strip()[:180]}...")


if __name__ == "__main__":
    run_tool_choice_comparisons()
