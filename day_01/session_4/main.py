"""
Day 01 - Session 04: Prompt Engineering & Classification Benchmark
===================================================================
Demonstrates production prompt engineering techniques:
  1. Role Prompting: Clear persona definition.
  2. Input Delimiters: Enclosing untrusted user input within XML-style tags (<email>...</email>).
  3. Few-Shot Examples: Grounding expected outputs with concrete input-output pairs.
  4. Structured Output Format: Enforcing valid JSON schema responses.
  5. Benchmark Evaluation: Automated scoring against ground-truth labels.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv
from openai import OpenAI

# Import evaluation dataset
from dataset import DATASET

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

# ---------------------------------------------------------------------------
# System Prompt with Role, Rules, Output Schema, and Few-Shot Examples
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are an automated customer support triage classifier.
Your task is to classify incoming customer emails into EXACTLY ONE of these categories:
- Billing
- Technical Support
- Feature Request
- Sales

OUTPUT FORMAT RULES:
Return ONLY a valid JSON object with exactly two keys:
{
  "category": "<One of the 4 exact category names>",
  "reasoning": "<1-sentence concise explanation>"
}

FEW-SHOT EXAMPLES:
<email>
Can we upgrade our account to 50 seats? We need to discuss enterprise pricing and invoicing.
</email>
{"category": "Sales", "reasoning": "Inquiry regarding purchasing additional seats and enterprise pricing."}

<email>
I noticed a duplicate charge of $49 on our credit card for this month's renewal.
</email>
{"category": "Billing", "reasoning": "Reporting an unauthorized duplicate payment charge."}

<email>
The web console fails to load and returns a 502 Bad Gateway error on the dashboard.
</email>
{"category": "Technical Support", "reasoning": "Reporting an operational service error and HTTP 502 failure."}

<email>
Please consider adding native support for dark mode and keyboard shortcuts.
</email>
{"category": "Feature Request", "reasoning": "Requesting user interface enhancements that do not currently exist."}
"""


def classify_email(email_text: str, max_retries: int = 2) -> Dict[str, Any]:
    """
    Classifies customer email text into structured JSON.
    Uses XML delimiter tags to isolate input text from system instructions.
    """
    user_prompt = f"<email>\n{email_text.strip()}\n</email>"

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )

            raw_content = response.choices[0].message.content or "{}"
            parsed_data = json.loads(raw_content)
            return {
                "category": parsed_data.get("category", "Unknown"),
                "reasoning": parsed_data.get("reasoning", "")
            }

        except json.JSONDecodeError:
            if attempt == max_retries - 1:
                return {"category": "Unknown", "reasoning": "JSON decode failed"}
        except Exception as e:
            if "429" in str(e):
                time.sleep(5.0)  # Gentle backoff on rate limit
            elif attempt == max_retries - 1:
                return {"category": "Error", "reasoning": f"API Error: {str(e)[:50]}"}
            time.sleep(1.0)

    return {"category": "Error", "reasoning": "Exceeded retry budget"}


def run_benchmark(eval_items: List[Dict[str, Any]]) -> None:
    """
    Executes the classification benchmark across the provided dataset items.
    """
    print("=" * 80)
    print(" DAY 01 - SESSION 04: PROMPT ENGINEERING & CLASSIFICATION BENCHMARK")
    print("=" * 80)
    print(f"Target Model       : {MODEL}")
    print(f"Evaluated Emails   : {len(eval_items)}")
    print(f"Target Categories  : Billing | Technical Support | Feature Request | Sales")
    print("=" * 80)
    print()

    print(f"{'ID':<4} {'True Category':<19} {'Predicted Category':<21} {'Status':<8} {'Reasoning'}")
    print("-" * 80)

    correct_count = 0
    category_metrics: Dict[str, Dict[str, int]] = {
        cat: {"correct": 0, "total": 0}
        for cat in ["Billing", "Technical Support", "Feature Request", "Sales"]
    }

    for item in eval_items:
        email_id = item["id"]
        true_cat = item["true_category"]
        email_text = item["email"]

        category_metrics[true_cat]["total"] += 1

        result = classify_email(email_text)
        predicted_cat = result["category"]
        reasoning = result["reasoning"]

        is_match = (predicted_cat.strip().lower() == true_cat.strip().lower())
        if is_match:
            correct_count += 1
            category_metrics[true_cat]["correct"] += 1
            status = "PASS"
        else:
            status = "FAIL"

        print(f"{email_id:<4} {true_cat:<19} {predicted_cat:<21} {status:<8} {reasoning[:28]}...")
        time.sleep(0.5)  # Slight pacing between API queries

    # Summary Report
    accuracy_pct = (correct_count / len(eval_items)) * 100.0 if eval_items else 0.0

    print("-" * 80)
    print("BENCHMARK SUMMARY:")
    print(f"  Overall Accuracy : {correct_count}/{len(eval_items)} ({accuracy_pct:.1f}%)\n")
    print(f"  {'Category':<22} {'Correct':<8} {'Total':<8} {'Accuracy'}")
    print("  " + "-" * 45)

    for cat, stats in category_metrics.items():
        if stats["total"] > 0:
            cat_acc = (stats["correct"] / stats["total"]) * 100.0
            print(f"  {cat:<22} {stats['correct']:<8} {stats['total']:<8} {cat_acc:.1f}%")

    print("=" * 80)
    print("Classification benchmark completed successfully.\n")


def main() -> None:
    # Run a quick 4-sample benchmark by default, or the full 20 with --full
    if "--full" in sys.argv or "--all" in sys.argv:
        eval_set = DATASET
    else:
        # 1 representative sample from each of the 4 categories
        eval_set = [DATASET[0], DATASET[5], DATASET[10], DATASET[15]]
        print("[Note] Running 4-email representative sample. Pass '--full' to evaluate all 20 emails.")

    run_benchmark(eval_set)


if __name__ == "__main__":
    main()
