"""
Database Seeding Script for Role B (Data Service).

Creates and seeds the SQLite database (`enterprise_business.db`) with 6 interconnected
tables and over 1,900 realistic business records (well exceeding the 1,000 row requirement).
"""
import os
import random
import sqlite3
from datetime import datetime, timedelta

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "enterprise_business.db")
SCHEMA_PATH = os.path.join(DB_DIR, "schema.sql")

# Deterministic seed for reproducible testing
random.seed(42)

DEPARTMENTS = [
    ("Engineering", "ENG", 4500000.0, "San Francisco, CA", "2020-01-15"),
    ("Sales & Business Development", "SALES", 3200000.0, "New York, NY", "2020-01-15"),
    ("Customer Success & Support", "CS", 1800000.0, "Austin, TX", "2020-02-01"),
    ("Product Management", "PROD", 2200000.0, "San Francisco, CA", "2020-02-15"),
    ("Marketing & Growth", "MKTG", 1950000.0, "New York, NY", "2020-03-01"),
    ("Finance & Accounting", "FIN", 1400000.0, "Chicago, IL", "2020-01-15"),
    ("Human Resources & People", "HR", 1100000.0, "Austin, TX", "2020-01-15"),
    ("Legal & Compliance", "LEGAL", 950000.0, "Washington, DC", "2020-04-01"),
]

FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
    "Kenneth", "Dorothy", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa",
    "Timothy", "Deborah", "Ronald", "Stephanie", "Edward", "Rebecca", "Jason", "Sharon",
    "Jeffrey", "Laura", "Ryan", "Cynthia", "Jacob", "Kathleen", "Gary", "Amy",
    "Nicholas", "Shirley", "Eric", "Angela", "Jonathan", "Helen", "Stephen", "Anna",
    "Larry", "Brenda", "Justin", "Pamela", "Scott", "Nicole", "Brandon", "Emma"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill",
    "Flores", "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell",
    "Mitchell", "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz"
]

ROLES_BY_DEPT = {
    1: [("Principal Architect", 195000), ("Staff Software Engineer", 165000), ("Senior DevOps Engineer", 145000),
        ("Software Engineer II", 125000), ("Frontend Engineer", 115000), ("QA Lead", 110000), ("Data Engineer", 135000)],
    2: [("VP of Enterprise Sales", 220000), ("Enterprise Account Executive", 130000), ("Senior Sales Rep", 95000),
        ("Account Manager", 85000), ("Business Development Rep", 65000), ("Sales Engineer", 120000)],
    3: [("Director of Support", 140000), ("Senior CS Manager", 105000), ("CS Specialist", 75000),
        ("Technical Support Lead", 85000), ("Support Specialist", 60000)],
    4: [("VP of Product", 210000), ("Principal Product Manager", 175000), ("Senior PM", 145000),
        ("Product Designer", 115000), ("UX Researcher", 100000)],
    5: [("Chief Marketing Officer", 230000), ("Demand Gen Lead", 125000), ("Content Strategist", 90000),
        ("SEO Specialist", 80000), ("Brand Manager", 95000)],
    6: [("VP of Finance", 200000), ("Financial Controller", 140000), ("Senior Financial Analyst", 110000),
        ("Staff Accountant", 80000), ("Payroll Specialist", 70000)],
    7: [("Chief People Officer", 190000), ("Senior HR Business Partner", 120000), ("Technical Recruiter", 90000),
        ("People Ops Specialist", 70000)],
    8: [("General Counsel", 240000), ("Senior Corporate Counsel", 160000), ("Compliance Officer", 115000)],
}

INDUSTRIES = ["Technology", "Healthcare", "Finance", "Retail", "Manufacturing", "Education"]
REGIONS = [
    ("North America", "United States"),
    ("North America", "Canada"),
    ("Europe", "United Kingdom"),
    ("Europe", "Germany"),
    ("Europe", "France"),
    ("Asia-Pacific", "Singapore"),
    ("Asia-Pacific", "Japan"),
    ("Asia-Pacific", "Australia"),
    ("Latin America", "Brazil"),
    ("Latin America", "Mexico"),
]
TIERS = ["Enterprise", "Mid-Market", "Startup"]

