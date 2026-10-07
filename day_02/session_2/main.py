import os
import sys
import json
import time
import re
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field, field_validator, ValidationError

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
# TOPIC 1 & 2: PYDANTIC DATA MODEL & VALIDATION RULES
# =====================================================================
class Invoice(BaseModel):
    """
    Validated Pydantic Model for Invoice Extraction.
    Enforces strict types, positive amounts, and standardized YYYY-MM-DD dates.
    """
    name: str = Field(
        description="Full name of the customer, client, or recipient individual"
    )
    company: str = Field(
        description="Name of the company or vendor issuing or receiving the invoice"
    )
    amount: float = Field(
        gt=0,
        description="Total invoice dollar amount as a positive float (without currency symbols)"
    )
    date: str = Field(
        description="Invoice date normalized to standard YYYY-MM-DD format"
    )

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Ensures the date is normalized to strict YYYY-MM-DD."""
        v = v.strip()
        # Regex check for YYYY-MM-DD
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError(f"Date '{v}' must be strictly formatted as YYYY-MM-DD.")
        # Verify it is a valid calendar date
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Date '{v}' is not a valid calendar date.")
        return v

    @field_validator("name", "company")
    @classmethod
    def check_non_empty(cls, v: str) -> str:
        """Ensures fields are clean non-empty strings."""
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Field cannot be empty.")
        return cleaned


# =====================================================================
# DATASET: 15 MESSY, REAL-WORLD INVOICE TEXTS
# Contains messy formatting, conversational chatter, OCR errors, and varied dates.
# =====================================================================
MESSY_INVOICES = [
    {
        "id": 1,
        "raw_text": (
            "Hey accounting, please process payment for Johnathan Doe over at Apex Global Logistics. "
            "The invoice total comes out to $1,450.00 for the consulting work delivered on January 14, 2024. Thanks!"
        ),
        "expected": {"name": "Johnathan Doe", "company": "Apex Global Logistics", "amount": 1450.0, "date": "2024-01-14"}
    },
    {
        "id": 2,
        "raw_text": (
            "*** INVOICE RECEIPT ***\n"
            "VENDOR: CloudScale Technologies Inc.\n"
            "BILLED TO: Samantha Reed\n"
            "SUBTOTAL: $820.00 | TAX: $79.50 | GRAND TOTAL: $899.50\n"
            "ISSUE DATE: 2023/11/05\n"
            "STATUS: PAID"
        ),
        "expected": {"name": "Samantha Reed", "company": "CloudScale Technologies Inc.", "amount": 899.50, "date": "2023-11-05"}
    },
    {
        "id": 3,
        "raw_text": (
            "Fwd: Expense Approval: Dr. Robert Banner purchased lab hardware from Stark Industries "
            "costing exactly 5420.75 USD on the 22nd of February, 2024. Approved by manager."
        ),
        "expected": {"name": "Robert Banner", "company": "Stark Industries", "amount": 5420.75, "date": "2024-02-22"}
    },
    {
        "id": 4,
        "raw_text": (
            "MEMO TO FINANCE: Reimburse Emily Watson for the marketing software subscription with "
            "HubSpot Marketing Hub. Total charged was $320.00 on 12-08-2023."
        ),
        "expected": {"name": "Emily Watson", "company": "HubSpot", "amount": 320.0, "date": "2023-12-08"}
    },
    {
        "id": 5,
        "raw_text": (
            "ORDER #998124\n"
            "Customer: Michael Chang\n"
            "Seller: Datadog Enterprise Systems\n"
            "Lines: APM License ($2400), Logs ($500)\n"
            "Total Due: $2,900.00\n"
            "Dated: March 3, 2024"
        ),
        "expected": {"name": "Michael Chang", "company": "Datadog Enterprise Systems", "amount": 2900.0, "date": "2024-03-03"}
    },
    {
        "id": 6,
        "raw_text": (
            "Slack Msg from Sarah: Hey team, we just paid CyberGuard Security Solutions $7,500.00 "
            "for our annual pentest. Invoice issued to Sarah Jenkins on 2023-10-18."
        ),
        "expected": {"name": "Sarah Jenkins", "company": "CyberGuard Security Solutions", "amount": 7500.0, "date": "2023-10-18"}
    },
    {
        "id": 7,
        "raw_text": (
            "Tax Invoice [COPY]\n"
            "Billed entity: David Miller\n"
            "Provider: Atlassian Corporation\n"
            "Jira Software Enterprise Plan\n"
            "Amount: $450.25 (USD)\n"
            "Transaction timestamp: April 19, 2024 14:32:00"
        ),
        "expected": {"name": "David Miller", "company": "Atlassian Corporation", "amount": 450.25, "date": "2024-04-19"}
    },
    {
        "id": 8,
        "raw_text": (
            "Hi all, attached is the catering invoice for Priya Patel from Green Leaf Catering Co. "
            "Total charge is $680.00 dated 2024-05-02. Please remit payment via ACH."
        ),
        "expected": {"name": "Priya Patel", "company": "Green Leaf Catering Co.", "amount": 680.0, "date": "2024-05-02"}
    },
    {
        "id": 9,
        "raw_text": (
            "RECEIPT - VENDOR: Snowflake Data Cloud // CLIENT: Carlos Gomez // "
            "AMOUNT CHARGED: 3120.40 $ // DATE: 11/28/2023 // THANK YOU FOR YOUR BUSINESS"
        ),
        "expected": {"name": "Carlos Gomez", "company": "Snowflake Data Cloud", "amount": 3120.40, "date": "2023-11-28"}
    },
    {
        "id": 10,
        "raw_text": (
            "Expense report submission by Rachel Green for office desk ergonomics. "
            "Company: Herman Miller Workspace. Net sum: $1,280.00. Dated September 15, 2023."
        ),
        "expected": {"name": "Rachel Green", "company": "Herman Miller Workspace", "amount": 1280.0, "date": "2023-09-15"}
    },
    {
        "id": 11,
        "raw_text": (
            "INVOICE #INV-2024-001\n"
            "Attention: Alexander Wright\n"
            "Issuer: Twilio Communications Platform\n"
            "SMS & Voice API Usage: $195.60\n"
            "Billing Period Ending: 2024-01-31"
        ),
        "expected": {"name": "Alexander Wright", "company": "Twilio Communications Platform", "amount": 195.60, "date": "2024-01-31"}
    },
    {
        "id": 12,
        "raw_text": (
            "Forwarded bill: Please reimburse Elena Rostova $3,850.00 for legal advisory services "
            "rendered by Baker & McKenzie LLP on 10 July 2023."
        ),
        "expected": {"name": "Elena Rostova", "company": "Baker & McKenzie LLP", "amount": 3850.0, "date": "2023-07-10"}
    },
    {
        "id": 13,
        "raw_text": (
            "CREDIT CARD STATEMENT LINE ITEM:\n"
            "Amazon Web Services (AWS) - Seattle, WA\n"
            "Cardholder: James O'Connor\n"
            "Transaction: $4,120.85 USD\n"
            "Posted Date: 2024-02-09"
        ),
        "expected": {"name": "James O'Connor", "company": "Amazon Web Services", "amount": 4120.85, "date": "2024-02-09"}
    },
    {
        "id": 14,
        "raw_text": (
            "Bill of Supply:\n"
            "Receiver: Fatima Al-Mansoor\n"
            "Merchant: Figma Design Inc\n"
            "Figma Organization Tier (15 seats)\n"
            "Total Paid: $675.00\n"
            "Date: 2023-12-20"
        ),
        "expected": {"name": "Fatima Al-Mansoor", "company": "Figma Design Inc", "amount": 675.0, "date": "2023-12-20"}
    },
    {
        "id": 15,
        "raw_text": (
            "From: accounting@notion.so\n"
            "To: Liam Murphy\n"
            "Subject: Your receipt from Notion Labs Inc\n"
            "Amount charged: $240.00 on 2024-03-25. View invoice online."
        ),
        "expected": {"name": "Liam Murphy", "company": "Notion Labs Inc", "amount": 240.0, "date": "2024-03-25"}
    }
]


# =====================================================================
# TOPIC 3: RETRY-ON-PARSE-FAILURE PATTERN (SELF-CORRECTION LOOP)
# =====================================================================
def extract_invoice_with_retry(raw_invoice_text: str, max_retries: int = 3) -> tuple[Invoice | None, int]:
    """
    Extracts invoice data into a validated Pydantic model.
    If the LLM generates an invalid schema or fails Pydantic validation rules,
    the exact ValidationError is fed back into the prompt for automated self-correction.

    Returns:
        tuple[Invoice | None, int]: The validated Invoice instance and the attempt count.
    """
    system_instruction = (
        "You are an expert financial data extraction engine. "
        "Extract the customer or recipient's name, company name, total dollar amount, and date "
        "from the provided messy invoice text.\n"
        "Normalize the date to strict YYYY-MM-DD format.\n"
        "Ensure the amount is a positive float without any currency signs."
    )

    # Initial prompt
    conversation = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": f"<invoice_text>\n{raw_invoice_text}\n</invoice_text>"}
    ]

    for attempt in range(1, max_retries + 1):
        try:
            # 1. Structured Output Call via OpenAI SDK / Gemini Endpoint
            response = client.beta.chat.completions.parse(
                model=MODEL,
                messages=conversation,
                response_format=Invoice,
                temperature=0.0
            )

            # 2. Extract parsed Pydantic object
            parsed_invoice: Invoice = response.choices[0].message.parsed

            if parsed_invoice is None:
                raise ValueError("Model returned empty or non-parseable output.")

            # Success!
            return parsed_invoice, attempt

        except ValidationError as val_err:
            # TOPIC 3: RETRY-ON-PARSE-FAILURE PATTERN
            # Feed the exact Pydantic validation failure back to the model
            print(f"   ⚠️ Validation Error on Attempt {attempt}: {val_err.errors()[0]['msg']}")
            error_feedback = (
                f"Your previous extraction failed Pydantic validation:\n"
                f"{str(val_err)}\n"
                f"Please correct the error and return a valid JSON object matching the Invoice schema."
            )
            conversation.append({"role": "assistant", "content": response.choices[0].message.content or ""})
            conversation.append({"role": "user", "content": error_feedback})

        except Exception as e:
            err = str(e)
            if "429" in err or "RateLimitError" in type(e).__name__:
                print(f"   ⏳ [Rate Limit] Sleeping 32s for free-tier quota reset...")
                time.sleep(32)
            else:
                print(f"   ⚠️ API/Parse Error on Attempt {attempt}: {err[:60]}")
                time.sleep(2)

    return None, max_retries


# =====================================================================
# BENCHMARK EXECUTION & VALIDATION REPORT
# =====================================================================
def main():
    print("=" * 95)
    print(" DAY 2 - SESSION 2: STRUCTURED OUTPUT & PYDANTIC EXTRACTION BENCHMARK")
    print("=" * 95)
    print(f"Model Under Test : {MODEL}")
    print(f"Total Invoices   : {len(MESSY_INVOICES)}")
    print(f"Target Schema    : Invoice(name: str, company: str, amount: float, date: YYYY-MM-DD)")
    print("=" * 95)

    successful_extractions = 0
    total_invoices = len(MESSY_INVOICES)

    print(f"\n{'ID':<4} {'Name':<20} {'Company':<28} {'Amount ($)':<12} {'Date':<12} {'Status'}")
    print("-" * 95)

    for item in MESSY_INVOICES:
        inv_id = item["id"]
        raw_text = item["raw_text"]

        invoice, attempts = extract_invoice_with_retry(raw_text)

        if invoice:
            successful_extractions += 1
            status = "✅ VALID" if attempts == 1 else f"✅ RETRIED ({attempts})"
            print(f"{inv_id:<4} {invoice.name[:18]:<20} {invoice.company[:26]:<28} {invoice.amount:<12.2f} {invoice.date:<12} {status}")
        else:
            print(f"{inv_id:<4} {'FAILED':<20} {'FAILED':<28} {'FAILED':<12} {'FAILED':<12} ❌ FAILED")

        # Pacing delay to respect the 15 requests/minute free-tier ceiling
        if inv_id < total_invoices:
            time.sleep(3.5)

    # -------------------------------------------------------------
    # FINAL SUMMARY REPORT
    # -------------------------------------------------------------
    success_rate = (successful_extractions / total_invoices) * 100

    print("-" * 95)
    print("\n" + "=" * 95)
    print(" EXTRACTION & VALIDATION REPORT")
    print("=" * 95)
    print(f"Total Invoices Processed : {total_invoices}")
    print(f"Pydantic Validated       : {successful_extractions}/{total_invoices} ({success_rate:.1f}%)")
    print(f"Validation Enforcements  : Strict YYYY-MM-DD dates, Positive Floats, Non-Empty Strings")
    print("=" * 95)
    print("Session 2 task completed successfully!")
    print("=" * 95)


if __name__ == "__main__":
    main()
