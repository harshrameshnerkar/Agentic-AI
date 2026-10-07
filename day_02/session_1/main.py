import os
import sys
import json
import time
from dotenv import load_dotenv
from openai import OpenAI

# Ensure UTF-8 output on Windows terminal
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# =====================================================================
# SETUP: LOAD CREDENTIALS & INITIALIZE CLIENT
# =====================================================================
load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL")
MODEL = os.getenv("OPENAI_MODEL", "gemini-3.5-flash-lite")

if not API_KEY:
    raise ValueError("Missing OPENAI_API_KEY in .env file.")

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# =====================================================================
# BENCHMARK DATASET: 6 MULTI-STEP REASONING PROBLEMS
# Each problem involves arithmetic, order of operations, and constraints.
# =====================================================================
DATASET = [
    {
        "id": 1,
        "title": "Cloud Server Auto-Scaling Bill",
        "problem": (
            "A company runs 3 base servers 24 hours a day for 30 days at $0.50/hour each. "
            "During peak hours (4 hours every day for all 30 days), they spin up 5 additional servers "
            "at $0.80/hour each. They get a 10% volume discount on the total server usage bill before "
            "a fixed $50 maintenance fee is added. What is the final monthly bill in dollars?"
        ),
        "ground_truth": 1454.0,
        "tolerance": 0.01
    },
    {
        "id": 2,
        "title": "Warehouse Packaging & Pallet Logistics",
        "problem": (
            "A warehouse needs to ship 1,750 widgets. Each small box holds 12 widgets. "
            "Any leftover widgets that don't fill a full box are packed in a special padded envelope. "
            "Each pallet can hold up to 25 small boxes. Padded envelopes cannot be placed on pallets "
            "and are shipped as individual loose items. "
            "How many shipping containers total (pallets + loose small boxes not on pallets + padded envelopes) "
            "must be loaded onto the shipping truck?"
        ),
        "ground_truth": 26.0,
        "tolerance": 0.01
    },
    {
        "id": 3,
        "title": "Multi-Leg Flight Journey Duration",
        "problem": (
            "A traveler takes a multi-leg journey: Flight 1 takes 6 hours, followed by a 3-hour layover, "
            "and Flight 2 takes 7 hours. However, Flight 1 was delayed by 45 minutes on departure, "
            "reducing the layover time to 2 hours and 15 minutes because the connection was maintained. "
            "Flight 2 experienced a 30-minute headwind delay in the air. "
            "How many total elapsed hours (including delays and layovers) did the entire journey take "
            "from the scheduled departure time of Flight 1 to the actual wheels-down arrival of Flight 2? "
            "Provide the answer in total hours as a decimal."
        ),
        "ground_truth": 16.5,
        "tolerance": 0.01
    },
    {
        "id": 4,
        "title": "Factory Machine Defect Rate",
        "problem": (
            "Machine A produces 150 microchips per hour with a 6% defect rate and runs for an 8-hour shift. "
            "Machine B produces 200 microchips per hour with a 5% defect rate, but breaks down after running for only 5 hours. "
            "All defective chips are discarded. How many total non-defective (good) chips were produced across both machines?"
        ),
        "ground_truth": 2078.0,
        "tolerance": 0.01
    },
    {
        "id": 5,
        "title": "Subscription Downgrade Prorated Credit",
        "problem": (
            "A customer pays $90 upfront for a 30-day Premium plan. After exactly 10 days, they downgrade to a Basic plan "
            "($30 per 30-day cycle) for the remaining 20 days. The billing system calculates unused credit on Premium for the 20 days "
            "($90 * 20/30), subtracts the cost of the Basic plan for those 20 days ($30 * 20/30), and deducts a $5 downgrade "
            "administrative fee. What is the net dollar credit refunded to the customer?"
        ),
        "ground_truth": 35.0,
        "tolerance": 0.01
    },
    {
        "id": 6,
        "title": "Engineering Sprint Story Point Capacity",
        "problem": (
            "A software team has 6 engineers working 8 hours a day for a 10-day sprint. "
            "25% of all total engineering hours are reserved for meetings, reviews, and support. "
            "The remaining hours are dedicated to user story points. "
            "If each story point requires exactly 3.6 dedicated engineering hours, "
            "how many story points can the team complete in the sprint?"
        ),
        "ground_truth": 100.0,
        "tolerance": 0.01
    }
]


