"""
Day 02 - Session 01: Chain-of-Thought & Prompt Chaining
========================================================
Demonstrates the power of prompt decomposition when solving multi-step reasoning
and mathematical problems:
  - Method A (Direct): Single-shot prompting asking for the final answer directly.
  - Method B (3-Step Chain): Decomposes the task into:
      1. Variable & Constraint Extraction
      2. Step-by-Step Intermediate Calculation
      3. Verification & Final Formatting
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv
from openai import OpenAI

from dataset import REASONING_DATASET

# Ensure UTF-8 output on Windows terminal
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# Setup Credentials & Client
# ---------------------------------------------------------------------------
local_env = Path(__file__).resolve().parent / ".env"
root_env = Path(__file__).resolve().parents[2] / ".env"

if local_env.exists():
    load_dotenv(local_env)
elif root_env.exists():
    load_dotenv(root_env)
else:
    load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL")
MODEL = os.getenv("OPENAI_MODEL", "gemini-3.1-flash-lite")

if not API_KEY:
    print("Error: Missing OPENAI_API_KEY in .env")
    sys.exit(1)

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)


def call_llm(messages: List[Dict[str, str]], temperature: float = 0.0, response_format: Any = None) -> str:
    """
    Standardized wrapper for chat completion with error handling.
    """
    try:
        kwargs: Dict[str, Any] = {
            "model": MODEL,
            "messages": messages,
            "temperature": temperature,
        }
        if response_format:
            kwargs["response_format"] = response_format

        response = client.chat.completions.create(**kwargs)
        return (response.choices[0].message.content or "").strip()
    except Exception as e:
        print(f"API Error: {e}")
        return "{}"


def solve_direct(problem_text: str) -> Dict[str, Any]:
    """
    Method A: Direct Prompting.
    Asks the model for the final numerical answer without encouraging intermediate work.
    """
    prompt = f"""Solve this problem. Provide ONLY a valid JSON object with the final numerical answer.
Do NOT show any work, explanation, or conversational text.

Problem:
{problem_text}

Output format:
{{"final_answer": <number>}}
"""
    raw_response = call_llm(
        messages=[
            {"role": "system", "content": "You are a concise computational assistant. Output only JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0,
        response_format={"type": "json_object"}
    )

    try:
        data = json.loads(raw_response)
        return {"answer": float(data.get("final_answer", 0.0)), "raw": raw_response}
    except Exception:
        import re
        nums = re.findall(r"[-+]?\d*\.\d+|\d+", raw_response)
        return {"answer": float(nums[-1]) if nums else 0.0, "raw": raw_response}


def solve_three_step_chain(problem_text: str) -> Dict[str, Any]:
    """
    Method B: 3-Step Chain Decomposition.
    Stage 1: Extract constants and constraints into structured JSON.
    Stage 2: Carry out step-by-step arithmetic.
    Stage 3: Verify constraints and output formatted answer.
    """
    # Stage 1: Extraction
    stage1_prompt = f"""Read the problem carefully. Extract all numerical parameters, rates, constraints, and units.
Do not solve yet. Output structured JSON.

Problem:
{problem_text}

JSON format:
{{
  "parameters": {{ ... }},
  "constraints": [ ... ]
}}"""

    stage1_json = call_llm(
        messages=[
            {"role": "system", "content": "You are a parameter extraction engine. Output valid JSON."},
            {"role": "user", "content": stage1_prompt}
        ],
        temperature=0.0,
        response_format={"type": "json_object"}
    )

    # Stage 2: Step-by-Step Reasoning
    stage2_prompt = f"""Using these extracted parameters, perform the step-by-step arithmetic to solve the problem.

Original Problem:
{problem_text}

Extracted Parameters:
{stage1_json}

JSON format:
{{
  "steps": [ ... ],
  "intermediate_result": <number>
}}"""

    stage2_json = call_llm(
        messages=[
            {"role": "system", "content": "You are a mathematical calculation engine. Output valid JSON."},
            {"role": "user", "content": stage2_prompt}
        ],
        temperature=0.0,
        response_format={"type": "json_object"}
    )

    # Stage 3: Verification and Final Formatting
    stage3_prompt = f"""Review the calculation steps against the original constraints to ensure no fees, units, or edge conditions were missed.
Emit the final verified numerical answer.

Calculation Summary:
{stage2_json}

JSON format:
{{"final_answer": <number>}}"""

    stage3_json = call_llm(
        messages=[
            {"role": "system", "content": "You are a verification engine. Output valid JSON."},
            {"role": "user", "content": stage3_prompt}
        ],
        temperature=0.0,
        response_format={"type": "json_object"}
    )

    try:
        data = json.loads(stage3_json)
        return {"answer": float(data.get("final_answer", 0.0)), "chain": stage3_json}
    except Exception:
        import re
        nums = re.findall(r"[-+]?\d*\.\d+|\d+", stage3_json)
        return {"answer": float(nums[-1]) if nums else 0.0, "chain": stage3_json}


def run_benchmark(problems: List[Dict[str, Any]]) -> None:
    print("=" * 85)
    print(" DAY 02 - SESSION 01: DIRECT PROMPTING vs 3-STEP CHAIN DECOMPOSITION")
    print("=" * 85)
    print(f"Active Model       : {MODEL}")
    print(f"Problem Count      : {len(problems)}")
    print("=" * 85)
    print()

    direct_correct = 0
    chain_correct = 0

    print(f"{'#':<3} {'Problem Title':<32} {'Ground Truth':<14} {'Direct Ans':<14} {'Chain Ans':<14}")
    print("-" * 85)

    for p in problems:
        p_id = p["id"]
        title = p["title"]
        gt = p["ground_truth"]
        tol = p["tolerance"]

        # Run Method A
        res_a = solve_direct(p["problem"])
        ans_a = res_a["answer"]
        match_a = abs(ans_a - gt) <= tol
        if match_a:
            direct_correct += 1

        # Run Method B
        res_b = solve_three_step_chain(p["problem"])
        ans_b = res_b["answer"]
        match_b = abs(ans_b - gt) <= tol
        if match_b:
            chain_correct += 1

        mark_a = "PASS" if match_a else "FAIL"
        mark_b = "PASS" if match_b else "FAIL"

        print(f"{p_id:<3} {title[:30]:<32} {gt:<14.2f} {ans_a:<8.2f}({mark_a})  {ans_b:<8.2f}({mark_b})")
        time.sleep(0.5)

    print("-" * 85)
    print("COMPARATIVE RESULTS:")
    print(f"  Method A (Direct Single-Shot) : {direct_correct}/{len(problems)} ({direct_correct / len(problems) * 100:.1f}%)")
    print(f"  Method B (3-Step Chain)       : {chain_correct}/{len(problems)} ({chain_correct / len(problems) * 100:.1f}%)")
    print("=" * 85)
    print("Reasoning benchmark completed successfully.\n")


def main() -> None:
    if "--full" in sys.argv or "--all" in sys.argv:
        subset = REASONING_DATASET
    else:
        # First 2 problems by default for snappy demonstration
        subset = REASONING_DATASET[:2]
        print("[Note] Running 2-problem demo. Pass '--full' to evaluate all 6 problems.\n")

    run_benchmark(subset)


if __name__ == "__main__":
    main()
