"""
Enterprise Tools for Agent Evaluation Test Suite.
Exposes mock operational capabilities across:
- Relational Database / SQL Analytics
- Knowledge Base / Documentation Search
- Math / Metric Computation
- Filesystem & Log Inspection
- Incident Alerting & Notifications
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

# Mock in-memory documentation
DOC_STORE = {
    "auth_sop": "Enterprise microservices require mutual TLS (mTLS) with RS256 JWT tokens rotated every 90 days.",
    "oncall_rotation": "Primary on-call responds within 15 minutes to Sev-1 alerts via PagerDuty bridge #incident-room.",
    "rate_limits": "Standard API tier is rate-limited to 60 requests/minute. Enterprise tier is provisioned for 1000 requests/minute.",
    "sla_tiers": "Tier 1 SLA guarantees 99.9% uptime with 2-hour response; Tier 2 guarantees 99.95% uptime with 30-min response.",
    "data_retention": "Customer transaction records must be retained in cold storage for 7 years per financial compliance mandate.",
}

# Mock virtual filesystem
VIRTUAL_FILESYSTEM = {
    "/var/log/syslog": "2026-10-06T04:12:00Z [INFO] Service started.\n2026-10-06T04:15:22Z [WARN] Memory pressure 82%.\n2026-10-06T04:18:45Z [ERROR] DB connection pool exhausted (timeout 30s).",
    "/etc/config.json": json.dumps({"app_name": "GatewayService", "port": 8080, "max_connections": 500, "ssl_enabled": True}, indent=2),
    "/app/manifest.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: checkout-api\nspec:\n  replicas: 4\n  strategy: RollingUpdate",
    "/var/log/auth.log": "2026-10-06T05:01:10Z [AUTH] Successful login for admin from 10.0.4.12.\n2026-10-06T05:02:15Z [AUTH] Failed login for user guest from 192.168.1.5.",
}


def tool_query_database(table: str, filter_column: Optional[str] = None, filter_value: Optional[str] = None) -> Dict[str, Any]:
    """Queries relational tables in database (tables: customers, orders, inventory)."""
    tbl = table.lower().strip()
    if tbl not in DB_TABLES:
        return {"status": "ERROR", "error": f"Table '{table}' does not exist. Available tables: {list(DB_TABLES.keys())}"}

    rows = DB_TABLES[tbl]
    if filter_column and filter_value:
        filtered = [
            r for r in rows
            if str(r.get(filter_column, "")).lower() == str(filter_value).lower()
        ]
        return {"status": "SUCCESS", "table": tbl, "row_count": len(filtered), "rows": filtered}

    return {"status": "SUCCESS", "table": tbl, "row_count": len(rows), "rows": rows}


def tool_search_docs(keyword: str) -> Dict[str, Any]:
    """Searches company knowledge base and SOP documentation."""
    kw = keyword.lower().strip()
    results = []
    for doc_key, content in DOC_STORE.items():
        if any(term in content.lower() or term in doc_key for term in kw.split()):
            results.append({"doc_id": doc_key, "content": content})

    if not results:
        # Fallback closest match or empty
        return {"status": "NOT_FOUND", "message": f"No documents found matching keyword: '{keyword}'"}

    return {"status": "SUCCESS", "match_count": len(results), "documents": results}


def tool_calculate(expression: str) -> Dict[str, Any]:
    """Safely evaluates basic mathematical and metric expressions."""
    clean_expr = expression.replace(",", "").replace("$", "").replace("%", "/100")
    # Only allow safe mathematical characters
    allowed_chars = set("0123456789+-*/(). ")
    if not set(clean_expr).issubset(allowed_chars):
        return {"status": "ERROR", "error": "Invalid mathematical characters in expression."}

    try:
        result = eval(clean_expr, {"__builtins__": None}, {})
        return {"status": "SUCCESS", "expression": expression, "result": round(float(result), 4)}
    except Exception as e:
        return {"status": "ERROR", "error": f"Calculation failed: {str(e)}"}


def tool_read_file(path: str) -> Dict[str, Any]:
    """Reads configuration or log files from virtual filesystem."""
    p = path.strip()
    if p in VIRTUAL_FILESYSTEM:
        return {"status": "SUCCESS", "filepath": p, "content": VIRTUAL_FILESYSTEM[p]}
    return {"status": "ERROR", "error": f"FileNotFound: '{path}' does not exist. Available: {list(VIRTUAL_FILESYSTEM.keys())}"}


def tool_list_dir(path: str) -> Dict[str, Any]:
    """Lists files in virtual directory."""
    p = path.rstrip("/")
    matching = [k for k in VIRTUAL_FILESYSTEM.keys() if k.startswith(p)]
    return {"status": "SUCCESS", "directory": path, "files": matching}


def tool_send_alert(level: str, channel: str, message: str) -> Dict[str, Any]:
    """Sends notification or escalation alert to operations channels."""
    valid_levels = ["INFO", "WARN", "SEV-1", "SEV-2", "CRITICAL"]
    lvl = level.upper().strip()
    if lvl not in valid_levels:
        lvl = "WARN"

    return {
        "status": "ALERT_DISPATCHED",
        "level": lvl,
        "channel": channel,
        "message": message,
    }


AGENT_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "query_database",
            "description": "Query database tables ('customers', 'orders', 'inventory') with optional filter column and value.",
            "parameters": {
                "type": "object",
                "properties": {
                    "table": {"type": "string", "description": "Database table name: 'customers', 'orders', or 'inventory'"},
                    "filter_column": {"type": "string", "description": "Optional column to filter by"},
                    "filter_value": {"type": "string", "description": "Optional value to filter by"}
                },
                "required": ["table"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_docs",
            "description": "Search internal company documentation, policies, and SOPs by keyword.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "Search keywords (e.g., 'auth', 'oncall', 'rate limits')"}
                },
                "required": ["keyword"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluate mathematical expressions, metric calculations, or financial formulas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Math expression (e.g. '12500 * 12', '1450 + 890.5')"}
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read file contents from virtual server paths (e.g. '/var/log/syslog', '/etc/config.json').",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute virtual file path"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "List files available under a virtual directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path (e.g. '/var/log', '/etc')"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_alert",
            "description": "Dispatch operational escalation alerts to Slack or PagerDuty channels.",
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {"type": "string", "description": "Alert severity level: 'INFO', 'WARN', 'CRITICAL', 'SEV-1'"},
                    "channel": {"type": "string", "description": "Target alert channel (e.g., '#incident-room', '#ops-alerts')"},
                    "message": {"type": "string", "description": "Alert summary description"}
                },
                "required": ["level", "channel", "message"],
            },
        },
    },
]
