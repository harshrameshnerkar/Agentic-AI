"""
Day 02 - Session 03: A/B Testing Benchmark Dataset
===================================================
8 incoming customer support emails across Billing, Tech Support, Feature Request, and Sales.
"""

from typing import List, Dict, Any

BENCHMARK_EMAILS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "true_category": "Billing",
        "email": "I was charged twice ($99.00 each) on my Visa card for this month's Pro subscription. Please reverse the duplicate charge."
    },
    {
        "id": 2,
        "true_category": "Billing",
        "email": "Can you please send our corporate accounting department an updated official VAT tax invoice with our registered company number?"
    },
    {
        "id": 3,
        "true_category": "Technical Support",
        "email": "Whenever we attempt to login using Okta SAML SSO, your identity gateway throws an HTTP 500 Internal Server Error."
    },
    {
        "id": 4,
        "true_category": "Technical Support",
        "email": "Our automated nightly backup job timed out after 30 minutes with error code ETIMEDOUT while attempting to connect to your API."
    },
    {
        "id": 5,
        "true_category": "Feature Request",
        "email": "Would it be possible to add direct export to Google Drive and OneDrive? It would save our compliance team several hours each week."
    },
    {
        "id": 6,
        "true_category": "Feature Request",
        "email": "We really need a dark mode theme for your desktop client. Working late at night in pure white background is causing severe eye fatigue."
    },
    {
        "id": 7,
        "true_category": "Sales",
        "email": "We have 350 developers on our engineering team and are looking to purchase enterprise licenses with dedicated 99.99% uptime SLAs."
    },
    {
        "id": 8,
        "true_category": "Sales",
        "email": "Could someone from your enterprise sales group schedule a demo with our VP of Engineering to discuss annual contract pricing?"
    }
]