PRODUCTS_DATA = [
    ("Nexus Enterprise ERP License", "Software Licenses", 12000.0, 3000.0, 500, "Active"),
    ("Nexus Core Team License", "Software Licenses", 4500.0, 1200.0, 800, "Active"),
    ("Nexus Solo Developer License", "Software Licenses", 1200.0, 350.0, 1500, "Active"),
    ("Nexus Analytics Suite Add-on", "Software Licenses", 3000.0, 800.0, 450, "Active"),
    ("Cloud Infrastructure Tier 1 (Small)", "Cloud Services", 800.0, 300.0, 9999, "Active"),
    ("Cloud Infrastructure Tier 2 (Medium)", "Cloud Services", 2400.0, 900.0, 9999, "Active"),
    ("Cloud Infrastructure Tier 3 (Enterprise)", "Cloud Services", 6500.0, 2200.0, 9999, "Active"),
    ("Dedicated Managed DB Cluster", "Cloud Services", 4200.0, 1600.0, 9999, "Active"),
    ("AI Inference GPU Acceleration Pool", "Cloud Services", 5800.0, 2400.0, 9999, "Active"),
    ("Edge Gateway Appliance v2", "Hardware", 3200.0, 1800.0, 140, "Active"),
    ("Enterprise Rack Server Unit S4", "Hardware", 8500.0, 5200.0, 65, "Active"),
    ("High-Throughput Cryptographic HSM", "Hardware", 14500.0, 9200.0, 30, "Active"),
    ("Smart IoT Sensor Hub (Pack of 10)", "Hardware", 1100.0, 620.0, 280, "Active"),
    ("Disaster Recovery Hot-Standby Box", "Hardware", 6200.0, 3800.0, 45, "Active"),
    ("Legacy Terminal Controller 2021", "Hardware", 1800.0, 1200.0, 0, "Discontinued"),
    ("Architecture & Migration Consulting", "Consulting Services", 15000.0, 6000.0, 200, "Active"),
    ("Security & SOC2 Readiness Audit", "Consulting Services", 18000.0, 7500.0, 150, "Active"),
    ("Performance Tuning 3-Day Sprint", "Consulting Services", 9000.0, 3800.0, 300, "Active"),
    ("Custom Data Pipeline Integration", "Consulting Services", 12500.0, 5000.0, 250, "Active"),
    ("GenAI Agent Readiness Assessment", "Consulting Services", 16000.0, 6500.0, 180, "Active"),
    ("Bronze Support Package (Email 24h)", "Support Packages", 600.0, 150.0, 9999, "Active"),
    ("Silver Support Package (8x5 Phone)", "Support Packages", 1800.0, 450.0, 9999, "Active"),
    ("Gold Support Package (24/7 SLA 1h)", "Support Packages", 4800.0, 1200.0, 9999, "Active"),
    ("Platinum Support Package (Dedicated TAM)", "Support Packages", 9500.0, 2800.0, 9999, "Active"),
    ("Legacy Dial-in Support Tier", "Support Packages", 900.0, 400.0, 0, "Discontinued"),
    ("API Gateway Annual Subscription", "Cloud Services", 3600.0, 1100.0, 9999, "Active"),
    ("Log Aggregator & SIEM Connector", "Cloud Services", 4900.0, 1500.0, 9999, "Active"),
    ("Real-Time Telemetry Dashboard", "Software Licenses", 2500.0, 600.0, 600, "Active"),
    ("Multi-Factor Identity Enforcer", "Software Licenses", 1900.0, 500.0, 850, "Active"),
    ("Zero-Trust Network Connector", "Software Licenses", 3800.0, 950.0, 500, "Active"),
    ("Enterprise Backup Agent (10TB)", "Cloud Services", 1400.0, 450.0, 9999, "Active"),
    ("Database Migration Toolkit Pro", "Software Licenses", 2800.0, 700.0, 400, "Active"),
    ("Automated Compliance Scanner", "Software Licenses", 5400.0, 1400.0, 320, "Active"),
    ("Kubernetes Fleet Orchestrator", "Software Licenses", 7200.0, 1900.0, 250, "Active"),
    ("High-Availability Load Balancer", "Hardware", 4900.0, 2900.0, 75, "Active"),
    ("Industrial Rugged Tablet", "Hardware", 2200.0, 1300.0, 110, "Active"),
    ("Optical Fiber Switch (48-Port)", "Hardware", 3900.0, 2300.0, 90, "Active"),
    ("Incident Response Retainer (Yearly)", "Consulting Services", 24000.0, 10000.0, 80, "Active"),
    ("Hands-on Engineering Bootcamp (Team)", "Consulting Services", 11000.0, 4500.0, 120, "Active"),
    ("Legacy COBOL Integration Bridge", "Software Licenses", 8500.0, 3000.0, 0, "Discontinued"),
]