# =====================================================================
# HELPER: RATE-LIMIT RESILIENT API CALL
# =====================================================================
def call_llm(messages: list, temperature: float = 0.0, response_format: dict = None, max_retries: int = 3) -> str:
    """Wrapper around client.chat.completions.create with automatic rate limit backoff."""
    for attempt in range(max_retries):
        try:
            kwargs = {
                "model": MODEL,
                "messages": messages,
                "temperature": temperature
            }
            if response_format:
                kwargs["response_format"] = response_format

            resp = client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content.strip()

        except Exception as e:
            err = str(e)
            if "429" in err or "RateLimitError" in type(e).__name__:
                print("\n   [Rate Limit Notice] Cooling down for 32s to refresh free-tier quota...")
                time.sleep(32)
            elif attempt < max_retries - 1:
                time.sleep(3)
            else:
                raise e


# =====================================================================
# METHOD A: DIRECT SINGLE PROMPT (ZERO-SHOT DIRECT)
# Asking the model to produce the final answer immediately without CoT.
# =====================================================================
def solve_single_prompt(problem_text: str) -> dict:
    """
    Direct prompting: Forces the model to output only the final number immediately.
    Common failure mode: Models make calculation slips because no intermediate
    reasoning tokens are generated before predicting the final number.
    """
    prompt = f"""Solve this problem. Provide ONLY a valid JSON object with the final numerical answer.
Do NOT show any work, explanation, or intermediate text.

Problem:
{problem_text}

Output format:
{{"final_answer": <number>}}
"""
    raw = call_llm(
        messages=[
            {"role": "system", "content": "You are a concise computational assistant. Output only JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0,
        response_format={"type": "json_object"}
    )

    try:
        data = json.loads(raw)
        return {"answer": float(data.get("final_answer", 0)), "raw": raw}
    except Exception:
        # Fallback extraction if JSON parsing fails
        import re
        numbers = re.findall(r"[-+]?\d*\.\d+|\d+", raw)
        ans = float(numbers[-1]) if numbers else 0.0
        return {"answer": ans, "raw": raw}


# =====================================================================
# METHOD B: 3-STEP PROMPT CHAIN (TASK DECOMPOSITION)
# Splitting the problem into 3 discrete, specialized stages:
#   Stage 1: Variable & Constraint Extractor
#   Stage 2: Step-by-Step Reasoner & Intermediate Calculator
#   Stage 3: Verifier & Final Output Formatter
# =====================================================================
def solve_three_step_chain(problem_text: str) -> dict:
    """
    Prompt Chaining / Decomposition:
    - Step 1: Extracts parameters, units, constraints into structured JSON.
    - Step 2: Carries out calculation steps methodically using extracted data.
    - Step 3: Verifies constraints, edge cases, and emits final verified number.
    """
    # -------------------------------------------------------------
    # STAGE 1: VARIABLE & CONSTRAINT EXTRACTION
    # -------------------------------------------------------------
    stage1_prompt = f"""Read the problem and extract all numerical quantities, rates, durations, fees, and constraints.
Do NOT solve the problem yet. Just extract the key facts into structured JSON.

Problem:
{problem_text}

Return JSON with:
{{
  "entities_and_values": {{ ... }},
  "rules_and_constraints": [ ... ]
}}
"""
    stage1_output = call_llm(
        messages=[
            {"role": "system", "content": "You are a data extraction specialist. Extract facts cleanly into JSON."},
            {"role": "user", "content": stage1_prompt}
        ],
        temperature=0.0,
        response_format={"type": "json_object"}
    )

    # Brief pacing delay between stages
    time.sleep(1.0)

    # -------------------------------------------------------------
    # STAGE 2: STEP-BY-STEP REASONING & ARITHMETIC CALCULATION
    # -------------------------------------------------------------
    stage2_prompt = f"""Using the extracted facts below, calculate the intermediate values step by step.
Show each intermediate calculation and formula clearly.

Original Problem:
{problem_text}

Extracted Facts:
{stage1_output}

Return JSON with:
{{
  "step_by_step_calculations": [ ... ],
  "tentative_result": <number>
}}
"""
    stage2_output = call_llm(
        messages=[
            {"role": "system", "content": "You are a mathematical reasoning engine. Execute computations step by step."},
            {"role": "user", "content": stage2_prompt}
        ],
        temperature=0.0,
        response_format={"type": "json_object"}
    )

    time.sleep(1.0)

    # -------------------------------------------------------------
    # STAGE 3: CONSTRAINT VERIFICATION & FINAL FORMATTING
    # -------------------------------------------------------------
    stage3_prompt = f"""Review the original problem, the extracted facts, and the calculations.
Check for any overlooked constraints, order-of-operation issues, or rounding errors.
Produce the final verified numerical answer.

Original Problem:
{problem_text}

Calculations:
{stage2_output}

Return JSON format:
{{
  "verification_notes": "<brief check>",
  "final_answer": <number>
}}
"""
    stage3_output = call_llm(
        messages=[
            {"role": "system", "content": "You are a strict QA auditor and verifier. Output verified JSON."},
            {"role": "user", "content": stage3_prompt}
        ],
        temperature=0.0,
        response_format={"type": "json_object"}
    )

    try:
        data = json.loads(stage3_output)
        return {
            "answer": float(data.get("final_answer", 0)),
            "stage1": stage1_output,
            "stage2": stage2_output,
            "stage3": stage3_output
        }
    except Exception:
        import re
        numbers = re.findall(r"[-+]?\d*\.\d+|\d+", stage3_output)
        ans = float(numbers[-1]) if numbers else 0.0
        return {"answer": ans, "stage3": stage3_output}


# =====================================================================
# BENCHMARK EXECUTION & ACCURACY COMPARISON
# =====================================================================
def main():
    print("=" * 95)
    print(" DAY 2 - SESSION 1: CHAIN-OF-THOUGHT & TASK DECOMPOSITION BENCHMARK")
    print("=" * 95)
    print(f"Model Under Test : {MODEL}")
    print(f"Total Problems   : {len(DATASET)}")
    print("Comparing        : Single Direct Prompt vs. 3-Step Decomposed Chain")
    print("=" * 95)

    single_correct = 0
    chain_correct = 0

    results = []

    for item in DATASET:
        p_id = item["id"]
        title = item["title"]
        problem = item["problem"]
        expected = item["ground_truth"]
        tol = item["tolerance"]

        print(f"\n[Problem {p_id}/6]: {title}")
        print("-" * 95)

        # 1. Run Single Direct Prompt
        print("   Running Method A (Single Direct Prompt)...", end="", flush=True)
        res_single = solve_single_prompt(problem)
        ans_single = res_single["answer"]
        match_single = abs(ans_single - expected) <= tol
        if match_single:
            single_correct += 1
            print(f" Answer: {ans_single} ✅ PASS")
        else:
            print(f" Answer: {ans_single} (Expected: {expected}) ❌ FAIL")

        # Pace calls to stay under free tier limit
        time.sleep(3.5)

        # 2. Run 3-Step Decomposed Chain
        print("   Running Method B (3-Step Chain Pipeline)...", end="", flush=True)
        res_chain = solve_three_step_chain(problem)
        ans_chain = res_chain["answer"]
        match_chain = abs(ans_chain - expected) <= tol
        if match_chain:
            chain_correct += 1
            print(f" Answer: {ans_chain} ✅ PASS")
        else:
            print(f" Answer: {ans_chain} (Expected: {expected}) ❌ FAIL")

        results.append({
            "id": p_id,
            "title": title,
            "expected": expected,
            "single_ans": ans_single,
            "single_match": match_single,
            "chain_ans": ans_chain,
            "chain_match": match_chain
        })

        # Inter-problem pacing
        time.sleep(3.5)

    # -------------------------------------------------------------
    # FINAL COMPARATIVE EVALUATION TABLE
    # -------------------------------------------------------------
    print("\n" + "=" * 95)
    print(" COMPARATIVE BENCHMARK REPORT: SINGLE PROMPT VS 3-STEP CHAIN")
    print("=" * 95)
    print(f"{'ID':<4} {'Problem Title':<38} {'Expected':<10} {'Single':<12} {'3-Step Chain':<12} {'Advantage'}")
    print("-" * 95)

    for r in results:
        single_str = f"{r['single_ans']} {'✅' if r['single_match'] else '❌'}"
        chain_str = f"{r['chain_ans']} {'✅' if r['chain_match'] else '❌'}"
        advantage = "Chain Won" if (r['chain_match'] and not r['single_match']) else ("Tie" if r['chain_match'] == r['single_match'] else "Single Won")
        print(f"{r['id']:<4} {r['title'][:36]:<38} {r['expected']:<10} {single_str:<12} {chain_str:<12} {advantage}")

    acc_single = (single_correct / len(DATASET)) * 100
    acc_chain = (chain_correct / len(DATASET)) * 100

    print("-" * 95)
    print(f"Method A (Single Direct Prompt) Accuracy : {single_correct}/{len(DATASET)} ({acc_single:.1f}%)")
    print(f"Method B (3-Step Decomposed Chain) Accuracy : {chain_correct}/{len(DATASET)} ({acc_chain:.1f}%)")
    print("=" * 95)
    print(f"Accuracy Delta: +{acc_chain - acc_single:.1f}% improvement via Task Decomposition & Chain-of-Thought!")
    print("=" * 95)


if __name__ == "__main__":
    main()
