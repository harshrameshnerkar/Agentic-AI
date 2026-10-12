"""
Day 02 - Session 02: Structured Output & Pydantic Validation
============================================================
Demonstrates extracting strongly-typed, schema-validated domain objects
from unstructured text with automated self-correction on validation failure.
"""

import os
import sys
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field, field_validator, ValidationError

from dataset import MESSY_INVOICES

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
# Domain Model: Strict Invoice Schema
# ---------------------------------------------------------------------------
class Invoice(BaseModel):
    """
    Validated Pydantic model enforcing type safety and business rules.
    """
    name: str = Field(description="Full name of customer or recipient individual")
    company: str = Field(description="Name of the company or vendor issuing/receiving invoice")
    amount: float = Field(gt=0, description="Total invoice amount in USD as a positive float")
    date: str = Field(description="Standardized date formatted strictly as YYYY-MM-DD")

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        clean_date = v.strip()
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", clean_date):
            raise ValueError(f"Date '{clean_date}' must follow strict YYYY-MM-DD format.")
        try:
            datetime.strptime(clean_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Date '{clean_date}' is not a valid calendar date.")
        return clean_date

    @field_validator("name", "company")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        clean_text = v.strip()
        if not clean_text:
            raise ValueError("Field cannot be empty.")
        return clean_text


def extract_invoice_with_retry(raw_text: str, max_retries: int = 2) -> Tuple[Optional[Invoice], int]:
    """
    Extracts an Invoice using structured output parsing.
    If a Pydantic ValidationError occurs, the error feedback is appended
    to the conversation for automated LLM self-correction.
    """
    system_instruction = (
        "You are an automated invoice extraction system. "
        "Extract the customer name, company name, total dollar amount, and date. "
        "Normalize the date to strict YYYY-MM-DD format. "
        "Ensure the amount is a positive number without currency signs."
    )

    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": f"<invoice_text>\n{raw_text}\n</invoice_text>"}
    ]

    for attempt in range(1, max_retries + 1):
        try:
            response = client.beta.chat.completions.parse(
                model=MODEL,
                messages=messages,
                response_format=Invoice,
                temperature=0.0
            )

            parsed_invoice = response.choices[0].message.parsed
            if parsed_invoice:
                return parsed_invoice, attempt

        except ValidationError as err:
            # Self-correction prompt loop
            err_msg = err.errors()[0]["msg"]
            print(f"    [Validation Retry {attempt}] Feeding error back to LLM: {err_msg}")
            messages.append({"role": "assistant", "content": response.choices[0].message.content or ""})
            messages.append({
                "role": "user",
                "content": f"The previous extraction failed validation: {err_msg}. Please fix and return matching schema."
            })
        except Exception as e:
            print(f"    [Attempt {attempt} Error] {e}")

    return None, max_retries


def main() -> None:
    print("=" * 80)
    print(" DAY 02 - SESSION 02: STRUCTURED OUTPUT & PYDANTIC EXTRACTION")
    print("=" * 80)
    print(f"Active Model       : {MODEL}")
    print(f"Total Invoices     : {len(MESSY_INVOICES)}")
    print("Target Schema      : Invoice(name, company, amount, date: YYYY-MM-DD)")
    print("=" * 80)
    print()

    successful = 0

    print(f"{'#':<3} {'Customer Name':<20} {'Company':<25} {'Amount':<10} {'Date':<12} {'Status'}")
    print("-" * 80)

    for item in MESSY_INVOICES:
        i_id = item["id"]
        raw_text = item["raw_text"]

        invoice, attempts = extract_invoice_with_retry(raw_text)

        if invoice:
            successful += 1
            status = f"PASS ({attempts}x)"
            print(f"{i_id:<3} {invoice.name[:18]:<20} {invoice.company[:23]:<25} ${invoice.amount:<9.2f} {invoice.date:<12} {status}")
        else:
            print(f"{i_id:<3} {'FAILED':<20} {'FAILED':<25} {'N/A':<10} {'N/A':<12} FAIL")

    print("-" * 80)
    success_rate = (successful / len(MESSY_INVOICES)) * 100.0 if MESSY_INVOICES else 0.0
    print(f"Extraction Accuracy: {successful}/{len(MESSY_INVOICES)} ({success_rate:.1f}%)")
    print("=" * 80)
    print("Structured output extraction completed successfully.\n")


if __name__ == "__main__":
    main()
