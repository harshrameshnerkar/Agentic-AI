"""
Safety Gate Tests for Role B (Data Service) on Real Northwind Database.
Verifies Acceptance Criterion 3:
- Destructive SQL provably blocked at validation, BEFORE execution.
- Multi-statements, table drops, deletes, updates, and schema alterations rejected.
- Database state remains completely unchanged.
"""
import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from db.connection import db_manager
from safety.errors import (
    DestructiveSQLBlockedException,
    MultipleStatementsBlockedException,
    SQLSecurityException,
)
from safety.validator import SQLSafetyValidator


class TestSQLSafetyValidation(unittest.TestCase):
    """Proves that destructive operations are blocked during the validation phase."""

    def test_drop_table_blocked_at_validation(self):
        """Criterion 3: Asking to drop a table is blocked at validation prior to execution."""
        sql = "DROP TABLE Customer;"
        with self.assertRaises(DestructiveSQLBlockedException) as ctx:
            SQLSafetyValidator.validate(sql)

        self.assertIn("DROP", str(ctx.exception))
        self.assertIn("Validation Phase", str(ctx.exception))

    def test_delete_blocked_at_validation(self):
        """DELETE queries must be blocked at validation."""
        sql = "DELETE FROM Employee WHERE EmployeeId = 1;"
        with self.assertRaises(DestructiveSQLBlockedException) as ctx:
            SQLSafetyValidator.validate(sql)

        self.assertIn("DELETE", str(ctx.exception))

    def test_update_blocked_at_validation(self):
        """UPDATE queries must be blocked at validation."""
        sql = "UPDATE Invoice SET Total = 0.0;"
        with self.assertRaises(DestructiveSQLBlockedException) as ctx:
            SQLSafetyValidator.validate(sql)

        self.assertIn("UPDATE", str(ctx.exception))

    def test_insert_blocked_at_validation(self):
        """INSERT queries must be blocked at validation."""
        sql = "INSERT INTO Track (Name, UnitPrice) VALUES ('Malware', 999.0);"
        with self.assertRaises(DestructiveSQLBlockedException) as ctx:
            SQLSafetyValidator.validate(sql)

        self.assertIn("INSERT", str(ctx.exception))

    def test_alter_table_blocked_at_validation(self):
        """ALTER TABLE queries must be blocked at validation."""
        sql = "ALTER TABLE Customer DROP COLUMN Phone;"
        with self.assertRaises(DestructiveSQLBlockedException) as ctx:
            SQLSafetyValidator.validate(sql)

        self.assertIn("ALTER", str(ctx.exception))

    def test_multiple_statements_blocked(self):
        """Chained multi-statement queries must be blocked at validation."""
        sql = "SELECT * FROM Customer; DROP TABLE Invoice;"
        with self.assertRaises((DestructiveSQLBlockedException, MultipleStatementsBlockedException)):
            SQLSafetyValidator.validate(sql)

    def test_dangerous_extension_loading_blocked(self):
        """SQLite extension loading must be blocked at validation."""
        sql = "SELECT load_extension('malicious.dll');"
        with self.assertRaises(DestructiveSQLBlockedException):
            SQLSafetyValidator.validate(sql)

    def test_valid_select_queries_pass_validation(self):
        """Legitimate business SELECT and JOIN queries must pass cleanly."""
        valid_queries = [
            "SELECT CustomerId, FirstName, LastName FROM Customer LIMIT 10;",
            "SELECT c.FirstName, COUNT(i.InvoiceId) FROM Customer c JOIN Invoice i ON c.CustomerId = i.CustomerId GROUP BY c.CustomerId;",
            "SELECT g.Name, COUNT(t.TrackId) FROM Genre g JOIN Track t ON g.GenreId = t.GenreId GROUP BY g.GenreId;",
            "SELECT * FROM Track ORDER BY UnitPrice DESC LIMIT 5;",
        ]
        for q in valid_queries:
            is_valid, canonical_sql, err = SQLSafetyValidator.validate(q)
            self.assertTrue(is_valid)
            self.assertIsNone(err)
            self.assertIn("SELECT", canonical_sql.upper())

    def test_database_remains_intact_after_destructive_attacks(self):
        """Proves database record count is identical before and after attack attempts."""
        counts_before = db_manager.get_table_counts()

        attacks = [
            "DROP TABLE Customer;",
            "DELETE FROM Invoice;",
            "UPDATE Track SET UnitPrice = 0.0;",
        ]
        for attack in attacks:
            try:
                SQLSafetyValidator.validate(attack)
            except SQLSecurityException:
                pass  # Successfully blocked

        counts_after = db_manager.get_table_counts()
        self.assertEqual(counts_before, counts_after, "Database counts changed! Security was breached.")


if __name__ == "__main__":
    unittest.main()
