"""
Day 01 - Session 04: Prompt Engineering & Classification Benchmark
Demonstrates prompt engineering techniques:
  1. System Role & Delimiters (<email>...</email>)
  2. Few-Shot Examples
  3. Structured JSON output format
  4. Accuracy evaluation against test samples
"""

import os
import sys
import json
import time
from dotenv import load_dotenv
from openai import OpenAI
from dataset import DATASET

# 1. Setup credentials
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
model = os.getenv("OPENAI_MODEL", "gemini-3.1-flash-lite")

if not api_key:
    raise ValueError("Missing API key in .env")

client = OpenAI(api_key=api_key, base_url=base_url)

# 2. System Prompt with Role, Rules, Output Schema, and Few-Shot Examples
SYSTEM_PROMPT = """You are a customer support triage classifier.
Classify incoming customer emails into EXACTLY ONE category:
- Billing
- Technical Support
- Feature Request
- Sales

Respond ONLY with a JSON object:
{
  "category": "<Exact Category Name>",
  "reasoning": "<One concise sentence explaining why>"
}

Examples:
<email>Can we upgrade to 50 seats? Need custom pricing.</email>
{"category": "Sales", "reasoning": "Inquiring about purchasing seats and pricing."}

<email>I was charged twice on my credit card this month.</email>
{"category": "Billing", "reasoning": "Customer reporting duplicate payment charge."}

<email>Dashboard gives a 500 error when clicking settings.</email>
{"category": "Technical Support", "reasoning": "Reporting an application crash and HTTP 500 error."}

<email>Please add an option to export tables as CSV.</email>
{"category": "Feature Request", "reasoning": "Requesting a new feature not currently available."}
"""


def classify_email(email_text: str) -> dict:
    """Classifies an email and returns structured JSON."""
    user_prompt = f"<email>\n{email_text.strip()}\n</email>"

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content or "{}")
    except Exception as e:
        return {"category": "Error", "reasoning": str(e)}


def main():
    # Use 4 representative emails by default (one per category) for quick evaluation, or --full for all 20
    if "--full" in sys.argv:
        eval_set = DATASET
    else:
        eval_set = [DATASET[0], DATASET[5], DATASET[10], DATASET[15]]
        print("Evaluating 4 sample emails (run with '--full' to evaluate all 20 emails)...\n")

    correct = 0

    for item in eval_set:
        true_cat = item["true_category"]
        result = classify_email(item["email"])
        pred_cat = result.get("category", "Unknown")
        reasoning = result.get("reasoning", "")

        is_match = pred_cat.strip().lower() == true_cat.strip().lower()
        if is_match:
            correct += 1
            status = "PASS"
        else:
            status = "FAIL"

        print(f"[{status}] Email #{item['id']}")
        print(f"  True:      {true_cat}")
        print(f"  Predicted: {pred_cat}")
        print(f"  Reason:    {reasoning}\n")
        time.sleep(0.5)

    accuracy = (correct / len(eval_set)) * 100
    print(f"Accuracy: {correct}/{len(eval_set)} ({accuracy:.0f}%)")


if __name__ == "__main__":
    main()