def seed_database():
    """Build and seed the database reproducibly."""
    print(f"[*] Initializing database at: {DB_PATH}")

    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except Exception:
            pass

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Read and apply DDL schema
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    cursor.executescript(schema_sql)
    conn.commit()
    print("[+] Applied schema.sql successfully.")

    # 1. Seed Departments (8 rows)
    cursor.executemany(
        "INSERT INTO departments (department_name, code, budget, location, created_at) VALUES (?, ?, ?, ?, ?);",
        DEPARTMENTS,
    )
    conn.commit()
    print(f"[+] Seeded {len(DEPARTMENTS)} departments.")

    # 2. Seed Employees (75 rows)
    employees = []
    used_emails = set()
    emp_id = 1
    for dept_id in range(1, 9):
        role_list = ROLES_BY_DEPT.get(dept_id, [("Team Member", 90000)])
        # Assign 8-12 employees per department
        count_for_dept = 11 if dept_id in (1, 2) else 9
        for _ in range(count_for_dept):
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            email_base = f"{first.lower()}.{last.lower()}"
            email = f"{email_base}@enterprise.com"
            counter = 1
            while email in used_emails:
                email = f"{email_base}{counter}@enterprise.com"
                counter += 1
            used_emails.add(email)

            role, base_salary = random.choice(role_list)
            # Add variance to salary
            salary = round(base_salary * random.uniform(0.92, 1.15), 2)

            # Hire date between 2020-01-01 and 2024-12-31
            hire_days_ago = random.randint(30, 1600)
            hire_date = (datetime.now() - timedelta(days=hire_days_ago)).strftime("%Y-%m-%d")

            status = random.choices(["Active", "On Leave", "Terminated"], weights=[0.88, 0.08, 0.04])[0]
            employees.append((first, last, email, dept_id, role, salary, hire_date, status))
            emp_id += 1

    cursor.executemany(
        """INSERT INTO employees
           (first_name, last_name, email, department_id, role, salary, hire_date, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?);""",
        employees,
    )
    conn.commit()
    print(f"[+] Seeded {len(employees)} employees.")

    # 3. Seed Customers (120 rows)
    COMPANY_PREFIXES = ["Apex", "Vertex", "Quantum", "Beacon", "Pinnacle", "Starlight", "Horizon",
                        "Omega", "Titan", "Cascade", "Vanguard", "Summit", "Nexus", "Aegis", "Catalyst"]
    COMPANY_SUFFIXES = ["Technologies", "Logistics", "Financial", "Health", "Solutions", "Industries",
                        "Systems", "Networks", "Enterprises", "Holdings", "Global", "Consulting", "Dynamics"]
    customers = []
    used_companies = set()
    for i in range(1, 121):
        while True:
            c_name = f"{random.choice(COMPANY_PREFIXES)} {random.choice(COMPANY_SUFFIXES)}"
            if c_name not in used_companies:
                used_companies.add(c_name)
                break

        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        contact_name = f"{first} {last}"
        contact_email = f"{first.lower()}.{last.lower()}@{c_name.lower().replace(' ', '')[:12]}.com"
        industry = random.choice(INDUSTRIES)
        region, country = random.choice(REGIONS)
        tier = random.choices(TIERS, weights=[0.25, 0.45, 0.30])[0]

        created_days_ago = random.randint(60, 1400)
        created_at = (datetime.now() - timedelta(days=created_days_ago)).strftime("%Y-%m-%d")
        customers.append((c_name, contact_name, contact_email, industry, region, country, tier, created_at))

    cursor.executemany(
        """INSERT INTO customers
           (company_name, contact_name, contact_email, industry, region, country, tier, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?);""",
        customers,
    )
    conn.commit()
    print(f"[+] Seeded {len(customers)} customers.")

    # 4. Seed Products (40 rows)
    cursor.executemany(
        """INSERT INTO products
           (product_name, category, unit_price, cost_price, stock_quantity, status)
           VALUES (?, ?, ?, ?, ?, ?);""",
        PRODUCTS_DATA,
    )
    conn.commit()
    print(f"[+] Seeded {len(PRODUCTS_DATA)} products.")

    # 5. Seed Orders (450 rows) & Order Items (1250 rows)
    # Sales reps are employees in department_id = 2
    cursor.execute("SELECT employee_id FROM employees WHERE department_id = 2;")
    sales_rep_ids = [row[0] for row in cursor.fetchall()]

    orders = []
    order_items = []
    item_id = 1

    # Product cache (id, price, status)
    cursor.execute("SELECT product_id, unit_price, status FROM products;")
    products_db = cursor.fetchall()
    active_products = [p for p in products_db if p[2] == "Active"]

    for order_id in range(1, 451):
        cust_id = random.randint(1, 120)
        emp_id = random.choice(sales_rep_ids)

        days_ago = random.randint(1, 650)
        order_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

        order_status = random.choices(
            ["Completed", "Processing", "Cancelled", "Refunded"],
            weights=[0.82, 0.10, 0.05, 0.03],
        )[0]

        if order_status == "Completed":
            payment_status = "Paid"
        elif order_status == "Processing":
            payment_status = random.choice(["Paid", "Pending"])
        else:
            payment_status = random.choice(["Failed", "Paid"])

        channel = random.choices(["Direct Sales", "Online Portal", "Partner Referral"], weights=[0.55, 0.30, 0.15])[0]

        # 1 to 5 order items per order
        num_items = random.randint(1, 5)
        picked_products = random.sample(active_products, k=min(num_items, len(active_products)))

        order_total = 0.0
        for p in picked_products:
            p_id = p[0]
            unit_price = p[1]
            qty = random.randint(1, 4)
            discount = random.choice([0.0, 0.0, 0.05, 0.10, 0.15, 0.20])
            line_total = round(qty * unit_price * (1.0 - discount), 2)
            order_total += line_total

            order_items.append((order_id, p_id, qty, unit_price, discount, line_total))
            item_id += 1

        order_total = round(order_total, 2)
        orders.append((order_id, cust_id, emp_id, order_date, order_status, payment_status, order_total, channel))

    cursor.executemany(
        """INSERT INTO orders
           (order_id, customer_id, employee_id, order_date, order_status, payment_status, total_amount, channel)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?);""",
        orders,
    )
    conn.commit()

    cursor.executemany(
        """INSERT INTO order_items
           (order_id, product_id, quantity, unit_price, discount_pct, line_total)
           VALUES (?, ?, ?, ?, ?, ?);""",
        order_items,
    )
    conn.commit()

    print(f"[+] Seeded {len(orders)} orders.")
    print(f"[+] Seeded {len(order_items)} order items.")

    # Verification and Summary Counts
    tables = ["departments", "employees", "customers", "products", "orders", "order_items"]
    total_rows = 0
    print("\n" + "=" * 50)
    print("DATABASE SEEDING SUMMARY (enterprise_business.db)")
    print("=" * 50)
    for t in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {t};")
        cnt = cursor.fetchone()[0]
        total_rows += cnt
        print(f"  {t:<16}: {cnt:>6} rows")
    print("-" * 50)
    print(f"  TOTAL RECORDS   : {total_rows:>6} rows")
    print("=" * 50)

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
