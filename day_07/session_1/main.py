"""
Day 07 - Session 01: Agent Fundamentals
Compares a deterministic workflow (chain) with an autonomous ReAct loop in plain Python.
"""

from __future__ import annotations
import time
from dotenv import load_dotenv

load_dotenv()

from react_agent import BareReActAgent, search, calculate


def run_workflow_example():
    """Deterministic Workflow: The exact sequence (search -> compute -> format) is hardcoded."""
    print("\n--- 1. Deterministic Workflow (Chain) ---")
    start = time.perf_counter()

    # Step 1: Fixed retrieval
    c_fact = search("curiosity rover")
    j_fact = search("james webb")

    # Step 2: Fixed calculation
    diff = calculate("2021 - 2012")

    # Step 3: Fixed output
    answer = f"According to NASA logs, {diff} years passed between Curiosity (2012) and JWST (2021)."
    elapsed_ms = (time.perf_counter() - start) * 1000

    print(f"Result: {answer}")
    print(f"Time: {elapsed_ms:.2f} ms | LLM calls: 0 (deterministic & zero failure risk)")


def run_react_agent_example():
    """Autonomous ReAct Agent: The LLM dynamically decides when to search and calculate."""
    print("\n--- 2. Autonomous ReAct Agent Loop ---")
    question = "How many years elapsed between the Apollo 11 moon landing and the launch of the James Webb Space Telescope (JWST)?"
    print(f"Question: '{question}'")

    agent = BareReActAgent()
    start = time.time()
    answer = agent.run(question, max_turns=5)
    elapsed = time.time() - start

    print(f"\nFinal Answer (in {elapsed:.2f}s):\n{answer}")


def main():
    print("Day 07 Session 01: Comparing Workflows vs Autonomous Agents")
    run_workflow_example()
    run_react_agent_example()


if __name__ == "__main__":
    main()
