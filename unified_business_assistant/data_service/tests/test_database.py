"""
Database Integrity and Seeding Tests for Role B (Data Service).
Verifies:
- 5+ interconnected tables exist.
- Over 1,000 total rows seeded.
- Strict foreign key constraints valid.
- Read-only connection blocks write operations at the database engine level.
"""
import os
import sqlite3
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from db.connection import db_manager


class TestDatabaseIntegrity(unittest.TestCase):
    """Verifies database row counts, relationships, and read-only enforcement."""

    def test_database_exists(self):
        """Database file must physically exist on disk."""
        self.assertTrue(os.path.exists(db_manager.db_path))

    def test_table_presence_and_row_counts(self):
        """Database must have >= 5 tables and >= 1000 total rows."""
        counts = db_manager.get_table_counts()
        expected_tables = {"departments", "employees", "customers", "products", "orders", "order_items"}
        for t in expected_tables:
            self.assertIn(t, counts, f"Table {t} missing from database.")
            self.assertGreater(counts[t], 0, f"Table {t} is empty.")

        total_rows = sum(counts.values())
        print(f"\n[TestDatabaseIntegrity] Total row count: {total_rows}")
        self.assertGreaterEqual(total_rows, 1000, "Database must contain at least 1,000 rows.")

    def test_foreign_key_integrity(self):
        """Foreign key integrity check must return zero violations."""
        conn = db_manager.get_readonly_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_key_check;")
            violations = cursor.fetchall()
            self.assertEqual(len(violations), 0, f"Foreign key violations found: {violations}")
        finally:
            conn.close()

    def test_readonly_connection_blocks_direct_writes(self):
        """Physical connection must reject any SQL INSERT, UPDATE, or DROP attempts."""
        conn = db_manager.get_readonly_connection()
        try:
            cursor = conn.cursor()
            with self.assertRaises(sqlite3.OperationalError):
                cursor.execute("INSERT INTO departments (department_name, code, budget, location) VALUES ('Test', 'TST', 100, 'Nowhere');")

            with self.assertRaises(sqlite3.OperationalError):
                cursor.execute("DROP TABLE customers;")
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
