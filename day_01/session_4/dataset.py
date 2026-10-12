"""
Day 01 - Session 04: Benchmark Dataset
=======================================
A realistic dataset of 20 incoming customer support emails across 4 key operational categories:
  - Billing
  - Technical Support
  - Feature Request
  - Sales
"""

from typing import List, Dict, Any

DATASET: List[Dict[str, Any]] = [
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
        "email": "The latest desktop application crashes immediately on launch on macOS Sequoia. Crash logs are attached to this ticket."
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
        "email": "Please allow us to assign custom roles and granular permission sets to team members rather than just Admin and Member."
    },
    {
        "id": 15,
        "true_category": "Feature Request",
        "email": "It would save us hours if you supported bulk CSV import for customer contact records."
    },

    # --- Category 4: Sales (5 emails) ---
    {
        "id": 16,
        "true_category": "Sales",
        "email": "We have an engineering team of 140 people and want to discuss Enterprise pricing, SOC-2 compliance, and dedicated support SLAs."
    },
    {
        "id": 17,
        "true_category": "Sales",
        "email": "Can someone from your sales team jump on a 20-minute Zoom call this Thursday to demo the enterprise security add-on?"
    },
    {
        "id": 18,
        "true_category": "Sales",
        "email": "Do you offer annual volume discounting if we prepay for 500 team seats upfront across our European subsidiary?"
    },
    {
        "id": 19,
        "true_category": "Sales",
        "email": "We are currently evaluating your platform against Datadog. What does your migration assistance package look like for new enterprise customers?"
    },
    {
        "id": 20,
        "true_category": "Sales",
        "email": "I'm the Head of Procurement at Acme Corp. Please send us your master service agreement (MSA) and enterprise quote for 50 licenses."
    }
]
