"""Tests for InvoiceExtraction schema and InvoiceValidator (Day 2 requirements)."""

from __future__ import annotations
import sys
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

# Ensure week5 directory is on path
WEEK5_DIR = Path(__file__).resolve().parent.parent
if str(WEEK5_DIR) not in sys.path:
    sys.path.insert(0, str(WEEK5_DIR))

from pydantic import ValidationError
from src.schemas import (
    CurrencyEnum,
    InvoiceExtraction,
    PaymentTermsEnum,
    parse_flexible_date,
    parse_flexible_decimal,
)
from src.validator import InvoiceValidator, ValidationResult


class TestSchemasAndValidation(unittest.TestCase):
    """Verifies strict typing, date parsing, decimal conversions, and domain validation."""

    def setUp(self):
        self.validator = InvoiceValidator()

    def test_valid_canonical_extraction(self):
        inv = InvoiceExtraction(
            invoice_id="INV-2024-001",
            invoice_date="2024-03-15",
            due_date="2024-04-14",
            vendor_name="Acme Industrial Corp",
            vendor_tax_id="US-12-3456789",
            customer_name="Global Logistics Ltd",
            currency="USD",
            subtotal="1,000.00",
            tax_amount="100.00",
            total_amount="1100.00",
            payment_terms="NET_30",
        )
        self.assertEqual(inv.invoice_id, "INV-2024-001")
        self.assertEqual(inv.invoice_date, date(2024, 3, 15))
        self.assertEqual(inv.due_date, date(2024, 4, 14))
        self.assertEqual(inv.subtotal, Decimal("1000.00"))
        self.assertEqual(inv.tax_amount, Decimal("100.00"))
        self.assertEqual(inv.total_amount, Decimal("1100.00"))
        self.assertEqual(inv.currency, CurrencyEnum.USD)
        self.assertEqual(inv.payment_terms, PaymentTermsEnum.NET_30)

    def test_flexible_date_parsing(self):
        self.assertEqual(parse_flexible_date("2024-05-10"), date(2024, 5, 10))
        self.assertEqual(parse_flexible_date("10/05/2024"), date(2024, 5, 10))
        self.assertEqual(parse_flexible_date("10 May 2024"), date(2024, 5, 10))
        self.assertIsNone(parse_flexible_date(None))
        self.assertIsNone(parse_flexible_date(""))
        self.assertIsNone(parse_flexible_date("null"))

    def test_reject_impossible_calendar_date(self):
        with self.assertRaises(ValidationError):
            InvoiceExtraction(invoice_date="2024-02-30")

    def test_reject_malformed_date_strings(self):
        with self.assertRaises(ValidationError):
            InvoiceExtraction(invoice_date="not-a-valid-date")

    def test_flexible_decimal_parsing(self):
        self.assertEqual(parse_flexible_decimal("$ 1,250.75"), Decimal("1250.75"))
        self.assertEqual(parse_flexible_decimal("€ 500,20"), Decimal("500.20"))
        self.assertEqual(parse_flexible_decimal(100.5), Decimal("100.50"))
        self.assertIsNone(parse_flexible_decimal(None))
        self.assertIsNone(parse_flexible_decimal(""))

    def test_currency_normalization(self):
        inv1 = InvoiceExtraction(currency="$")
        self.assertEqual(inv1.currency, CurrencyEnum.USD)
        inv2 = InvoiceExtraction(currency="€")
        self.assertEqual(inv2.currency, CurrencyEnum.EUR)
        inv3 = InvoiceExtraction(currency="£")
        self.assertEqual(inv3.currency, CurrencyEnum.GBP)

    def test_payment_terms_normalization(self):
        inv1 = InvoiceExtraction(payment_terms="Net 30 days")
        self.assertEqual(inv1.payment_terms, PaymentTermsEnum.NET_30)
        inv2 = InvoiceExtraction(payment_terms="due on receipt")
        self.assertEqual(inv2.payment_terms, PaymentTermsEnum.DUE_ON_RECEIPT)
        inv3 = InvoiceExtraction(payment_terms="UNKNOWN_RANDOM_TERM")
        self.assertEqual(inv3.payment_terms, PaymentTermsEnum.UNKNOWN)

    def test_prefix_stripping_on_invoice_id(self):
        inv = InvoiceExtraction(invoice_id="Invoice #: 98765")
        self.assertEqual(inv.invoice_id, "98765")

    def test_validator_arithmetic_coherence(self):
        # Valid math
        val_pass = self.validator.validate_raw({
            "invoice_id": "INV-100",
            "invoice_date": "2024-01-01",
            "subtotal": 100.0,
            "tax_amount": 10.0,
            "total_amount": 110.0,
        })
        self.assertTrue(val_pass.is_valid)
        self.assertTrue(val_pass.math_coherent)

        # Mismatched math: 100 + 10 != 150
        val_fail = self.validator.validate_raw({
            "invoice_id": "INV-100",
            "invoice_date": "2024-01-01",
            "subtotal": 100.0,
            "tax_amount": 10.0,
            "total_amount": 150.0,
        })
        self.assertFalse(val_fail.is_valid)
        self.assertFalse(val_fail.math_coherent)
        feedback = val_fail.get_retry_prompt_feedback()
        self.assertIn("ARITHMETIC_MISMATCH", feedback)

    def test_validator_chronological_coherence(self):
        # due_date earlier than invoice_date
        val_fail = self.validator.validate_raw({
            "invoice_id": "INV-100",
            "invoice_date": "2024-05-15",
            "due_date": "2024-05-01",
            "total_amount": 50.0,
        })
        self.assertFalse(val_fail.dates_coherent)
        feedback = val_fail.get_retry_prompt_feedback()
        self.assertIn("CHRONOLOGICAL_ERROR", feedback)


if __name__ == "__main__":
    unittest.main(verbosity=2)
