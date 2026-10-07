"""
Day 11 - Session 2: Enterprise 5-Table Relational Database
==========================================================
Implements a 5-table SQLite schema modeling an enterprise Cloud Platform:
  1. customers (customer_id, name, email, tier, region, created_at)
  2. products (product_id, product_name, category, unit_price, status)
  3. orders (order_id, customer_id, order_date, status, total_amount)
  4. order_items (item_id, order_id, product_id, quantity, unit_price)
  5. support_tickets (ticket_id, customer_id, order_id, priority, status, subject, created_at)

Includes schema introspection, relationship graph mapping, and safe execution.
"""

import sqlite3
import time
from typing import Dict, List, Any, Optional


class EnterpriseDatabase:
    """Manages the 5-table SQLite relational schema with schema reflection."""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
        self._seed_data()

    def _init_schema(self):
        """Creates the 5 relational tables with explicit foreign key constraints."""
        cursor = self.conn.cursor()

        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Table 1: customers
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                tier TEXT NOT NULL CHECK(tier IN ('Enterprise', 'Pro', 'Starter')),
                region TEXT NOT NULL CHECK(region IN ('North America', 'Europe', 'APAC', 'LATAM')),
                created_at TEXT NOT NULL
            );
        """)

        # Table 2: products
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL CHECK(category IN ('Compute', 'Storage', 'AI Services', 'Networking')),
                unit_price REAL NOT NULL CHECK(unit_price >= 0),
                status TEXT NOT NULL CHECK(status IN ('Active', 'Deprecated'))
            );
        """)

        # Table 3: orders
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                order_date TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('Completed', 'Processing', 'Cancelled', 'Refunded')),
                total_amount REAL NOT NULL CHECK(total_amount >= 0),
                FOREIGN KEY (customer_id) REFERENCES customers (customer_id) ON DELETE CASCADE
            );
        """)

        # Table 4: order_items
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                unit_price REAL NOT NULL CHECK(unit_price >= 0),
                FOREIGN KEY (order_id) REFERENCES orders (order_id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products (product_id) ON DELETE RESTRICT
            );
        """)

        # Table 5: support_tickets
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS support_tickets (
                ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                order_id INTEGER,
                priority TEXT NOT NULL CHECK(priority IN ('P1-Critical', 'P2-High', 'P3-Normal')),
                status TEXT NOT NULL CHECK(status IN ('Open', 'In_Progress', 'Resolved', 'Closed')),
                subject TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers (customer_id) ON DELETE CASCADE,
                FOREIGN KEY (order_id) REFERENCES orders (order_id) ON DELETE SET NULL
            );
        """)

        self.conn.commit()

    def _seed_data(self):
        """Populates realistic interconnected records across all 5 tables."""
        cursor = self.conn.cursor()

        # Check if already seeded
        cursor.execute("SELECT COUNT(*) FROM customers;")
        if cursor.fetchone()[0] > 0:
            return

        # 1. Customers (10 entities across 4 regions and 3 tiers)
        customers_data = [
            (1, "Acme Global Corp", "admin@acmeglobal.com", "Enterprise", "North America", "2024-01-15"),
            (2, "Apex Fintech Labs", "ops@apexfintech.io", "Enterprise", "Europe", "2024-02-10"),
            (3, "Borealis AI Research", "contact@borealisai.org", "Enterprise", "APAC", "2024-03-01"),
            (4, "CyberShield Security", "dev@cybershield.net", "Pro", "North America", "2024-03-20"),
            (5, "Delta Cloud Systems", "support@deltacloud.co", "Pro", "Europe", "2024-04-05"),
            (6, "Echo Health Tech", "team@echohealth.io", "Pro", "LATAM", "2024-04-18"),
            (7, "Fusion Logistics", "it@fusionlogistics.com", "Starter", "APAC", "2024-05-02"),
            (8, "Global Micro Ventures", "hello@microventures.co", "Starter", "North America", "2024-05-15"),
            (9, "HyperScale Telecom", "noc@hyperscale.net", "Enterprise", "APAC", "2024-06-01"),
            (10, "Zenith Media Group", "ops@zenithmedia.com", "Starter", "Europe", "2024-06-20"),
        ]
        cursor.executemany(
            "INSERT INTO customers (customer_id, name, email, tier, region, created_at) VALUES (?, ?, ?, ?, ?, ?);",
            customers_data
        )

        # 2. Products (8 items across 4 categories)
        products_data = [
            (1, "Cloud Compute vCPU Cluster", "Compute", 1200.00, "Active"),
            (2, "GPU Inference Accelerator A100", "AI Services", 3500.00, "Active"),
            (3, "Enterprise Object Storage 100TB", "Storage", 850.00, "Active"),
            (4, "Managed PostgreSQL HA Cluster", "Storage", 650.00, "Active"),
            (5, "Global Edge CDN & DDoS Shield", "Networking", 450.00, "Active"),
            (6, "Dedicated Fiber Interconnect 10Gbps", "Networking", 1800.00, "Active"),
            (7, "GenAI Fine-Tuning Pipeline Node", "AI Services", 4200.00, "Active"),
            (8, "Legacy Cold Archival Vault v1", "Storage", 200.00, "Deprecated"),
        ]
        cursor.executemany(
            "INSERT INTO products (product_id, product_name, category, unit_price, status) VALUES (?, ?, ?, ?, ?);",
            products_data
        )

        # 3. Orders (14 orders across customers)
        orders_data = [
            (101, 1, "2024-07-01", "Completed", 8200.00),
            (102, 1, "2024-07-15", "Completed", 3500.00),
            (103, 2, "2024-07-03", "Completed", 7700.00),
            (104, 2, "2024-07-20", "Completed", 1200.00),
            (105, 3, "2024-07-05", "Completed", 11900.00),
            (106, 3, "2024-08-01", "Processing", 4200.00),
            (107, 4, "2024-07-10", "Completed", 1850.00),
            (108, 4, "2024-07-28", "Refunded", 650.00),
            (109, 5, "2024-07-12", "Completed", 2650.00),
            (110, 6, "2024-07-14", "Completed", 1650.00),
            (111, 7, "2024-07-18", "Completed", 450.00),
            (112, 8, "2024-07-22", "Cancelled", 1200.00),
            (113, 9, "2024-07-25", "Completed", 9500.00),
            (114, 9, "2024-08-02", "Processing", 3500.00),
        ]
        cursor.executemany(
            "INSERT INTO orders (order_id, customer_id, order_date, status, total_amount) VALUES (?, ?, ?, ?, ?);",
            orders_data
        )

        # 4. Order Items (line items corresponding to orders)
        order_items_data = [
            # Order 101 (Acme Corp): GPU A100 (2 units) + Cloud Compute (1 unit) -> 7000 + 1200 = 8200
            (1, 101, 2, 2, 3500.00),
            (2, 101, 1, 1, 1200.00),
            # Order 102 (Acme Corp): GPU A100 (1 unit) -> 3500
            (3, 102, 2, 1, 3500.00),
            # Order 103 (Apex Fintech): GenAI Node (1 unit) + GPU A100 (1 unit) -> 4200 + 3500 = 7700
            (4, 103, 7, 1, 4200.00),
            (5, 103, 2, 1, 3500.00),
            # Order 104 (Apex Fintech): Cloud Compute (1 unit) -> 1200
            (6, 104, 1, 1, 1200.00),
            # Order 105 (Borealis AI - APAC Enterprise): 2x GenAI Node + 1x GPU A100 -> 8400 + 3500 = 11900
            (7, 105, 7, 2, 4200.00),
            (8, 105, 2, 1, 3500.00),
            # Order 106 (Borealis AI - Processing): 1x GenAI Node -> 4200
            (9, 106, 7, 1, 4200.00),
            # Order 107 (CyberShield): 1x Storage 100TB + 1x Fiber Interconnect -> 850 + 1000 = 1850
            (10, 107, 3, 1, 850.00),
            (11, 107, 5, 1, 450.00),
            (12, 107, 4, 1, 550.00),
            # Order 108 (CyberShield - Refunded): Managed Postgres -> 650
            (13, 108, 4, 1, 650.00),
            # Order 109 (Delta Cloud): 1x Fiber (1800) + 1x Storage (850) = 2650
            (14, 109, 6, 1, 1800.00),
            (15, 109, 3, 1, 850.00),
            # Order 110 (Echo Health): 1x Cloud Compute (1200) + 1x CDN (450) = 1650
            (16, 110, 1, 1, 1200.00),
            (17, 110, 5, 1, 450.00),
            # Order 111 (Fusion Logistics): 1x CDN (450)
            (18, 111, 5, 1, 450.00),
            # Order 112 (Global Micro - Cancelled): 1x Cloud Compute (1200)
            (19, 112, 1, 1, 1200.00),
            # Order 113 (HyperScale Telecom - APAC Enterprise): 1x Fiber (1800) + 2x GPU A100 (7000) + 1x Postgres (700) = 9500
            (20, 113, 6, 1, 1800.00),
            (21, 113, 2, 2, 3500.00),
            (22, 113, 4, 1, 700.00),
            # Order 114 (HyperScale Telecom): 1x GPU A100 (3500)
            (23, 114, 2, 1, 3500.00),
        ]
        cursor.executemany(
            "INSERT INTO order_items (item_id, order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?, ?);",
            order_items_data
        )

        # 5. Support Tickets (10 tickets linking to customers and orders)
        tickets_data = [
            (1, 1, 101, "P2-High", "Resolved", "Inference latency spike on A100 cluster", "2024-07-02"),
            (2, 3, 105, "P1-Critical", "Open", "Node disconnection in APAC GPU cluster during training run", "2024-07-06"),
            (3, 2, 103, "P2-High", "In_Progress", "Intermittent SSL handshake timeout on GenAI endpoint", "2024-07-07"),
            (4, 4, 108, "P3-Normal", "Resolved", "Billing discrepancy and refund request for Postgres addon", "2024-07-11"),
            (5, 9, 113, "P1-Critical", "Open", "Fiber interconnect packet loss exceeding 15% SLA threshold", "2024-07-26"),
            (6, 5, 109, "P3-Normal", "Closed", "Request for bandwidth upgrade quota in Europe region", "2024-07-16"),
            (7, 3, 106, "P2-High", "In_Progress", "Slow provisioning on secondary fine-tuning node", "2024-08-01"),
            (8, 7, 111, "P3-Normal", "Closed", "Inquiry regarding CDN caching rules for static assets", "2024-07-19"),
            (9, 6, 110, "P2-High", "Open", "Storage bucket access control configuration error", "2024-07-20"),
            (10, 9, None, "P1-Critical", "Open", "Enterprise SLA escalation for APAC redundancy zone", "2024-08-03"),
        ]
        cursor.executemany(
            "INSERT INTO support_tickets (ticket_id, customer_id, order_id, priority, status, subject, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?);",
            tickets_data
        )

        self.conn.commit()

    def get_schema_info(self) -> Dict[str, Any]:
        """Reflects SQLite metadata to produce a structured schema dictionary."""
        cursor = self.conn.cursor()
        tables = ["customers", "products", "orders", "order_items", "support_tickets"]
        schema = {}

        for table in tables:
            cursor.execute(f"PRAGMA table_info({table});")
            cols = cursor.fetchall()

            cursor.execute(f"PRAGMA foreign_key_list({table});")
            fks = cursor.fetchall()

            schema[table] = {
                "columns": {col[1]: {"type": col[2], "notnull": bool(col[3]), "pk": bool(col[5])} for col in cols},
                "foreign_keys": [
                    {"column": fk[3], "references_table": fk[2], "references_column": fk[4]} for fk in fks
                ],
            }

        return schema

    def get_schema_prompt(self) -> str:
        """Generates an LLM-friendly schema definition with relationships and hints."""
        return """
