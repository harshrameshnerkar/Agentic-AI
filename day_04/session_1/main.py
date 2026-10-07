"""
main.py
=======
DAY 4 — SESSION 1: TOOL & FUNCTION CALLING MASTER WALKTHROUGH
============================================================

Learning Objectives Covered:
1. How the model requests a tool (emitting structured JSON, finish_reason="tool_calls")
2. JSON Schema Definitions (specifying function name, semantic descriptions, parameter types)
3. tool_choice modes ('auto', 'none', 'required', and forced specific function)
4. The 3-Turn Request -> Execute -> Return Result loop
5. Why the model never runs code itself (Brain/Planner vs. Host/Hands)
6. Task Verification: Confirming the model calls the right tool (calculator vs. get_current_time vs. none)
"""

import sys
import time

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from schemas import format_schema_summary
from tool_caller import ToolCallingAgent
from tool_choice_demo import run_tool_choice_comparisons
from evaluator import run_evaluation


def print_header(title: str):
    print("\n" + "=" * 85)
    print(f" {title}")
    print("=" * 85)


def main():
    print_header("DAY 4 — SESSION 1: TOOL & FUNCTION CALLING")
    print(
        """
CORE CONCEPTUAL FOUNDATION:
---------------------------
Question: Why does the model NEVER run code itself?
Answer:
1. LLMs are neural probability engines that map input tokens to output tokens.
   They run in a remote inference cluster with zero access to your local CPU,
   operating system, filesystem, network sockets, or system clock.
2. The model acts strictly as the 'BRAIN' (Planner):
   - It reads your prompt and understands what information is missing.
   - It inspects the provided JSON Schemas.
   - It outputs an intentional structured payload saying: "Please run tool X with arguments Y".
3. The host program (our Python code) acts as the 'HANDS' (Executor):
   - It intercepts the model's tool call.
   - It runs the actual Python code (e.g. calculator or clock).
   - It returns the raw result back to the model with a matching tool_call_id.
"""
    )

    # -----------------------------------------------------------------------
    # STAGE 1: JSON SCHEMA DEFINITIONS
    # -----------------------------------------------------------------------
    print_header("[STAGE 1: JSON SCHEMA DEFINITIONS] How the Model Learns About Tools")
    print(
        "Before making an API call, we register tools using JSON Schema.\n"
        "The model uses the 'description' to understand when to invoke the tool,\n"
        "and 'parameters' to format the arguments correctly:\n"
    )
    print(format_schema_summary())

    # -----------------------------------------------------------------------
    # STAGE 2: THE 3-TURN EXECUTION LOOP
    # -----------------------------------------------------------------------
    print_header("[STAGE 2: THE 3-TURN EXECUTION LOOP] Request -> Execute -> Return")
    agent = ToolCallingAgent()

    # Step A: Calculator
    q_math = "A client booked a conference room for $4,500. With a 15% service tax, what is the total cost?"
    print(f"\nScenario A (Math Query): '{q_math}'")
    tel_math = agent.run(q_math)
    print(f"  Turn 1 (Model Request): Function='{tel_math.tool_called}' | Args={tel_math.tool_arguments}")
    print(f"  Turn 2 (Python Exec):   Output={tel_math.tool_raw_output}")
    print(f"  Turn 3 (Synthesized):   {tel_math.final_answer.strip()}")
    print(f"  Telemetry: {tel_math.turn_count} turns in {tel_math.latency_ms:.1f}ms")

    time.sleep(2.5)

    # Step B: Get Current Time
    q_time = "What is the current time in IST (Indian Standard Time) right now?"
    print(f"\nScenario B (Time Query): '{q_time}'")
    tel_time = agent.run(q_time)
    print(f"  Turn 1 (Model Request): Function='{tel_time.tool_called}' | Args={tel_time.tool_arguments}")
    print(f"  Turn 2 (Python Exec):   Output={tel_time.tool_raw_output}")
    print(f"  Turn 3 (Synthesized):   {tel_time.final_answer.strip()}")
    print(f"  Telemetry: {tel_time.turn_count} turns in {tel_time.latency_ms:.1f}ms")

    time.sleep(2.5)

    # Step C: Conversational (No Tool)
    q_chat = "What is the difference between a synchronous and asynchronous function?"
    print(f"\nScenario C (Direct Text Query): '{q_chat}'")
    tel_chat = agent.run(q_chat)
    print(f"  Turn 1 (Direct Text):   {tel_chat.final_answer.strip()[:200]}...")
    print(f"  Telemetry: {tel_chat.turn_count} turn in {tel_chat.latency_ms:.1f}ms (No tool needed)")

    time.sleep(2.5)

    # -----------------------------------------------------------------------
    # STAGE 3: TOOL CHOICE MODES COMPARISON
    # -----------------------------------------------------------------------
    print_header("[STAGE 3: TOOL_CHOICE MODES] auto vs none vs required vs forced")
    run_tool_choice_comparisons()

    time.sleep(2.5)

    # -----------------------------------------------------------------------
    # STAGE 4: AUTOMATED CONFIRMATION & ROUTING EVALUATION
    # -----------------------------------------------------------------------
    print_header("[STAGE 4: AUTOMATED EVALUATION] Confirming Model Calls the Right Tool")
    scorecard = run_evaluation()

    print_header("SESSION 1 COMPLETE")
    print(
        f"✓ Successfully verified JSON schema construction\n"
        f"✓ Successfully executed 3-turn request -> execute -> return result loop\n"
        f"✓ Successfully compared tool_choice modalities\n"
        f"✓ Confirmed {scorecard['accuracy_pct']:.1f}% routing accuracy between calculator and get_current_time!\n"
    )


if __name__ == "__main__":
    main()
