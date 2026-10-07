"""
database_setup.py
=================
Seeds the enterprise SQLite database for Day 4 - Session 3.
Creates 'employees', 'departments', and 'payroll_audit' tables.
"""

import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).parent / "enterprise.db"


def init_database():
    if DB_FILE.exists():
        DB_FILE.unlink()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 1. Employees table
    cursor.execute("""
    CREATE TABLE employees (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        role TEXT NOT NULL,
        salary REAL NOT NULL,
        email TEXT NOT NULL
    );
    """)

    employees = [
        (101, "Marcus Vance", "Engineering", "Senior DevOps Engineer", 135000.0, "marcus.vance@enterprise.io"),
        (102, "Sarah Connor", "Engineering", "Principal Systems Architect", 165000.0, "sarah.connor@enterprise.io"),
        (103, "Elena Rostova", "Data Science", "Senior Data Scientist", 155000.0, "elena.rostova@enterprise.io"),
        (104, "David Chen", "Product", "Senior Product Manager", 170000.0, "david.chen@enterprise.io"),
        (105, "James Wilson", "Security", "Senior Security Engineer", 195000.0, "james.wilson@enterprise.io"),
        (106, "Maya Patel", "Engineering", "Software Engineer II", 110000.0, "maya.patel@enterprise.io"),
    ]
    cursor.executemany("INSERT INTO employees VALUES (?, ?, ?, ?, ?, ?);", employees)

    # 2. Departments table
    cursor.execute("""
    CREATE TABLE departments (
        dept_name TEXT PRIMARY KEY,
        head_of_department TEXT NOT NULL,
        headcount INTEGER NOT NULL,
        quarterly_budget REAL NOT NULL
    );
    """)

    departments = [
        ("Engineering", "Sarah Connor", 42, 1250000.0),
        ("Data Science", "Dr. Aris Thorne", 18, 650000.0),
        ("Product", "David Chen", 12, 420000.0),
        ("Security", "James Wilson", 8, 380000.0),
    ]
    cursor.executemany("INSERT INTO departments VALUES (?, ?, ?, ?);", departments)

    # 3. Payroll audit table
    cursor.execute("""
    CREATE TABLE payroll_audit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_name TEXT NOT NULL,
        bonus_amount REAL NOT NULL,
        status TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()
    print(f"Database initialized successfully at: {DB_FILE}")


if __name__ == "__main__":
    init_database()
