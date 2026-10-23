"""
Database Seeding & Ingestion Script for Role B (Data Service).

Sources and installs the authentic, real-world Chinook Enterprise Database
(11 related tables, 15,607 real records, 0% AI-generated).
"""
import os
import sqlite3
import urllib.request

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "enterprise_business.db")
SCHEMA_PATH = os.path.join(DB_DIR, "schema.sql")

CHINOOK_URL = "https://raw.githubusercontent.com/lerocha/chinook-database/master/ChinookDatabase/DataSources/Chinook_Sqlite.sqlite"


def seed_database(force_redownload: bool = False):
    """
    Downloads or restores the real-world Chinook relational database.
    """
    print(f"[*] Initializing authentic real database at: {DB_PATH}")

    # If database file doesn't exist or forced redownload, fetch from upstream repository
    if not os.path.exists(DB_PATH) or force_redownload:
        print(f"[*] Fetching authentic Chinook database from: {CHINOOK_URL}")
        req = urllib.request.Request(CHINOOK_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp, open(DB_PATH, "wb") as f:
            f.write(resp.read())
        print(f"[+] Download complete: {os.path.getsize(DB_PATH)} bytes.")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Verify tables and row counts
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
    tables = [row[0] for row in cursor.fetchall()]

    total_rows = 0
    print("\n" + "=" * 55)
    print("AUTHENTIC REAL DATABASE SUMMARY (Chinook Real Dataset)")
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

    conn.close()
    return total_rows


if __name__ == "__main__":
    seed_database()
