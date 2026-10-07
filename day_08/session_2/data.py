"""
Raw Multi-Currency Cloud Infrastructure Spending Dataset.
Ground Truth benchmark data for comparing Fixed Pipeline vs Autonomous Agent.
"""

from typing import Any, Dict, List

# Exchange rates to USD
EXCHANGE_RATES = {
    "USD": 1.0,
    "EUR": 1.08,
    "GBP": 1.28,
}

# Raw monthly invoice line-items
RAW_INVOICES: List[Dict[str, Any]] = [
    {
        "invoice_id": "INV-2026-001",
        "vendor": "AWS",
        "service": "AWS EC2 & ECS Compute Cluster",
        "category": "Compute",
        "amount": 14500.00,
        "currency": "USD",
        "monthly_budget_usd": 13000.00,
    },
    {
        "invoice_id": "INV-2026-002",
        "vendor": "Snowflake",
        "service": "Snowflake Data Cloud Warehouse",
        "category": "Data Warehouse",
        "amount": 18200.00,
        "currency": "EUR",
        "monthly_budget_usd": 15000.00,
    },
    {
        "invoice_id": "INV-2026-003",
        "vendor": "Google Cloud",
        "service": "Google Cloud Vertex AI & BigQuery",
        "category": "AI / Data",
        "amount": 12400.00,
        "currency": "USD",
        "monthly_budget_usd": 12000.00,
    },
    {
        "invoice_id": "INV-2026-004",
        "vendor": "Datadog",
        "service": "Datadog APM & Log Management",
        "category": "Observability",
        "amount": 7500.00,
        "currency": "GBP",
        "monthly_budget_usd": 7000.00,
    },
    {
        "invoice_id": "INV-2026-005",
        "vendor": "Cloudflare",
        "service": "Cloudflare Enterprise CDN & WAF",
        "category": "Networking",
        "amount": 3800.00,
        "currency": "USD",
        "monthly_budget_usd": 4000.00,
    },
]

# Mathematical Ground Truth
GROUND_TRUTH = {
    "normalized_items": [
        {"service": "AWS EC2 & ECS Compute Cluster", "cost_usd": 14500.00, "over_budget_pct": 11.54, "is_anomaly": False},
        {"service": "Snowflake Data Cloud Warehouse", "cost_usd": 19656.00, "over_budget_pct": 31.04, "is_anomaly": True},
        {"service": "Google Cloud Vertex AI & BigQuery", "cost_usd": 12400.00, "over_budget_pct": 3.33, "is_anomaly": False},
        {"service": "Datadog APM & Log Management", "cost_usd": 9600.00, "over_budget_pct": 37.14, "is_anomaly": True},
        {"service": "Cloudflare Enterprise CDN & WAF", "cost_usd": 3800.00, "over_budget_pct": -5.00, "is_anomaly": False},
    ],
    "total_spend_usd": 59956.00,
    "top_3_services": [
        {"service": "Snowflake Data Cloud Warehouse", "cost_usd": 19656.00},
        {"service": "AWS EC2 & ECS Compute Cluster", "cost_usd": 14500.00},
        {"service": "Google Cloud Vertex AI & BigQuery", "cost_usd": 12400.00},
    ],
    "anomalies": [
        {"service": "Datadog APM & Log Management", "cost_usd": 9600.00, "budget_usd": 7000.00, "variance_pct": 37.14},
        {"service": "Snowflake Data Cloud Warehouse", "cost_usd": 19656.00, "budget_usd": 15000.00, "variance_pct": 31.04},
    ],
}
