import os
import sys
import json
import time
from dotenv import load_dotenv
from openai import OpenAI

# Ensure UTF-8 output in Windows PowerShell terminal
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# =====================================================================
# SETUP: LOAD CREDENTIALS & INITIALIZE CLIENT
# =====================================================================
load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if not API_KEY:
    raise ValueError("Missing OPENAI_API_KEY in .env file.")

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# =====================================================================
# DATASET: 20 REALISTIC CUSTOMER EMAILS ACROSS 4 CATEGORIES
# Categories: "Billing", "Technical Support", "Feature Request", "Sales"
# =====================================================================
DATASET = [
    # --- Category 1: Billing (5 emails) ---
    {
        "id": 1,
        "true_category": "Billing",
        "email": "Hi, I was charged twice on invoice #48291 for my Pro subscription this month. Can you please refund the duplicate $49 charge?"
    },
    {
        "id": 2,
        "true_category": "Billing",
        "email": "Our company credit card on file expired yesterday. Where can I update our payment method before our subscription is suspended?"
    },
    {
        "id": 3,
        "true_category": "Billing",
        "email": "I would like to cancel our monthly plan and request a prorated refund for the remaining 20 days of our billing cycle."
    },
    {
        "id": 4,
        "true_category": "Billing",
        "email": "We need a formal VAT tax invoice with our corporate tax ID (EU-982341) for our accounting and auditing department."
    },
    {
        "id": 5,
        "true_category": "Billing",
        "email": "My annual subscription auto-renewed this morning without warning. I haven't used the account in 3 months; can I get a full refund?"
    },

    # --- Category 2: Technical Support (5 emails) ---
    {
        "id": 6,
        "true_category": "Technical Support",
        "email": "Whenever I click 'Export to CSV', the screen goes blank and I see a 500 Internal Server Error in my browser developer console."
    },
    {
        "id": 7,
        "true_category": "Technical Support",
        "email": "Our team cannot log in using Google Single Sign-On (SSO) today. It constantly redirects to an 'Invalid OAuth callback' page."
    },
    {
        "id": 8,
        "true_category": "Technical Support",
        "email": "The latest v2.4 desktop application crashes immediately on launch on macOS Sequoia. Crash logs are attached to this ticket."
    },
    {
        "id": 9,
        "true_category": "Technical Support",
        "email": "Your REST API endpoints are throwing 429 Too Many Requests even though our traffic is well under our 60 req/min rate limit."
    },
    {
        "id": 10,
        "true_category": "Technical Support",
        "email": "Database sync failed at 03:00 AM UTC with error: 'Connection timeout after 30000ms'. Our downstream webhooks did not fire."
    },

    # --- Category 3: Feature Request (5 emails) ---
    {
        "id": 11,
        "true_category": "Feature Request",
        "email": "Could you please add dark mode support? Coding in your web editor late at night is causing severe eye strain for our team."
    },
    {
        "id": 12,
        "true_category": "Feature Request",
        "email": "We love your product! It would be fantastic if you could build a native bi-directional sync integration with Notion and Linear."
    },
    {
        "id": 13,
        "true_category": "Feature Request",
        "email": "Can you provide a button to export analytics charts directly as vector SVG files instead of raster PNG images?"
    },
    {
        "id": 14,
        "true_category": "Feature Request",
        "email": "Would it be possible to allow custom keyboard shortcuts? We use Vim keybindings and would love to navigate with j/k."
    },
    {
        "id": 15,
        "true_category": "Feature Request",
        "email": "It would save us hours every week if we could set up automated recurring email PDF reports for our leadership team every Monday."
    },

    # --- Category 4: Sales (5 emails) ---
    {
        "id": 16,
        "true_category": "Sales",
        "email": "We are an enterprise organization with 450 engineers and want to explore bulk team licensing and custom enterprise SLA pricing."
    },
    {
        "id": 17,
        "true_category": "Sales",
        "email": "Could someone from your account executive team schedule a 30-minute product demo for our engineering leadership this Thursday?"
    },
    {
        "id": 18,
        "true_category": "Sales",
        "email": "Do you offer discounted pricing tiers for educational institutions, accredited universities, or registered non-profit organizations?"
    },
    {
        "id": 19,
        "true_category": "Sales",
        "email": "We are currently evaluating your platform against Datadog. Does your enterprise plan support private on-premise VPC deployments?"
    },
    {
        "id": 20,
        "true_category": "Sales",
        "email": "Our procurement team requires a signed Master Services Agreement (MSA) and a completed SOC2 security questionnaire before purchase."
    }
]

# =====================================================================
# PROMPT ENGINEERING: CORE TOPICS DEMONSTRATED
# =====================================================================

