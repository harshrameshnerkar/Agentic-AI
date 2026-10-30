"""
Database Seeding & Ingestion Script for Role B (Data Service).

Sources and installs the authentic, real-world Northwind Enterprise Database
(Categories, Customers, Employees, Orders, Order Details, Products, Shippers, Suppliers).
"""
import os
import sqlite3
import urllib.request

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "enterprise_business.db")
SCHEMA_PATH = os.path.join(DB_DIR, "schema.sql")

NORTHWIND_URL = "https://raw.githubusercontent.com/jpwhite3/northwind-SQLite3/main/dist/northwind.db"


def seed_database(force_redownload: bool = False):
    """
    Downloads or restores the real-world Northwind relational database and applies compatibility views.
    """
    print(f"[*] Initializing authentic Northwind database at: {DB_PATH}")

    # If database file doesn't exist or forced redownload, fetch from upstream repository
    if not os.path.exists(DB_PATH) or force_redownload:
        print(f"[*] Fetching authentic Northwind database from: {NORTHWIND_URL}")
        req = urllib.request.Request(NORTHWIND_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp, open(DB_PATH, "wb") as f:
            f.write(resp.read())
        print(f"[+] Download complete: {os.path.getsize(DB_PATH)} bytes.")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Apply compatibility views and columns
    # 1. OrderDetails view without spaces to support both 'OrderDetails' and '[Order Details]'
    cursor.execute(
        "CREATE VIEW IF NOT EXISTS OrderDetails AS "
        "SELECT OrderID, ProductID, UnitPrice, Quantity, Discount FROM [Order Details];"
    )

    # 2. Add Price column to Products (synced to UnitPrice) so queries using Price work seamlessly
    cursor.execute("PRAGMA table_info(Products);")
    prod_cols = [r[1] for r in cursor.fetchall()]
    if "Price" not in prod_cols:
        cursor.execute("ALTER TABLE Products ADD COLUMN Price NUMERIC;")
        cursor.execute("UPDATE Products SET Price = UnitPrice;")

    # 3. Add CustomerName column to Customers (synced to ContactName) so queries using CustomerName work
    cursor.execute("PRAGMA table_info(Customers);")
    cust_cols = [r[1] for r in cursor.fetchall()]
    if "CustomerName" not in cust_cols:
        cursor.execute("ALTER TABLE Customers ADD COLUMN CustomerName TEXT;")
        cursor.execute("UPDATE Customers SET CustomerName = ContactName;")

    # 4. Add ShipperName column to Shippers (synced to CompanyName)
    cursor.execute("PRAGMA table_info(Shippers);")
    ship_cols = [r[1] for r in cursor.fetchall()]
    if "ShipperName" not in ship_cols:
        cursor.execute("ALTER TABLE Shippers ADD COLUMN ShipperName TEXT;")
        cursor.execute("UPDATE Shippers SET ShipperName = CompanyName;")

    conn.commit()

    # Verify tables and row counts
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
    tables = [row[0] for row in cursor.fetchall()]

    total_rows = 0
    print("\n" + "=" * 55)
    print("AUTHENTIC REAL DATABASE SUMMARY (Northwind Dataset)")
    print("=" * 55)
    for t in tables:
        cursor.execute(f'SELECT COUNT(*) FROM "{t}";')
        cnt = cursor.fetchone()[0]
        total_rows += cnt
        print(f"  {t:<22}: {cnt:>6} rows")
    print("-" * 55)
    print(f"  TOTAL RECORDS (REAL)  : {total_rows:>6} rows")
    print("=" * 55)

    # Integrity verification
    cursor.execute("PRAGMA foreign_key_check;")
    fk_errors = cursor.fetchall()
    if fk_errors:
        print(f"[!] Warning: Foreign key check failed: {fk_errors}")
    else:
        print("[+] Foreign key constraint integrity: 100% OK.")

    # Export schema.sql
    with open(SCHEMA_PATH, "w", encoding="utf-8") as f:
        f.write("-- ==============================================================================\n")
        f.write("-- UNIFIED BUSINESS ASSISTANT - ROLE B: DATA SERVICE\n")
        f.write("-- Real World Enterprise Database Schema (Northwind Official Dataset)\n")
        f.write("-- ==============================================================================\n\n")
        cursor.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%';")
        for row in cursor.fetchall():
            f.write(row[0] + ";\n\n")
    print(f"[+] Exported schema to {SCHEMA_PATH}")

    conn.close()
    return total_rows


if __name__ == "__main__":
    seed_database(force_redownload=True)