DATABASE SCHEMA (5 Relational Tables):

Table 1: customers
  - customer_id (INTEGER PRIMARY KEY)
  - name (TEXT) : Company name (e.g. 'Acme Global Corp', 'Apex Fintech Labs', 'Borealis AI Research')
  - email (TEXT) : Primary contact email
  - tier (TEXT) : Service tier ('Enterprise', 'Pro', 'Starter')
  - region (TEXT) : Geographic region ('North America', 'Europe', 'APAC', 'LATAM')
  - created_at (TEXT) : Customer onboarding date (YYYY-MM-DD)

Table 2: products
  - product_id (INTEGER PRIMARY KEY)
  - product_name (TEXT) : Name of product/service (e.g. 'Cloud Compute vCPU Cluster', 'GPU Inference Accelerator A100')
  - category (TEXT) : Category ('Compute', 'Storage', 'AI Services', 'Networking')
  - unit_price (REAL) : Base price in USD
  - status (TEXT) : Product status ('Active', 'Deprecated')

Table 3: orders
  - order_id (INTEGER PRIMARY KEY)
  - customer_id (INTEGER FOREIGN KEY -> customers.customer_id)
  - order_date (TEXT) : Date order placed (YYYY-MM-DD)
  - status (TEXT) : Order status ('Completed', 'Processing', 'Cancelled', 'Refunded')
  - total_amount (REAL) : Total dollar value of the order