# TOPIC 1: ROLE SETTING (System Persona)
#   -> Tells the model its identity and operational domain.
#
# TOPIC 2: CLEAR INSTRUCTIONS & CONSTRAINTS
#   -> Bounded list of 4 allowed categories.
#   -> Negative constraint: "No conversational preamble or text outside JSON".
#
# TOPIC 4: GIVING EXAMPLES (Few-Shot In-Context Learning)
#   -> Demonstrates exact input format and ideal output structure for each class.
#
# TOPIC 5: SPECIFYING OUTPUT FORMAT (Strict JSON Schema)
#   -> Required keys: "category" and "reasoning".
SYSTEM_PROMPT = """You are an expert customer support triage classifier.
Your task is to classify incoming customer emails into EXACTLY ONE of these 4 categories:
1. Billing
2. Technical Support
3. Feature Request
4. Sales

RULES:
- Return ONLY a valid JSON object.
- The JSON object must contain exactly two keys:
  - "category": Must be one of ["Billing", "Technical Support", "Feature Request", "Sales"]
  - "reasoning": A brief 1-sentence explanation of why this category was chosen.
- Do NOT include markdown code blocks, backticks, or any conversational text outside the JSON.

FEW-SHOT EXAMPLES:
<email>
Can we upgrade our account to 50 seats? We need to discuss enterprise pricing.
</email>
{"category": "Sales", "reasoning": "The customer is asking to purchase additional seats and inquiring about enterprise pricing."}

<email>
I see an unauthorized charge of $120 on my credit card from your company.
</email>
{"category": "Billing", "reasoning": "The customer is reporting a disputed monetary charge on their card."}

<email>
The login page returns a 403 Forbidden error whenever our team tries to authenticate.
</email>
{"category": "Technical Support", "reasoning": "The user is reporting an operational authentication bug and HTTP error code."}

<email>
Please add support for exporting reports to Google Sheets directly.
</email>
{"category": "Feature Request", "reasoning": "The user is asking for a new feature that does not currently exist."}
"""

# =====================================================================
# CLASSIFICATION FUNCTION
# Demonstrates:
# - TOPIC 3: Delimiters (<email>...</email>) to isolate untrusted input
# - TOPIC 5: response_format={"type": "json_object"}
# - TOPIC 6: Handling common failures (JSON parsing errors, rate limits)
# =====================================================================
def classify_email(email_text: str, max_retries: int = 3) -> dict:
    """
    Classifies a customer email using engineered prompts and returns structured JSON.
    Includes automated backoff for rate limits and JSON validation.
    """
    # TOPIC 3: Delimiters isolate the user's raw email text from system instructions
    user_prompt = f"<email>\n{email_text}\n</email>"

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},  # TOPIC 1: Role Setting
                    {"role": "user", "content": user_prompt}        # TOPIC 3: Delimited User Input
                ],
                temperature=0.0,  # Deterministic, repeatable classification
                response_format={"type": "json_object"}  # TOPIC 5: Enforced JSON Output
            )

            raw_text = response.choices[0].message.content.strip()
            return json.loads(raw_text)

        except json.JSONDecodeError:
            # TOPIC 6: Handling Malformed JSON
            return {"category": "Unknown", "reasoning": "JSON parse error", "raw": raw_text}

        except Exception as e:
            # TOPIC 6: Handling Rate Limits (429) & Network Timeouts
            err = str(e)
            if "429" in err or "RateLimitError" in type(e).__name__:
                print("\n   [Notice] Rate limit hit. Waiting 32s for free-tier quota reset...")
                time.sleep(32)
            elif attempt < max_retries - 1:
                time.sleep(3)
            else:
                return {"category": "Error", "reasoning": f"API Failed: {err[:50]}"}


# =====================================================================
# BENCHMARK EXECUTION & ACCURACY MEASUREMENT
# =====================================================================
def main():
    print("=" * 85)
    print(" DAY 1 - SESSION 4: PROMPT ENGINEERING & CLASSIFICATION BENCHMARK")
    print("=" * 85)
    print(f"Model Under Test : {MODEL}")
    print(f"Total Emails     : {len(DATASET)}")
    print("Categories       : Billing | Technical Support | Feature Request | Sales")
    print("=" * 85)

    correct_count = 0
    category_stats = {
        "Billing": {"total": 0, "correct": 0},
        "Technical Support": {"total": 0, "correct": 0},
        "Feature Request": {"total": 0, "correct": 0},
        "Sales": {"total": 0, "correct": 0}
    }

    print(f"\n{'ID':<4} {'True Label':<19} {'Predicted Label':<19} {'Match':<7} {'Reasoning'}")
    print("-" * 85)

    for item in DATASET:
        email_id = item["id"]
        true_cat = item["true_category"]
        email_text = item["email"]

        category_stats[true_cat]["total"] += 1

        # Run classification
        result = classify_email(email_text)
        pred_cat = result.get("category", "Unknown")
        reasoning = result.get("reasoning", "")

        # Check accuracy
        is_match = (pred_cat.strip().lower() == true_cat.strip().lower())
        if is_match:
            correct_count += 1
            category_stats[true_cat]["correct"] += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"

        # Display result row (truncated reasoning for neat tabular alignment)
        print(f"{email_id:<4} {true_cat:<19} {pred_cat:<19} {status:<7} {reasoning[:35]}...")

        # Pace requests to remain under the 15 requests/minute free-tier ceiling
        if email_id < len(DATASET):
            time.sleep(3.5)

    # Calculate overall accuracy
    overall_accuracy = (correct_count / len(DATASET)) * 100

    print("-" * 85)
    print("\n" + "=" * 85)
    print(" ACCURACY & BENCHMARK REPORT")
    print("=" * 85)
    print(f"Overall Accuracy: {correct_count}/{len(DATASET)} ({overall_accuracy:.1f}%)\n")

    print(f"{'Category':<24} {'Correct':<10} {'Total':<10} {'Accuracy':<10}")
    print("-" * 55)
    for cat, stats in category_stats.items():
        cat_acc = (stats["correct"] / stats["total"]) * 100 if stats["total"] else 0
        print(f"{cat:<24} {stats['correct']:<10} {stats['total']:<10} {cat_acc:.1f}%")

    print("=" * 85)
    print("Session 4 task completed successfully!")
    print("=" * 85)


if __name__ == "__main__":
    main()
