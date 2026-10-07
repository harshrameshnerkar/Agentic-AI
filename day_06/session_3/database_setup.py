"""
Day 6 - Session 3: Multi-Step Tool Use
Module: database_setup.py

Initializes SQLite database 'incident_system.db' for enterprise incident processing:
1. customers: SLA tier, account balances, contacts.
2. incidents: Production incident telemetry, downtime minutes, affected services.
3. credit_ledger: Financial adjustment records protected by an IDEMPOTENCY KEY.
"""

from __future__ import annotations
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "incident_system.db"


def init_database() -> Path:
    """Creates tables and populates baseline records for incident and ledger processing."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Table 1: Customers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            company_name TEXT NOT NULL,
            sla_tier TEXT NOT NULL,
            manager_email TEXT NOT NULL,
            credit_balance_usd REAL NOT NULL DEFAULT 0.0
        );
    """)

    # Table 2: Incidents
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            ticket_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            service_name TEXT NOT NULL,
            downtime_minutes INTEGER NOT NULL,
            severity TEXT NOT NULL,
            root_cause TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        );
    """)

    # Table 3: Credit Ledger (Side-effecting table requiring idempotency protection)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS credit_ledger (
            idempotency_key TEXT PRIMARY KEY,
            transaction_id TEXT NOT NULL UNIQUE,
            ticket_id TEXT NOT NULL,
            customer_id TEXT NOT NULL,
            amount_usd REAL NOT NULL,
            manager_email TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (ticket_id) REFERENCES incidents(ticket_id)
        );
    """)

    # Seed baseline customers
    cursor.execute("DELETE FROM customers;")
    cursor.execute("DELETE FROM incidents;")
    # (Do not wipe credit_ledger unnecessarily if preserved, but for clean tests we can reinitialize)
    cursor.execute("DELETE FROM credit_ledger;")

    customers_data = [
        ("CUST-901", "Apex Logistics Global", "Enterprise Platinum", "ops-lead@apexlogistics.com", 12500.00),
        ("CUST-902", "Nexus Fintech Core", "Enterprise Gold", "billing@nexusfintech.io", 5400.00),
        ("CUST-903", "Starlight Health Systems", "Standard Business", "admin@starlighthealth.org", 850.00)
    ]
    cursor.executemany(
        "INSERT INTO customers (customer_id, company_name, sla_tier, manager_email, credit_balance_usd) VALUES (?, ?, ?, ?, ?);",
        customers_data
    )

    # Seed incidents
    incidents_data = [
        ("INC-8042", "CUST-901", "Cloud Storage Gateway", 145, "CRITICAL", "Upstream fiber degradation and storage replica timeout", "RESOLVED"),
        ("INC-8043", "CUST-902", "Realtime Payment Ingress", 45, "HIGH", "SSL certificate renegotiation lock contention", "RESOLVED"),
        ("INC-8044", "CUST-903", "Batch Report Dispatcher", 210, "MEDIUM", "Out of memory in ephemeral container pod", "INVESTIGATING")
    ]
    cursor.executemany(
        "INSERT INTO incidents (ticket_id, customer_id, service_name, downtime_minutes, severity, root_cause, status) VALUES (?, ?, ?, ?, ?, ?, ?);",
        incidents_data
    )

    conn.commit()
    conn.close()
    return DB_PATH


if __name__ == "__main__":
    db = init_database()
    print(f"[Database Setup] 'incident_system.db' successfully initialized at {db}")
