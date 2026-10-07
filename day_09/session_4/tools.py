"""
Enterprise Operational Tools for Cost & Latency Benchmark.
"""

import json
from typing import Any, Dict, List, Optional

# Mock in-memory database
DB_TABLES = {
    "customers": [
        {"customer_id": "C-101", "name": "Acme Corp", "tier": "Enterprise", "mrr": 12500, "status": "Active"},
        {"customer_id": "C-102", "name": "Globex Inc", "tier": "Pro", "mrr": 3200, "status": "Active"},
        {"customer_id": "C-103", "name": "Soylent Corp", "tier": "Enterprise", "mrr": 18000, "status": "Churned"},
        {"customer_id": "C-104", "name": "Initech", "tier": "Standard", "mrr": 1200, "status": "Active"},
        {"customer_id": "C-105", "name": "Umbrella Corp", "tier": "Enterprise", "mrr": 25000, "status": "Active"},
    ],
    "orders": [
        {"order_id": "ORD-501", "customer_id": "C-101", "amount": 1450.00, "status": "Shipped", "date": "2026-09-15"},
        {"order_id": "ORD-502", "customer_id": "C-102", "amount": 890.50, "status": "Processing", "date": "2026-09-18"},
        {"order_id": "ORD-503", "customer_id": "C-104", "amount": 2100.00, "status": "Delivered", "date": "2026-09-20"},
        {"order_id": "ORD-504", "customer_id": "C-105", "amount": 12500.00, "status": "Shipped", "date": "2026-09-22"},
    ],
    "inventory": [
        {"sku": "SKU-RACK-01", "item_name": "Server Rack Unit 42U", "stock": 14, "warehouse": "US-East", "cost": 850.00},
        {"sku": "SKU-SWITCH-24", "item_name": "24-Port Managed Switch", "stock": 42, "warehouse": "US-West", "cost": 320.00},
        {"sku": "SKU-SFP-10G", "item_name": "10G Optical Transceiver", "stock": 180, "warehouse": "EU-Central", "cost": 45.00},
        {"sku": "SKU-UPS-3000", "item_name": "3000VA UPS Battery", "stock": 6, "warehouse": "US-East", "cost": 1200.00},
    ],
}

DOC_STORE = {
    "auth_sop": "Enterprise microservices require mutual TLS (mTLS) with RS256 JWT tokens rotated every 90 days.",
    "oncall_rotation": "Primary on-call responds within 15 minutes to Sev-1 alerts via PagerDuty bridge #incident-room.",
    "rate_limits": "Standard API tier is rate-limited to 60 requests/minute. Enterprise tier is provisioned for 1000 requests/minute.",
    "sla_tiers": "Tier 1 SLA guarantees 99.9% uptime with 2-hour response; Tier 2 guarantees 99.95% uptime with 30-min response.",
}

VIRTUAL_LOGS = {
    "/var/log/syslog": (
        "2026-10-06T04:12:00Z [INFO] GatewayService startup initialized.\n"
        "2026-10-06T04:15:22Z [WARN] Memory pressure 82% on worker pod-4.\n"
        "2026-10-06T04:18:45Z [ERROR] DB connection pool exhausted (timeout 30s).\n"
        "2026-10-06T04:20:01Z [INFO] Health check probe failed for endpoint /health."
    )
}


def tool_query_database(table: str, filter_column: Optional[str] = None, filter_value: Optional[str] = None) -> Dict[str, Any]:
    """Queries relational database tables ('customers', 'orders', 'inventory')."""
    tbl = table.lower().strip()
    if tbl not in DB_TABLES:
        return {"status": "ERROR", "error": f"Table '{table}' not found."}

    rows = DB_TABLES[tbl]
    if filter_column and filter_value:
        filtered = [r for r in rows if str(r.get(filter_column, "")).lower() == str(filter_value).lower()]
        return {"status": "SUCCESS", "table": tbl, "rows": filtered}

    return {"status": "SUCCESS", "table": tbl, "rows": rows}


def tool_search_docs(keyword: str) -> Dict[str, Any]:
    """Searches corporate SOPs and security documentation."""
    kw = keyword.lower().strip()
    matches = []
    for k, text in DOC_STORE.items():
        if any(term in text.lower() or term in k for term in kw.split()):
            matches.append({"doc_id": k, "content": text})
    return {"status": "SUCCESS", "matches": matches} if matches else {"status": "NOT_FOUND", "matches": []}


def tool_calculate(expression: str) -> Dict[str, Any]:
    """Evaluates mathematical expressions."""
    clean = expression.replace(",", "").replace("$", "").replace("%", "/100")
    try:
        res = eval(clean, {"__builtins__": None}, {})
        return {"status": "SUCCESS", "expression": expression, "result": round(float(res), 4)}
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}


def tool_read_log(path: str) -> Dict[str, Any]:
    """Reads system log contents."""
    p = path.strip()
    if p in VIRTUAL_LOGS:
        return {"status": "SUCCESS", "filepath": p, "content": VIRTUAL_LOGS[p]}
    return {"status": "ERROR", "error": f"Log file '{path}' not found."}


OPTIMIZED_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "query_database",
            "description": "Query tables: customers, orders, inventory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "table": {"type": "string"},
                    "filter_column": {"type": "string"},
                    "filter_value": {"type": "string"},
                },
                "required": ["table"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_docs",
            "description": "Search SOPs and policies by keyword.",
            "parameters": {
                "type": "object",
                "properties": {"keyword": {"type": "string"}},
                "required": ["keyword"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluate math and metric expressions.",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_log",
            "description": "Read server log file (e.g. /var/log/syslog).",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
]
