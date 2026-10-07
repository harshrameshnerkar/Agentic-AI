"""
database_setup.py
=================
Seeds and initializes a realistic enterprise SQLite database (enterprise.db)
for testing database query tools.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "enterprise.db"


def init_database(db_path: Path = DB_PATH) -> Path:
    """Initializes schema and seeds realistic records for enterprise operations."""
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Employees table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        role TEXT NOT NULL,
        salary INTEGER NOT NULL,
        email TEXT UNIQUE NOT NULL
    );
    """)

    employees_data = [
        ("Sarah Connor", "Engineering", "Principal Architect", 165000, "sarah.connor@enterprise.io"),
        ("Marcus Vance", "Engineering", "Senior DevOps Engineer", 135000, "marcus.vance@enterprise.io"),
        ("Elena Rostova", "Data Science", "Lead AI Researcher", 155000, "elena.rostova@enterprise.io"),
        ("David Chen", "Product", "Director of Product", 170000, "david.chen@enterprise.io"),
        ("Priya Sharma", "Finance", "Senior Financial Analyst", 115000, "priya.sharma@enterprise.io"),
        ("James Wilson", "Security", "CISO", 195000, "james.wilson@enterprise.io"),
        ("Aisha Patel", "Customer Success", "Head of Support", 105000, "aisha.patel@enterprise.io"),
    ]
    cursor.executemany(
        "INSERT INTO employees (name, department, role, salary, email) VALUES (?, ?, ?, ?, ?)",
        employees_data,
    )

    # 2. Orders table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY,
        customer_name TEXT NOT NULL,
        product TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        total_amount REAL NOT NULL,
        order_date TEXT NOT NULL,
        status TEXT NOT NULL
    );
    """)

    orders_data = [
        ("ORD-1001", "Acme Corp", "Enterprise AI License (Annual)", 1, 48000.00, "2026-09-15", "Completed"),
        ("ORD-1002", "Globex Inc", "Vector Database Cloud Cluster", 4, 12800.00, "2026-09-22", "Completed"),
        ("ORD-1003", "Soylent Tech", "Fine-Tuning Compute Nodes", 8, 34500.00, "2026-10-01", "Processing"),
        ("ORD-1004", "Initech LLC", "Enterprise Support SLA (Tier 1)", 1, 9500.00, "2026-10-03", "Pending Approval"),
        ("ORD-1005", "Massive Dynamic", "On-Premises CrossEncoder Model", 2, 26000.00, "2026-10-04", "Completed"),
    ]
    cursor.executemany(
        "INSERT INTO orders (order_id, customer_name, product, quantity, total_amount, order_date, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        orders_data,
    )

    # 3. Inventory table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        sku TEXT PRIMARY KEY,
        product_name TEXT NOT NULL,
        stock_level INTEGER NOT NULL,
        reorder_threshold INTEGER NOT NULL,
        unit_price REAL NOT NULL
    );
    """)

    inventory_data = [
        ("SKU-GPU-H100", "NVIDIA H100 80GB PCIe", 14, 5, 29999.00),
        ("SKU-GPU-A100", "NVIDIA A100 80GB SXM4", 28, 10, 14500.00),
        ("SKU-SRV-2U", "2U Dual-AMD EPYC Compute Server", 42, 15, 6800.00),
        ("SKU-SW-NVLINK", "NVSwitch 32-Port High Speed Interconnect", 6, 8, 18500.00),
    ]
    cursor.executemany(
        "INSERT INTO inventory (sku, product_name, stock_level, reorder_threshold, unit_price) VALUES (?, ?, ?, ?, ?)",
        inventory_data,
    )

    conn.commit()
    conn.close()
    return db_path


if __name__ == "__main__":
    path = init_database()
    print(f"Database successfully initialized at: {path}")
