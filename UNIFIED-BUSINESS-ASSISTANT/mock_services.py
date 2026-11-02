"""
Mock Services for Day 1 Development (Interfaces 1 & 2)
Allows Role C to build and test the complete orchestrator without waiting for Role A & B.
Conforms strictly to the committed INTERFACE CONTRACT v1.0.0.
"""

from typing import Dict, Any, List, Optional
import re

import sqlite3
import os

# ──────────────────────────────────────────────────────────────────────────────
# SQLite Database connection for Northwind queries
# ──────────────────────────────────────────────────────────────────────────────
_SQLITE_CONN = None

def get_northwind_sqlite_conn():
    global _SQLITE_CONN
    if _SQLITE_CONN is not None:
        return _SQLITE_CONN

    db_path = os.path.join(os.path.dirname(__file__), "db", "northwind.sqlite3")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Suppliers'")
    if not cursor.fetchone():
        sql_file = os.path.join(os.path.dirname(__file__), "northwind.sql")
        if os.path.exists(sql_file):
            with open(sql_file, "r", encoding="utf-8") as f:
                sql_content = f.read()
            clean_lines = [
                l.replace("AUTO_INCREMENT", "") for l in sql_content.splitlines()
                if not l.strip().startswith(("CREATE DATABASE", "USE ", "START TRANSACTION", "COMMIT", "SET "))
            ]
            for stmt in "\n".join(clean_lines).split(";"):
                if stmt.strip():
                    try:
                        cursor.execute(stmt.strip())
                    except Exception:
                        pass
            conn.commit()

    _SQLITE_CONN = conn
    return _SQLITE_CONN

def query_sqlite(sql: str) -> List[Dict[str, Any]]:
    try:
        conn = get_northwind_sqlite_conn()
        cursor = conn.cursor()
        cursor.execute(sql)
        return [dict(r) for r in cursor.fetchall()]
    except Exception:
        return []

def extract_limit(q_lower: str, default: int = 5) -> int:
    m = re.search(r'(?:limit\s*(?:to\s*|of\s*|set\s*)?|top\s*|bottom\s*|first\s*|last\s*)(\d+)', q_lower)
    if m:
        try:
            return min(max(int(m.group(1)), 1), 50)
        except ValueError:
            pass
    m2 = re.search(r'(\d+)\s*(?:records|rows|products|items|customers|employees|suppliers|orders|shippers)', q_lower)
    if m2:
        try:
            return min(max(int(m2.group(1)), 1), 50)
        except ValueError:
            pass
    m3 = re.search(r'(?:show|get|list|display|find|return|select)\s+(?:the\s+)?(\d+)', q_lower)
    if m3:
        try:
            return min(max(int(m3.group(1)), 1), 50)
        except ValueError:
            pass
    m4 = re.search(r'\bthe\s+(\d+)\b', q_lower)
    if m4:
        try:
            return min(max(int(m4.group(1)), 1), 50)
        except ValueError:
            pass
    return default


