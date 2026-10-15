"""Extraction Schema for Week 5 Document Extraction Pipeline.

Defines the official 11-field Pydantic V2 extraction contract with strict typing:
- Dates as datetime.date (never loose strings)
- Monetary amounts as decimal.Decimal (prevent IEEE-754 precision drift)
- Fixed domain sets as Enums (CurrencyEnum, PaymentTermsEnum)
- Nullable/Optional handling per FIELD_SPECIFICATION.md
"""

from __future__ import annotations
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator


class CurrencyEnum(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CAD = "CAD"
    INR = "INR"


class PaymentTermsEnum(str, Enum):
    NET_15 = "NET_15"
    NET_30 = "NET_30"
    NET_45 = "NET_45"
    NET_60 = "NET_60"
    DUE_ON_RECEIPT = "DUE_ON_RECEIPT"
    UNKNOWN = "UNKNOWN"


def parse_flexible_date(val: Any) -> Optional[date]:
    """Parses various date representations into a canonical datetime.date object."""
    if val is None or val == "" or str(val).lower() in ("null", "none", "n/a", "unknown"):
        return None
    if isinstance(val, date):
        return val
    if isinstance(val, datetime):
        return val.date()

    val_str = str(val).strip()
    # Try ISO YYYY-MM-DD
    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d-%m-%Y",
        "%Y/%m/%d",
        "%d %b %Y",
        "%d %B %Y",
        "%b %d, %Y",
        "%B %d, %Y",
        "%Y%m%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(val_str, fmt).date()
        except ValueError:
            continue

    # Regex search for YYYY-MM-DD within string
    m = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', val_str)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass

    raise ValueError(f"Cannot parse '{val}' into a valid calendar date.")


def parse_flexible_decimal(val: Any) -> Optional[Decimal]:
    """Parses numeric values or currency strings ('$ 1,200.50', '214,41') into Decimal."""
    if val is None or val == "" or str(val).lower() in ("null", "none", "n/a", "unknown"):
        return None
    if isinstance(val, Decimal):
        return val.quantize(Decimal("0.01"))
    if isinstance(val, (int, float)):
        return Decimal(str(round(float(val), 2))).quantize(Decimal("0.01"))

    s = str(val).strip()
    # Remove currency symbols and extraneous whitespace
    s = re.sub(r'[\$\€\£\₹\¥A-Za-z]', '', s).strip()
    s = s.replace(' ', '')

    if not s:
        return None

    # Handle European vs US formatting (e.g. 1.200,50 vs 1,200.50)
    if ',' in s and '.' in s:
        if s.rfind(',') > s.rfind('.'):
            s = s.replace('.', '').replace(',', '.')
        else:
            s = s.replace(',', '')
    elif ',' in s:
        s = s.replace(',', '.')

    try:
        d = Decimal(s)
        return d.quantize(Decimal("0.01"))
    except InvalidOperation:
        raise ValueError(f"Cannot parse '{val}' into a valid monetary Decimal.")


class InvoiceExtraction(BaseModel):
    """Pydantic schema enforcing the 11-field commercial invoice contract."""

    invoice_id: Optional[str] = Field(
        default=None,
        description="Unique reference identifier printed on the invoice (e.g., 'INV-2024-1001', '36258').",
    )
    invoice_date: Optional[date] = Field(
        default=None,
        description="Official issue/transaction date as ISO YYYY-MM-DD. Never synthesize or default to today.",
    )
    due_date: Optional[date] = Field(
        default=None,
        description="Explicit printed payment deadline date as ISO YYYY-MM-DD. None if omitted.",
    )
    vendor_name: Optional[str] = Field(
        default=None,
        description="Legal business name or trade name of billing vendor.",
    )
    vendor_tax_id: Optional[str] = Field(
        default=None,
        description="Tax registration / VAT / EIN / GSTIN number of the vendor. None if omitted.",
    )
    customer_name: Optional[str] = Field(
        default=None,
        description="Entity or person to whom goods/services are billed.",
    )
    currency: Optional[CurrencyEnum] = Field(
        default=None,
        description="ISO 4217 3-letter currency code (USD, EUR, GBP, CAD, INR).",
    )
    subtotal: Optional[Decimal] = Field(
        default=None,
        description="Total monetary amount before taxes and discounts with 2 decimal places.",
    )
    tax_amount: Optional[Decimal] = Field(
        default=Decimal("0.00"),
        description="Cumulative tax amount with 2 decimal places. 0.00 if tax-exempt.",
    )
    total_amount: Optional[Decimal] = Field(
        default=None,
        description="Final gross monetary amount payable by customer with 2 decimal places.",
    )
    payment_terms: PaymentTermsEnum = Field(
        default=PaymentTermsEnum.UNKNOWN,
        description="Standardized payment terms code (e.g. NET_30, DUE_ON_RECEIPT, UNKNOWN).",
    )

    # Field validators for real types & cleaning
    @field_validator("invoice_id", mode="before")
    @classmethod
    def clean_invoice_id(cls, v: Any) -> Optional[str]:
        if v is None or v == "" or str(v).lower() in ("null", "none", "n/a"):
            return None
        s = str(v).strip()
        # Strip common prefixes like 'Invoice #:', 'Inv No.', '#'
        s = re.sub(r'^(?:invoice\s*(?:#|no\.?|num\.?)?:?|#\s*)', '', s, flags=re.IGNORECASE).strip()
        return s or None

    @field_validator("invoice_date", "due_date", mode="before")
    @classmethod
    def validate_dates(cls, v: Any) -> Optional[date]:
        return parse_flexible_date(v)

    @field_validator("subtotal", "tax_amount", "total_amount", mode="before")
    @classmethod
    def validate_decimals(cls, v: Any) -> Optional[Decimal]:
        return parse_flexible_decimal(v)

    @field_validator("currency", mode="before")
    @classmethod
    def validate_currency(cls, v: Any) -> Optional[CurrencyEnum]:
        if v is None or v == "" or str(v).lower() in ("null", "none", "n/a"):
            return None
        s = str(v).strip().upper()
        symbol_map = {"$": "USD", "€": "EUR", "£": "GBP", "₹": "INR", "C$": "CAD"}
        s = symbol_map.get(s, s)
        try:
            return CurrencyEnum(s)
        except ValueError:
            return None

    @field_validator("payment_terms", mode="before")
    @classmethod
    def validate_payment_terms(cls, v: Any) -> PaymentTermsEnum:
        if v is None or v == "" or str(v).lower() in ("null", "none", "n/a"):
            return PaymentTermsEnum.UNKNOWN
        s = str(v).strip().upper().replace(" ", "_").replace("-", "_")
        if "RECEIPT" in s:
            return PaymentTermsEnum.DUE_ON_RECEIPT
        if "30" in s:
            return PaymentTermsEnum.NET_30
        if "15" in s:
            return PaymentTermsEnum.NET_15
        if "45" in s:
            return PaymentTermsEnum.NET_45
        if "60" in s:
            return PaymentTermsEnum.NET_60
        try:
            return PaymentTermsEnum(s)
        except ValueError:
            return PaymentTermsEnum.UNKNOWN

    @field_validator("vendor_tax_id", mode="before")
    @classmethod
    def clean_tax_id(cls, v: Any) -> Optional[str]:
        if v is None or v == "" or str(v).lower() in ("null", "none", "n/a"):
            return None
        s = str(v).strip()
        s = re.sub(r'^(?:tax\s*id|vat(?:\s*no\.?)?|ein|gstin):?\s*', '', s, flags=re.IGNORECASE).strip()
        return s or None

    def to_ground_truth_dict(self) -> Dict[str, Any]:
        """Serializes extraction into format compatible with ground_truth_40.json."""
        return {
            "invoice_id": self.invoice_id,
            "invoice_date": self.invoice_date.isoformat() if self.invoice_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "vendor_name": self.vendor_name,
            "vendor_tax_id": self.vendor_tax_id,
            "customer_name": self.customer_name,
            "currency": self.currency.value if self.currency else None,
            "subtotal": float(self.subtotal) if self.subtotal is not None else None,
            "tax_amount": float(self.tax_amount) if self.tax_amount is not None else 0.0,
            "total_amount": float(self.total_amount) if self.total_amount is not None else None,
            "payment_terms": self.payment_terms.value,
        }