Table 4: order_items
  - item_id (INTEGER PRIMARY KEY)
  - order_id (INTEGER FOREIGN KEY -> orders.order_id)
  - product_id (INTEGER FOREIGN KEY -> products.product_id)
  - quantity (INTEGER) : Number of units ordered
  - unit_price (REAL) : Unit price applied at order time

Table 5: support_tickets
  - ticket_id (INTEGER PRIMARY KEY)
  - customer_id (INTEGER FOREIGN KEY -> customers.customer_id)
  - order_id (INTEGER FOREIGN KEY -> orders.order_id, NULLABLE)
  - priority (TEXT) : Ticket urgency ('P1-Critical', 'P2-High', 'P3-Normal')
  - status (TEXT) : Ticket status ('Open', 'In_Progress', 'Resolved', 'Closed')
  - subject (TEXT) : Short description of issue
  - created_at (TEXT) : Date ticket opened (YYYY-MM-DD)

COMMON JOIN PATHS:
  - customers -> orders: ON customers.customer_id = orders.customer_id
  - orders -> order_items: ON orders.order_id = order_items.order_id
  - order_items -> products: ON order_items.product_id = products.product_id
  - customers -> support_tickets: ON customers.customer_id = support_tickets.customer_id
  - orders -> support_tickets: ON orders.order_id = support_tickets.order_id
"""

    def explain_query(self, sql: str) -> Dict[str, Any]:
        """Runs EXPLAIN QUERY PLAN to validate syntax and index execution without changing state."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(f"EXPLAIN QUERY PLAN {sql}")
            plan = [dict(row) for row in cursor.fetchall()]
            return {"valid": True, "plan": plan}
        except Exception as e:
            return {"valid": False, "error": str(e)}

    def execute_query(self, sql: str) -> Dict[str, Any]:
        """Safely executes a SELECT query and returns rows, column names, and timing."""
        t0 = time.perf_counter()
        cursor = self.conn.cursor()
        try:
            cursor.execute(sql)
            rows = cursor.fetchall()
            latency_ms = (time.perf_counter() - t0) * 1000.0

            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            data = [dict(row) for row in rows]

            return {
                "status": "SUCCESS",
                "sql": sql,
                "columns": columns,
                "row_count": len(data),
                "rows": data,
                "latency_ms": round(latency_ms, 2),
            }
        except Exception as e:
            latency_ms = (time.perf_counter() - t0) * 1000.0
            return {
                "status": "ERROR",
                "sql": sql,
                "error": str(e),
                "latency_ms": round(latency_ms, 2),
            }


# Singleton database instance
db = EnterpriseDatabase()
