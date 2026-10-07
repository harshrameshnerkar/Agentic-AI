"""
Database and Financial Diagnostic Tools with Real Production Failure Modes.
Includes a live SQLite database for realistic schema validation and query tracing.
"""

import sqlite3
from typing import Any, Dict, List


def get_in_memory_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE revenue_reports (
            id INTEGER PRIMARY KEY,
            region TEXT NOT NULL,
            quarter TEXT NOT NULL,
            gross_revenue_usd REAL NOT NULL,
            active_customers INTEGER NOT NULL
        )
    """)
    cursor.executemany("""
        INSERT INTO revenue_reports (region, quarter, gross_revenue_usd, active_customers)
        VALUES (?, ?, ?, ?)
    """, [
        ("North America", "Q3-2026", 4250000.0, 1420),
        ("Europe/EMEA", "Q3-2026", 3120000.0, 980),
        ("Asia/APAC", "Q3-2026", 2890000.0, 1150),
        ("Latin America", "Q3-2026", 840000.0, 310),
    ])
    conn.commit()
    return conn


# Singleton connection for testing
DB_CONN = get_in_memory_db()


def query_database(query_sql: str) -> Dict[str, Any]:
    """
    Executes a SQL query against the revenue reports database.
    Can raise real sqlite3.OperationalError if column or syntax is invalid.
    """
    cursor = DB_CONN.cursor()
    # Execute query directly to capture real database exceptions in traces!
    cursor.execute(query_sql)
    columns = [col[0] for col in cursor.description] if cursor.description else []
    rows = cursor.fetchall()
    results = [dict(zip(columns, row)) for row in rows]
    return {
        "status": "SUCCESS",
        "rows_count": len(results),
        "data": results,
    }


def convert_currency(amount_usd: float, target_currency: str) -> Dict[str, Any]:
    """Converts USD amount into EUR, GBP, or JPY."""
    rates = {"EUR": 0.92, "GBP": 0.78, "JPY": 152.0}
    curr = target_currency.upper().strip()
    rate = rates.get(curr)
    if not rate:
        raise ValueError(f"Unsupported target currency: '{target_currency}'. Supported: {list(rates.keys())}")
    return {
        "amount_usd": amount_usd,
        "target_currency": curr,
        "converted_amount": round(amount_usd * rate, 2),
        "rate": rate,
    }


OBSERVABILITY_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "query_database",
            "description": "Execute a SQL query against 'revenue_reports' table (columns: id, region, quarter, gross_revenue_usd, active_customers).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_sql": {
                        "type": "string",
                        "description": "SQL SELECT statement to run",
                    }
                },
                "required": ["query_sql"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "convert_currency",
            "description": "Convert USD revenue into target foreign currency (EUR, GBP, JPY).",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount_usd": {"type": "number", "description": "Amount in USD"},
                    "target_currency": {"type": "string", "description": "Target currency code (e.g. 'EUR')"},
                },
                "required": ["amount_usd", "target_currency"],
            },
        },
    },
]

OBSERVABILITY_TOOL_REGISTRY = {
    "query_database": query_database,
    "convert_currency": convert_currency,
}
