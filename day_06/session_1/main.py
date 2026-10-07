"""
Day 6 - Session 1: How Tool Calling Works
Master Demonstration: main.py

Learning Objectives:
1. Trace the complete Request -> Execute -> Return tool calling lifecycle.
2. Understand why the model never runs code itself (symbolic intent vs host execution).
3. Inspect JSON schema definitions and typed argument validation.
4. Master tool_choice controls ('auto', 'none', and forced specific function).
5. Demonstrate parallel tool execution (multiple tools requested in a single turn).
"""

from __future__ import annotations
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import os
import time
from pathlib import Path
from dotenv import load_dotenv

# Ensure local imports work reliably
sys.path.insert(0, str(Path(__file__).resolve().parent))

from tool_loop import ToolLoopTracer


def print_banner(title: str):
    print("\n" + "=" * 80, flush=True)
    print(f" {title}", flush=True)
    print("=" * 80, flush=True)


def print_section(title: str):
    print("\n" + "#" * 80, flush=True)
    print(f" SCENARIO: {title}", flush=True)
    print("#" * 80, flush=True)


def main():
    print_banner("DAY 6 - SESSION 1: HOW TOOL CALLING WORKS")

    print("""
[CORE PEDAGOGICAL CONCEPTS COVERED]
  1. The Request -> Execute -> Return Loop:
     Client sends prompt + schemas ➔ Model returns tool_calls ➔ Host runs code ➔ Host returns tool message ➔ Model synthesizes.
  2. Why the Model Never Runs Code:
     LLMs are pure mathematical next-token predictors. They have NO CPU, NO network sockets, NO OS process.
     The model only outputs structured text representing its INTENT; the host executes the real code safely.
  3. JSON Schema Validation:
     Formal types, property descriptions, and required constraints define the function calling interface.
  4. Parallel Tool Calling:
     In a single turn, the model can emit multiple distinct tool calls to resolve independent sub-tasks.
  5. tool_choice Control:
     'auto' (model decides), 'none' (model forbidden from calling tools), or forced specific function.
""", flush=True)

    tracer = ToolLoopTracer()

    # -------------------------------------------------------------------------
    # SCENARIO 1: Single Tool Request -> Execute -> Return (get_time)
    # -------------------------------------------------------------------------
    print_section("1. SINGLE TOOL EXECUTION (get_time)")
    prompt_1 = "What is the current time in Tokyo, Japan, and what day of the week is it?"
    report_1 = tracer.run_trace(user_prompt=prompt_1, tool_choice="auto")

    time.sleep(3)

    # -------------------------------------------------------------------------
    # SCENARIO 2: Parallel Tool Calling (get_time + calculator in ONE Turn)
    # -------------------------------------------------------------------------
    print_section("2. PARALLEL TOOL CALLING (Multi-Tool Dispatch in a Single Turn)")
    prompt_2 = (
        "I need two quick pieces of information: "
        "1. What is the current time in New York? "
        "2. What is (8500 * 1.18) - 450?"
    )
    report_2 = tracer.run_trace(user_prompt=prompt_2, tool_choice="auto")

    time.sleep(3)

    # -------------------------------------------------------------------------
    # SCENARIO 3: tool_choice Controls ('none' vs forced 'calculator')
    # -------------------------------------------------------------------------
    print_section("3. TOOL_CHOICE CONTROLS ('none' vs forced function)")
    prompt_3 = "What is 150 * 12 + 400?"

    print("\n--- 3A. tool_choice='none' (Model FORBIDDEN from calling tools) ---", flush=True)
    report_3a = tracer.run_trace(user_prompt=prompt_3, tool_choice="none")
    print(f"Tools Requested: {report_3a.tool_calls_requested} (Expected: 0)", flush=True)

    time.sleep(3)

    print("\n--- 3B. tool_choice=Forced 'calculator' ---", flush=True)
    forced_choice = {"type": "function", "function": {"name": "calculator"}}
    report_3b = tracer.run_trace(user_prompt=prompt_3, tool_choice=forced_choice)
    print(f"Tools Requested: {report_3b.tool_calls_requested} (Expected: >= 1)", flush=True)

    # -------------------------------------------------------------------------
    # MASTER AUDIT SUMMARY
    # -------------------------------------------------------------------------
    print_banner("DAY 6 - SESSION 1: COMPLETE EXECUTION AUDIT SUMMARY")
    print(f"{'Scenario':<30} | {'tool_choice':<15} | {'Tools Called':<12} | {'Total Duration'}", flush=True)
    print("-" * 75, flush=True)
    print(f"{'1. Single Tool (get_time)':<30} | {'auto':<15} | {report_1.tool_calls_requested:<12} | {report_1.total_duration_sec:.2f}s", flush=True)
    print(f"{'2. Parallel (time + calc)':<30} | {'auto':<15} | {report_2.tool_calls_requested:<12} | {report_2.total_duration_sec:.2f}s", flush=True)
    print(f"{'3A. tool_choice=\"none\"':<30} | {'none':<15} | {report_3a.tool_calls_requested:<12} | {report_3a.total_duration_sec:.2f}s", flush=True)
    print(f"{'3B. Forced calculator':<30} | {'forced':<15} | {report_3b.tool_calls_requested:<12} | {report_3b.total_duration_sec:.2f}s", flush=True)

    print("\n[+] Day 6 - Session 1 master demonstration completed successfully!", flush=True)


if __name__ == "__main__":
    main()
