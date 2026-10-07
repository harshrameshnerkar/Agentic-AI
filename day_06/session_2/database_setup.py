"""
Day 6 - Session 2: Designing Good Tools
Module: database_setup.py

Description:
    Seeds a realistic SQLite enterprise database ('enterprise_data.db')
    with sample tables:
    1. employees (team members, departments, salaries, emails)
    2. products (inventory items, categories, pricing, stock levels)
    3. orders (customer purchases, SKUs, order values, status)
"""

from __future__ import annotations
import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).resolve().parent / "enterprise_data.db"


def init_database() -> Path:
    """Initializes and seeds the SQLite database with clean enterprise tables."""
    if DB_FILE.exists():
        DB_FILE.unlink()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 1. Employees Table
    cursor.execute("""
        CREATE TABLE employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            role TEXT NOT NULL,
            salary REAL NOT NULL,
            email TEXT UNIQUE NOT NULL,
            hire_date TEXT NOT NULL
        );
    """)

    employees_data = [
        ("Alice Chen", "Engineering", "Principal AI Architect", 185000.0, "alice.chen@enterprise.io", "2023-01-15"),
        ("Marcus Vance", "Engineering", "Senior DevOps Engineer", 145000.0, "marcus.vance@enterprise.io", "2023-06-01"),
        ("Elena Rostova", "Product", "VP of Product", 195000.0, "elena.rostova@enterprise.io", "2022-03-10"),
        ("David Miller", "Finance", "Head of FP&A", 160000.0, "david.miller@enterprise.io", "2022-11-20"),
        ("Sophia Patel", "Engineering", "MLOps Infrastructure Lead", 170000.0, "sophia.patel@enterprise.io", "2023-09-01"),
        ("James Rodriguez", "Marketing", "Growth Marketing Director", 135000.0, "james.rodriguez@enterprise.io", "2024-02-15")
    ]
    cursor.executemany("""
        INSERT INTO employees (name, department, role, salary, email, hire_date)
        VALUES (?, ?, ?, ?, ?, ?);
    """, employees_data)

    # 2. Products Table
    cursor.execute("""
        CREATE TABLE products (
            sku TEXT PRIMARY KEY,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            stock_quantity INTEGER NOT NULL
        );
    """)

    products_data = [
        ("AI-ACCEL-01", "Edge Tensor Accelerator", "Hardware", 499.00, 150),
        ("AI-ROUTER-99", "Neural Gateway Router", "Networking", 899.00, 45),
        ("SRV-BLADE-V4", "Enterprise Blade Compute Node", "Servers", 3499.00, 20),
        ("SFT-AGENT-ENT", "Agentic Orchestrator License (Annual)", "Software", 12000.00, 9999),
        ("IOT-SENSOR-PRO", "Telemetry Sensor Hub", "IoT", 149.50, 420)
    ]
    cursor.executemany("""
        INSERT INTO products (sku, product_name, category, price, stock_quantity)
        VALUES (?, ?, ?, ?, ?);
    """, products_data)

    # 3. Orders Table
    cursor.execute("""
        CREATE TABLE orders (
            order_id TEXT PRIMARY KEY,
            customer_name TEXT NOT NULL,
            product_sku TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            total_price REAL NOT NULL,
            order_date TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (product_sku) REFERENCES products(sku)
        );
    """)

    orders_data = [
        ("ORD-2026-101", "Apex Logistics", "AI-ACCEL-01", 10, 4990.00, "2026-10-01", "DELIVERED"),
        ("ORD-2026-102", "Nova Healthtech", "SRV-BLADE-V4", 2, 6998.00, "2026-10-02", "SHIPPED"),
        ("ORD-2026-103", "Finovate Global", "SFT-AGENT-ENT", 1, 12000.00, "2026-10-03", "DELIVERED"),
        ("ORD-2026-104", "Quantum Robotics", "AI-ROUTER-99", 5, 4495.00, "2026-10-04", "PROCESSING"),
        ("ORD-2026-105", "CyberMesh Corp", "IOT-SENSOR-PRO", 50, 7475.00, "2026-10-05", "PENDING_APPROVAL")
    ]
    cursor.executemany("""
        INSERT INTO orders (order_id, customer_name, product_sku, quantity, total_price, order_date, status)
        VALUES (?, ?, ?, ?, ?, ?, ?);
    """, orders_data)

    conn.commit()
    conn.close()
    return DB_FILE


if __name__ == "__main__":
    db_path = init_database()
    print(f"[+] Enterprise database successfully created and seeded at: {db_path}")