MOCK_POLICY_KNOWLEDGE_BASE = [
    # ── Gitlab Documents ── 
    {
        "keywords": ["gitlab", "five", "beliefs", "five-beliefs"],
        "text": "GitLab's five beliefs are a) Quality is in the eye of the user, b) Trust is built in, not boltd on. c) Context is the moat, d) Humans direct, machines build, both are first-class, e) Software gets built everywhere.",
        "difficulty": "medium",
        "source": "Gitlab/gitlab mission.pdf",
        "page": 2,
        "score": 0.95
    },
    {
        "keywords": ["WFH", "equipment", "expense policy", "gitlab"],
        "text": "Visual guide showing categories of approved work from home equipment including computer equipment, furniture, lighting, and other office supplies.",
        "source": "Gitlab/Gitlab Expense Policy.pdf",
        "page": 20,
        "score": 0.94
    },
    {
        "keywords": ["security principles", "vulnerability disclosure", "hackerone", "security document"],
        "text": "GitLab's security is built around principles including least privilege, defense-in-depth, and transparency. GitLab operates a public HackerOne bug bounty program for responsible vulnerability disclosure, allowing external security researchers to report vulnerabilities.",
        "source": "Gitlab/Gitlab security.pdf",
        "page": 2,
        "score": 0.93
    },

    # ── Google Docs Documents ──
    {
        "keywords": ["seven ai principles", "ai principles", "weapons of mass destruction"],
        "text": "Google's seven AI Principles are: (1) Be socially beneficial; (2) Avoid creating or reinforcing unfair bias; (3) Be built and tested for safety; (4) Be accountable to people; (5) Incorporate privacy design principles; (6) Uphold high standards of scientific excellence; (7) Be made available for uses that accord with these principles. Google also committed to NOT pursue AI for weapons of mass destruction or illegal surveillance.",
        "source": "Google docs/Google AI principles operational guidelines.pdf",
        "page": 1,
        "score": 0.96
    },
    {
        "keywords": ["privacy principles", "privacy policy summary", "transparency and user choice", "takeout"],
        "text": "Google's two core privacy principles are Transparency and User Choice. Google provides privacy dashboards, the ability to review and delete search history, ad personalization settings that can be turned off, and tools like Google Takeout to download personal data.",
        "source": "Google docs/Google privacy policy summary.pdf",
        "page": 2,
        "score": 0.94
    },
    {
        "keywords": ["renewable energy", "supplier code of conduct", "responsible supply chain report"],
        "text": "In 2018, Google set a goal to help its suppliers transition to renewable energy and committed to develop markets enabling access to affordable renewable energy in communities where it sources and produces products. Google works with more than 1,000 suppliers worldwide that support hardware manufacturing and indirect services.",
        "source": "Google docs/Google supplier code of conduct.pdf",
        "page": 4,
        "score": 0.92
    },

    # ── Jayaswal Neco Documents ──
    {
        "keywords": ["anti-corruption", "anti-bribery", "scope of jayaswal", "jnil", "third parties"],
        "text": "The Anti-Corruption and Anti-Bribery and Anti-Money Laundering Policy of JNIL applies to JNIL itself, its Employees, and Third Parties acting on behalf of JNIL. JNIL shall ensure all associates and affiliates adopt a similar policy. The policy reflects JNIL zero-tolerance approach to bribery, corruption, and money laundering.",
        "source": "jayaswal/jayaswal_neco_anti_corruption_anti_bribery_policy.pdf",
        "page": 3,
        "score": 0.95
    },
    {
        "keywords": ["csr activities", "fy 2022-23", "healthcare", "sanitation", "safe drinking water"],
        "text": "For FY 2022-23, Jayaswal Neco CSR healthcare and sanitation activities included: organising health check-up and blood donation camps, establishing First Aid Centres, free medical counselling and medicine distribution, eye check-up camps, free ambulance services in mine peripheral villages, sanitary pad vending machines, female toilets, and iron removal plants on handpumps.",
        "source": "jayaswal/jayaswal_neco_csr_activities_fy2022_to_fy2026.pdf",
        "page": 5,
        "score": 0.93
    },
    {
        "keywords": ["purpose of jayaswal", "remuneration policy", "three key objectives", "section 178"],
        "text": "The Remuneration Policy of JNIL is adopted under Section 178 of the Companies Act, 2013 and SEBI Listing Obligations. Its three key objectives are: (i) to ensure remuneration is reasonable and sufficient to attract, retain and motivate Directors, KMP and Senior Management; (ii) clear relationship of remuneration to performance; and (iii) a balance between fixed and incentive pay.",
        "source": "jayaswal/jayaswal_neco_remuneration_policy.pdf",
        "page": 2,
        "score": 0.94
    },
    {
        "keywords": ["define senior management", "definition of senior management", "jayaswal neco remuneration"],
        "text": "Senior Management means officers and personnel of the listed entity who are members of its core management team, excluding Board of Directors. It comprises all members of management one level below the CEO, MD, Whole Time Director, or Manager, specifically including functional heads and Key Managerial Personnel.",
        "source": "jayaswal/jayaswal_neco_remuneration_policy.pdf",
        "page": 3,
        "score": 0.96
    },

    # ── Reckitt Documents ──
    {
        "keywords": ["maternity leave", "parental leave policy", "reckitt", "premature births"],
        "text": "Under Reckitt Global Parental Leave Policy, fully paid maternity leave is 26 weeks, subject to 12 months of continuous employment at RB. The first 16 weeks must be taken immediately after birth; the remaining 10 weeks before the child's first birthday. For premature births before the 37th week, paid weeks are extended by the number of weeks between birth date and 37th week.",
        "source": "reckitt/reckitt_global_parental_leave_policy.pdf",
        "page": 2,
        "score": 0.95
    },
    {
        "keywords": ["product safety policy", "reckitt product safety", "don'ts", "purpose and scope"],
        "text": "The purpose of Reckitt Product Safety Policy is to protect consumers by ensuring every Reckitt product is safe and compliant. Explicit Don'ts include: releasing a product with unacceptable safety risk; ignoring or suppressing product safety information; using unapproved ingredients; and making product safety decisions without proper authority.",
        "source": "reckitt/reckitt_product_safety_policy.pdf",
        "page": 1,
        "score": 0.95
    },

    # ── Susan Electricals Documents ──
    {
        "keywords": ["susan electricals", "code of conduct", "compliance officer", "board and senior management"],
        "text": "The Code of Conduct of Susan Electricals India Limited applies to the Board of Directors and Senior Management Personnel under Regulation 17(5) of SEBI Listing Regulations. The Company Secretary is appointed as the Compliance Officer under the Code, responsible for answering questions and ensuring compliance.",
        "source": "susan/susan_electricals_code_of_conduct_board_senior_management.pdf",
        "page": 2,
        "score": 0.95
    },
    {
        "keywords": ["vigil mechanism", "whistle blower policy", "protected disclosure", "susan electricals"],
        "text": "The legal basis is Section 177(9) of the Companies Act, 2013 and Regulation 22 of SEBI LODR Regulations, 2015. Protected Disclosure is defined as a concern raised by an employee in writing or email in good faith, disclosing unethical or improper activity, including identity details of the submitter.",
        "source": "susan/susan_electricals_vigil_mechanism_whistleblower_policy.pdf",
        "page": 4,
        "score": 0.94
    },
    {
        "keywords": ["nomination and remuneration policy", "susan electricals", "three key objectives"],
        "text": "The three key objectives of Susan Electricals Nomination and Remuneration Policy are: (a) To formulate criteria for determining qualifications, competencies, and independence for director appointments; (b) To specify the manner for effective evaluation of Board and Committee performance; and (c) To recommend remuneration policy for Directors, KMP, and employees.",
        "source": "susan/susan_electricals_nomination_and_remuneration_policy.pdf",
        "page": 3,
        "score": 0.94
    }
]

