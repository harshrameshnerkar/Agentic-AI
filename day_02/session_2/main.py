"""
Day 02 - Session 02: Structured Output & Pydantic Validation
Extract strongly-typed, schema-validated Invoice objects from raw text
using OpenAI's parse() endpoint and Pydantic models.
"""

import os
import re
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field, field_validator
from dataset import MESSY_INVOICES

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
model = os.getenv("OPENAI_MODEL", "gemini-3.1-flash-lite")

if not api_key:
    raise ValueError("Missing API key in .env")

client = OpenAI(api_key=api_key, base_url=base_url)


# 1. Define the validated schema
class Invoice(BaseModel):
    name: str = Field(description="Full name of customer or recipient")
    company: str = Field(description="Vendor or issuing company name")
    amount: float = Field(gt=0, description="Total amount in USD as a positive number")
    date: str = Field(description="Date formatted strictly as YYYY-MM-DD")

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        clean = v.strip()
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", clean):
            raise ValueError(f"Date '{clean}' must be in YYYY-MM-DD format.")
        datetime.strptime(clean, "%Y-%m-%d")
        return clean


def extract_invoice(text: str) -> Invoice | None:
    """Extracts an Invoice object from unstructured text."""
    try:
        response = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": "Extract invoice details into structured format. Normalize dates to YYYY-MM-DD."},
                {"role": "user", "content": f"Invoice text:\n{text}"}
            ],
            response_format=Invoice,
            temperature=0.0
        )
        return response.choices[0].message.parsed
    except Exception as e:
        print(f"Extraction error: {e}")
        return None


def main():
    print(f"Extracting invoices from {len(MESSY_INVOICES)} sample documents...\n")

    for item in MESSY_INVOICES:
        inv = extract_invoice(item["raw_text"])
        if inv:
            print(f"[SUCCESS] #{item['id']}")
            print(f"  Customer: {inv.name}")
            print(f"  Company:  {inv.company}")
            print(f"  Amount:   ${inv.amount:.2f}")
            print(f"  Date:     {inv.date}\n")
        else:
            print(f"[FAILED] #{item['id']}\n")


if __name__ == "__main__":
    main()
