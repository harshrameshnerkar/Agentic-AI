"""
Relational SQL Database Engine for Day 11 Session 1.
Provides structured relational data storage, schema inspection, and safe query execution.
Tables:
- orders: Customer transactions, statuses, amounts, dates.
- inventory: SKUs, stock levels, unit prices, warehouse locations.
- employees: Departments, salaries, titles, hire dates.
"""

import sqlite3
from typing import Dict, Any, List, Optional


class EnterpriseSQLDatabase:
    """In-memory SQLite database preloaded with enterprise relational records."""

    def __init__(self, db_path: str = ":memory:"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema_and_seed()

    def _init_schema_and_seed(self) -> None:
        cursor = self.conn.cursor()

        # 1. Orders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY,
                customer_name TEXT NOT NULL,
                product_name TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                status TEXT NOT NULL,
                order_date TEXT NOT NULL
            )
        """)

        # 2. Inventory table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                sku TEXT PRIMARY KEY,
                product_name TEXT NOT NULL,
                category TEXT NOT NULL,
                stock_quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                warehouse_location TEXT NOT NULL
            )
        """)

        # 3. Employees table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                emp_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                title TEXT NOT NULL,
                salary REAL NOT NULL,
                hire_date TEXT NOT NULL
            )
        """)

        # Seed data
        orders_data = [
            (101, "Acme Corp", "Cloud Server Pro", "Compute", 4200.0, "completed", "2026-09-01"),
            (102, "Beta Retail", "Kubernetes Ingress Gateway", "Networking", 1850.0, "completed", "2026-09-03"),
            (103, "Gamma Logistics", "Redis Cluster Cache", "Storage", 950.0, "pending", "2026-09-15"),
            (104, "Delta Health", "Postgres Dedicated DB", "Database", 3200.0, "completed", "2026-09-18"),
            (105, "Epsilon Media", "CDN Edge Delivery", "Networking", 650.0, "refunded", "2026-09-20"),
            (106, "Zeta AI", "GPU Inference Node A100", "Compute", 8500.0, "completed", "2026-09-22"),
            (107, "Eta Fintech", "Postgres Dedicated DB", "Database", 3200.0, "pending", "2026-09-25"),
            (108, "Theta Gaming", "Cloud Server Pro", "Compute", 4200.0, "cancelled", "2026-09-28"),
            (109, "Iota Sec", "WAF Security Shield", "Security", 1400.0, "completed", "2026-10-01"),
            (110, "Kappa Stream", "GPU Inference Node A100", "Compute", 8500.0, "pending", "2026-10-03"),
        ]
        cursor.executemany(
            "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?)", orders_data
        )

        inventory_data = [
            ("SKU-SRV-01", "Cloud Server Pro", "Compute", 45, 4200.0, "us-east-dc1"),
            ("SKU-GPU-01", "GPU Inference Node A100", "Compute", 8, 8500.0, "us-central-dc2"),
            ("SKU-NET-01", "Kubernetes Ingress Gateway", "Networking", 120, 1850.0, "us-east-dc1"),
            ("SKU-NET-02", "CDN Edge Delivery", "Networking", 500, 650.0, "eu-west-dc1"),
            ("SKU-DB-01", "Postgres Dedicated DB", "Database", 25, 3200.0, "us-east-dc1"),
            ("SKU-DB-02", "Redis Cluster Cache", "Storage", 80, 950.0, "us-west-dc3"),
            ("SKU-SEC-01", "WAF Security Shield", "Security", 200, 1400.0, "global-edge"),
        ]
        cursor.executemany(
            "INSERT INTO inventory VALUES (?, ?, ?, ?, ?, ?)", inventory_data
        )

        employees_data = [
            (1, "Alice Walker", "Engineering", "Principal SRE", 185000.0, "2022-03-15"),
            (2, "Bob Vance", "Sales", "Enterprise AE", 140000.0, "2021-06-01"),
            (3, "Charlie Davis", "Engineering", "DevOps Engineer", 135000.0, "2023-01-10"),
            (4, "Dana Scully", "Security", "Lead Security Analyst", 165000.0, "2020-11-20"),
            (5, "Evan Wright", "Finance", "Senior Financial Analyst", 125000.0, "2022-08-05"),
            (6, "Fiona Gallagher", "Engineering", "Cloud Architect", 195000.0, "2019-04-12"),
            (7, "George Clark", "Sales", "VP of Enterprise Sales", 220000.0, "2020-02-18"),
        ]
        cursor.executemany(
            "INSERT INTO employees VALUES (?, ?, ?, ?, ?, ?)", employees_data
        )

        self.conn.commit()

    def get_schema_summary(self) -> str:
        """Returns structured DDL schema description for LLM prompting."""
        return """
TABLE orders (
  order_id INTEGER PRIMARY KEY,
  customer_name TEXT,
  product_name TEXT,
  category TEXT,
  amount REAL,
  status TEXT ('completed', 'pending', 'cancelled', 'refunded'),
  order_date TEXT (YYYY-MM-DD)
);

TABLE inventory (
  sku TEXT PRIMARY KEY,
  product_name TEXT,
  category TEXT,
  stock_quantity INTEGER,
  unit_price REAL,
  warehouse_location TEXT
);

TABLE employees (
  emp_id INTEGER PRIMARY KEY,
  name TEXT,
  department TEXT,
  title TEXT,
  salary REAL,
  hire_date TEXT (YYYY-MM-DD)
);
""".strip()

    def execute_query(self, sql_query: str) -> Dict[str, Any]:
        """Executes a SQL query safely, rejecting destructive DDL/DML statements."""
        clean_sql = sql_query.strip()
        prohibited = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]
        if any(clean_sql.upper().startswith(p) for p in prohibited):
            return {"status": "ERROR", "error": "Destructive SQL operations are prohibited."}

        try:
            cursor = self.conn.cursor()
            cursor.execute(clean_sql)
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description] if cursor.description else []
            data = [dict(zip(columns, row)) for row in rows]
            return {
                "status": "SUCCESS",
                "sql": clean_sql,
                "row_count": len(data),
                "columns": columns,
                "rows": data,
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "sql": clean_sql,
                "error": str(e),
            }


# Singleton database instance
db = EnterpriseSQLDatabase()