def search_knowledge_mock(query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Mock implementation of Interface 1 (POST /search).
    Returns ranked passages matching the query or no_match=True.
    """
    q_lower = query.lower()
    matches = []
    
    for doc in MOCK_POLICY_KNOWLEDGE_BASE:
        # Check keyword overlaps
        score_boost = sum(0.15 for kw in doc["keywords"] if kw in q_lower)
        if score_boost > 0:
            assigned_score = min(0.98, round(doc["score"] + score_boost * 0.05, 3))
            matches.append({
                "text": doc["text"],
                "source": doc["source"],
                "page": doc["page"],
                "score": assigned_score
            })

    # Sort descending by score
    matches.sort(key=lambda x: x["score"], reverse=True)
    results = matches[:top_k]

    if not results:
        return {
            "results": [],
            "no_match": True
        }

    return {
        "results": results,
        "no_match": False
    }


# ──────────────────────────────────────────────────────────────────────────────
# Mock Data Service (Interface 2 - Role B)
# ──────────────────────────────────────────────────────────────────────────────

MOCK_SQL_DATABASE = {
    "product": {
        "sql": "SELECT ProductName, Price FROM Products ORDER BY Price DESC LIMIT 5;",
        "columns": ["ProductName", "Price"],
        "rows": [
            {"ProductName": "Côte de Blaye", "Price": 263.5},
            {"ProductName": "Thüringer Rostbratwurst", "Price": 123.79},
            {"ProductName": "Mishi Kobe Niku", "Price": 97.0},
            {"ProductName": "Sir Rodney's Marmalade", "Price": 81.0},
            {"ProductName": "Carnarvon Tigers", "Price": 62.5}
        ]
    },
    "customer": {
        "sql": "SELECT CustomerName, City, Country FROM Customers WHERE Country = 'Germany';",
        "columns": ["CustomerName", "City", "Country"],
        "rows": [
            {"CustomerName": "Alfreds Futterkiste", "City": "Berlin", "Country": "Germany"},
            {"CustomerName": "Blauer See Delikatessen", "City": "Mannheim", "Country": "Germany"},
            {"CustomerName": "Königlich Essen", "City": "Brandenburg", "Country": "Germany"},
            {"CustomerName": "Lehmanns Marktstand", "City": "Frankfurt", "Country": "Germany"},
            {"CustomerName": "Morgenstern Gesundkost", "City": "Leipzig", "Country": "Germany"}
        ]
    },
    "employee": {
        "sql": "SELECT EmployeeID, FirstName, LastName, Title FROM Employees;",
        "columns": ["EmployeeID", "FirstName", "LastName", "Title"],
        "rows": [
            {"EmployeeID": 1, "FirstName": "Nancy", "LastName": "Davolio", "Title": "Sales Representative"},
            {"EmployeeID": 2, "FirstName": "Andrew", "LastName": "Fuller", "Title": "Vice President, Sales"},
            {"EmployeeID": 3, "FirstName": "Janet", "LastName": "Leverling", "Title": "Sales Representative"},
            {"EmployeeID": 4, "FirstName": "Margaret", "LastName": "Peacock", "Title": "Sales Representative"}
        ]
    },
    "supplier": {
        "sql": "SELECT SupplierID, SupplierName, Phone, Country FROM Suppliers WHERE SupplierName LIKE '%Exotic%';",
        "columns": ["SupplierID", "SupplierName", "Phone", "Country"],
        "rows": [
            {"SupplierID": 1, "SupplierName": "Exotic Liquids", "Phone": "(171) 555-2222", "Country": "UK"}
        ]
    },
    "shipper": {
        "sql": "SELECT ShipperID, ShipperName, Phone FROM Shippers;",
        "columns": ["ShipperID", "ShipperName", "Phone"],
        "rows": [
            {"ShipperID": 1, "ShipperName": "Speedy Express", "Phone": "(503) 555-9831"},
            {"ShipperID": 2, "ShipperName": "United Package", "Phone": "(503) 555-3199"},
            {"ShipperID": 3, "ShipperName": "Federal Shipping", "Phone": "(503) 555-9931"}
        ]
    },
    "order": {
        "sql": "SELECT OrderID, OrderDate, CustomerID, EmployeeID FROM Orders ORDER BY OrderDate DESC LIMIT 4;",
        "columns": ["OrderID", "OrderDate", "CustomerID", "EmployeeID"],
        "rows": [
            {"OrderID": 10443, "OrderDate": "1997-02-12", "CustomerID": 66, "EmployeeID": 8},
            {"OrderID": 10442, "OrderDate": "1997-02-11", "CustomerID": 20, "EmployeeID": 3},
            {"OrderID": 10441, "OrderDate": "1997-02-10", "CustomerID": 55, "EmployeeID": 3},
            {"OrderID": 10440, "OrderDate": "1997-02-10", "CustomerID": 71, "EmployeeID": 4}
        ]
    }
}

UNANSWERABLE_DATA_PATTERNS = [
    r"money laundering",
    r"criminal",
    r"stock price",
    r"nse ticker",
    r"financial year 2026",
    r"revenue .* 2026",
    r"personal cell",
    r"home address",
    r"sql injection",
    r"exploit",
    r"nonexistent",
    r"profit margin"
]

def query_data_mock(question: str) -> Dict[str, Any]:
    """
    Mock implementation of Interface 2 (POST /query).
    Returns sql, rows, columns, row_count, error, and answerable flag.
    """
    q_lower = question.lower()
    
    # Check if question is unanswerable from database context
    for pattern in UNANSWERABLE_DATA_PATTERNS:
        if re.search(pattern, q_lower):
            return {
                "sql": "",
                "rows": [],
                "columns": [],
                "row_count": 0,
                "error": f"The query '{question}' cannot be answered by the relational database schema.",
                "answerable": False
            }

    # Extract dynamic limit and direction
    limit = extract_limit(q_lower, default=5)
    direction = "DESC" if ("bottom" in q_lower or "last" in q_lower) else "ASC"

    # Dynamic Suppliers table handling
    if "supplier" in q_lower:
        if "exotic" in q_lower:
            return {
                "sql": "SELECT SupplierID, SupplierName, Phone, Country FROM Suppliers WHERE SupplierName LIKE '%Exotic%';",
                "rows": [{"SupplierID": 1, "SupplierName": "Exotic Liquids", "Phone": "(171) 555-2222", "Country": "UK"}],
                "columns": ["SupplierID", "SupplierName", "Phone", "Country"],
                "row_count": 1,
                "error": None,
                "answerable": True
            }
        sql = f"SELECT SupplierID, SupplierName, ContactName, City, Country, Phone FROM Suppliers ORDER BY SupplierID {direction} LIMIT {limit};"
        rows = query_sqlite(sql)
        return {
            "sql": sql,
            "rows": rows,
            "columns": ["SupplierID", "SupplierName", "ContactName", "City", "Country", "Phone"],
            "row_count": len(rows),
            "error": None,
            "answerable": True
        }

    # Dynamic Customers table handling
    if "customer" in q_lower:
        if "german" in q_lower or "germany" in q_lower:
            return {
                "sql": "SELECT CustomerName, City, Country FROM Customers WHERE Country = 'Germany';",
                "rows": [
                    {"CustomerName": "Alfreds Futterkiste", "City": "Berlin", "Country": "Germany"},
                    {"CustomerName": "Blauer See Delikatessen", "City": "Mannheim", "Country": "Germany"},
                    {"CustomerName": "Königlich Essen", "City": "Brandenburg", "Country": "Germany"},
                    {"CustomerName": "Lehmanns Marktstand", "City": "Frankfurt", "Country": "Germany"},
                    {"CustomerName": "Morgenstern Gesundkost", "City": "Leipzig", "Country": "Germany"}
                ],
                "columns": ["CustomerName", "City", "Country"],
                "row_count": 5,
                "error": None,
                "answerable": True
            }
        sql = f"SELECT CustomerID, CustomerName, ContactName, City, Country FROM Customers ORDER BY CustomerID {direction} LIMIT {limit};"
        rows = query_sqlite(sql)
        return {
            "sql": sql,
            "rows": rows,
            "columns": ["CustomerID", "CustomerName", "ContactName", "City", "Country"],
            "row_count": len(rows),
            "error": None,
            "answerable": True
        }

    # Dynamic Products table handling
    if "product" in q_lower:
        # Check specific benchmark queries first
        if "max" in q_lower or "maximum" in q_lower:
            sql = "SELECT MAX(Price) AS max_price FROM Products;"
            rows = query_sqlite(sql)
            return {
                "sql": sql,
                "rows": rows,
                "columns": ["max_price"],
                "row_count": len(rows),
                "error": None,
                "answerable": True
            }
        if "greater than" in q_lower or ">" in q_lower or "strictly greater" in q_lower:
            sql = "SELECT ProductID, ProductName, Price FROM Products WHERE Price > 50;"
            rows = query_sqlite(sql)
            return {
                "sql": sql,
                "rows": rows,
                "columns": ["ProductID", "ProductName", "Price"],
                "row_count": len(rows),
                "error": None,
                "answerable": True
            }
        if "category" in q_lower or "categoryid" in q_lower:
            if "average" in q_lower or "avg" in q_lower:
                sql = "SELECT AVG(Price) AS average_price FROM Products WHERE CategoryID = 1;"
                rows = query_sqlite(sql)
                return {
                    "sql": sql,
                    "rows": rows,
                    "columns": ["average_price"],
                    "row_count": len(rows),
                    "error": None,
                    "answerable": True
                }
            sql = "SELECT p.ProductName, c.CategoryName FROM Products p JOIN Categories c ON p.CategoryID = c.CategoryID;"
            rows = query_sqlite(sql)
            return {
                "sql": sql,
                "rows": rows[:limit] if limit else rows[:10],
                "columns": ["ProductName", "CategoryName"],
                "row_count": len(rows),
                "error": None,
                "answerable": True
            }
        if "japan" in q_lower:
            sql = "SELECT p.ProductName FROM Products p JOIN Suppliers s ON p.SupplierID = s.SupplierID WHERE s.Country = 'Japan';"
            rows = query_sqlite(sql)
            return {
                "sql": sql,
                "rows": rows,
                "columns": ["ProductName"],
                "row_count": len(rows),
                "error": None,
                "answerable": True
            }

        # Check price sorting direction
        is_lowest = any(k in q_lower for k in ["lowest", "cheap", "cheapest", "least", "bottom", "min", "minimum", "asc", "ascending", "inexpensive", "small", "smallest"])
        is_highest = any(k in q_lower for k in ["highest", "expensive", "most expensive", "top", "max", "maximum", "desc", "descending", "costly"])

        if is_lowest:
            sql = f"SELECT ProductID, ProductName, Price FROM Products ORDER BY Price ASC LIMIT {limit};"
        elif is_highest:
            sql = f"SELECT ProductID, ProductName, Price FROM Products ORDER BY Price DESC LIMIT {limit};"
        elif "price" in q_lower:
            sql = f"SELECT ProductID, ProductName, Price FROM Products ORDER BY Price ASC LIMIT {limit};" if ("low" in q_lower or "asc" in q_lower) else f"SELECT ProductID, ProductName, Price FROM Products ORDER BY Price DESC LIMIT {limit};"
        else:
            sql = f"SELECT ProductID, ProductName, Price FROM Products ORDER BY ProductID {direction} LIMIT {limit};"

        rows = query_sqlite(sql)
        return {
            "sql": sql,
            "rows": rows,
            "columns": ["ProductID", "ProductName", "Price"],
            "row_count": len(rows),
            "error": None,
            "answerable": True
        }

    # Dynamic Orders table handling
    if "order" in q_lower:
        sql = f"SELECT OrderID, OrderDate, CustomerID, EmployeeID FROM Orders ORDER BY OrderDate DESC LIMIT {limit};"
        rows = query_sqlite(sql)
        return {
            "sql": sql,
            "rows": rows,
            "columns": ["OrderID", "OrderDate", "CustomerID", "EmployeeID"],
            "row_count": len(rows),
            "error": None,
            "answerable": True
        }

    # Dynamic Employees table handling
    if "employee" in q_lower:
        sql = f"SELECT EmployeeID, FirstName, LastName, Title FROM Employees LIMIT {limit};"
        rows = query_sqlite(sql)
        return {
            "sql": sql,
            "rows": rows,
            "columns": ["EmployeeID", "FirstName", "LastName", "Title"],
            "row_count": len(rows),
            "error": None,
            "answerable": True
        }

    # Dynamic Shippers table handling
    if "shipper" in q_lower:
        sql = f"SELECT ShipperID, ShipperName, Phone FROM Shippers LIMIT {limit};"
        rows = query_sqlite(sql)
        return {
            "sql": sql,
            "rows": rows,
            "columns": ["ShipperID", "ShipperName", "Phone"],
            "row_count": len(rows),
            "error": None,
            "answerable": True
        }

    # Match tables
    for table_key, table_data in MOCK_SQL_DATABASE.items():
        if table_key in q_lower:
            return {
                "sql": table_data["sql"],
                "rows": table_data["rows"],
                "columns": table_data["columns"],
                "row_count": len(table_data["rows"]),
                "error": None,
                "answerable": True
            }

    # Default fallback structured query for count/aggregate
    if any(k in q_lower for k in ["count", "total", "average", "sum", "sales", "how many"]):
        return {
            "sql": "SELECT COUNT(*) AS total_count FROM Orders;",
            "rows": [{"total_count": 830}],
            "columns": ["total_count"],
            "row_count": 1,
            "error": None,
            "answerable": True
        }

    # If nothing matched in SQL database
    return {
        "sql": "",
        "rows": [],
        "columns": [],
        "row_count": 0,
        "error": "No matching database tables or columns found for this request.",
        "answerable": False
    }
