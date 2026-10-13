"""
Day 02 - Session 01: Chain-of-Thought & Prompt Chaining
Compares two approaches to solving math & reasoning problems:
  - Method A (Direct): Single-shot asking for final answer directly.
  - Method B (3-Step Chain): Decomposes the task into:
      1. Extract parameters & constraints
      2. Step-by-step arithmetic calculation
      3. Verification & final formatting
"""

import os
import sys
import json
import time
from dotenv import load_dotenv
from openai import OpenAI
from dataset import REASONING_DATASET

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
model = os.getenv("OPENAI_MODEL", "gemini-3.1-flash-lite")

if not api_key:
    raise ValueError("Missing API key in .env")

client = OpenAI(api_key=api_key, base_url=base_url)


def call_llm(prompt: str, system_msg: str = "You are a helpful assistant. Output only JSON.") -> str:
    """Helper function to call the LLM and return the text response."""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        return (response.choices[0].message.content or "{}").strip()
    except Exception as e:
        print(f"API Error: {e}")
        return "{}"


def solve_direct(problem_text: str) -> float:
    """Method A: Ask for the answer directly in one prompt."""
    prompt = f"""Solve this problem. Provide ONLY a JSON object with the final numerical answer.
Problem:
{problem_text}

Format: {{"final_answer": <number>}}"""

    raw = call_llm(prompt)
    try:
        return float(json.loads(raw).get("final_answer", 0.0))
    except Exception:
        return 0.0


def solve_three_step_chain(problem_text: str) -> float:
    """Method B: 3-Step prompt chain (Extract -> Calculate -> Verify)."""
    # Step 1: Extract parameters
    p1 = f"Extract all parameters and numbers from this problem as JSON:\n{problem_text}"
    extracted = call_llm(p1, system_msg="Extract numbers and constraints. Output JSON.")

    # Step 2: Step-by-step arithmetic
    p2 = f"Using these parameters:\n{extracted}\nCalculate the solution step by step as JSON: {{\"intermediate_result\": <number>}}"
    calc = call_llm(p2, system_msg="Calculate intermediate values. Output JSON.")

    # Step 3: Verify and format final answer
    p3 = f"Verify this calculation against the problem:\nProblem: {problem_text}\nCalculation: {calc}\nOutput JSON: {{\"final_answer\": <number>}}"
    verified = call_llm(p3, system_msg="Verify constraints and output final answer in JSON.")

    try:
        return float(json.loads(verified).get("final_answer", 0.0))
    except Exception:
        return 0.0


def main():
    # Use 2 problems by default for speed, or --full for all 6
    problems = REASONING_DATASET if "--full" in sys.argv else REASONING_DATASET[:2]
    print(f"Comparing Direct vs Chain-of-Thought Prompting on {len(problems)} problem(s)...\n")

    for p in problems:
        gt = p["ground_truth"]
        tol = p["tolerance"]

        ans_direct = solve_direct(p["problem"])
        ans_chain = solve_three_step_chain(p["problem"])

        pass_direct = abs(ans_direct - gt) <= tol
        pass_chain = abs(ans_chain - gt) <= tol

        print(f"Problem #{p['id']}: {p['title']}")
        print(f"  Ground Truth: {gt}")
        print(f"  Direct:       {ans_direct} ({'PASS' if pass_direct else 'FAIL'})")
        print(f"  3-Step Chain: {ans_chain} ({'PASS' if pass_chain else 'FAIL'})\n")
        time.sleep(0.5)


if __name__ == "__main__":
    main()
