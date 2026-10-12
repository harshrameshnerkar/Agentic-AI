"""
Day 02 - Session 02: Invoice Extraction Benchmark Dataset
==========================================================
15 messy, realistic invoice receipts, email notifications, and statement line items.
"""

from typing import List, Dict, Any

MESSY_INVOICES: List[Dict[str, Any]] = [
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
            "Payment notification for Marcus Aurelius Vance representing Roma Design Studio. "
            "Charges: 3,200.75 USD. Billing finalized on 02-18-2024."
        ),
        "expected": {"name": "Marcus Aurelius Vance", "company": "Roma Design Studio", "amount": 3200.75, "date": "2024-02-18"}
    },
    {
        "id": 4,
        "raw_text": (
            "Vendor: Datadog Monitoring\n"
            "Customer: Elena Rostova\n"
            "Period: March 2024\n"
            "Amount due: $450.00\n"
            "Date: 2024-03-31"
        ),
        "expected": {"name": "Elena Rostova", "company": "Datadog Monitoring", "amount": 450.0, "date": "2024-03-31"}
    },
    {
        "id": 5,
        "raw_text": (
            "Statement of Account:\n"
            "Recipient: David Chen\n"
            "Provider: Snowflake Computing LLC\n"
            "Total Incurred: $2,840.50\n"
            "Invoice Date: 12/04/2023"
        ),
        "expected": {"name": "David Chen", "company": "Snowflake Computing LLC", "amount": 2840.50, "date": "2023-12-04"}
    }
]
