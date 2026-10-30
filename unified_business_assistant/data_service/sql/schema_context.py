import re
from typing import Optional, Tuple

SCHEMA_METADATA = {
    "Customers": {
        "columns": [
            ("CustomerID", "TEXT PK"),
            ("CustomerName", "TEXT"),
            ("CompanyName", "TEXT"),
            ("ContactName", "TEXT"),
            ("ContactTitle", "TEXT"),
            ("Address", "TEXT"),
            ("City", "TEXT"),
            ("Region", "TEXT"),
            ("PostalCode", "TEXT"),
            ("Country", "TEXT"),
            ("Phone", "TEXT"),
        ],
        "relationships": ["1-to-many Orders (via Orders.CustomerID)"],
    },
    "Products": {
        "columns": [
            ("ProductID", "INTEGER PK"),
            ("ProductName", "TEXT"),
            ("SupplierID", "INTEGER FK -> Suppliers.SupplierID"),
            ("CategoryID", "INTEGER FK -> Categories.CategoryID"),
            ("QuantityPerUnit", "TEXT"),
            ("UnitPrice", "NUMERIC"),
            ("Price", "NUMERIC"),
            ("UnitsInStock", "INTEGER"),
            ("UnitsOnOrder", "INTEGER"),
            ("ReorderLevel", "INTEGER"),
            ("Discontinued", "INTEGER"),
        ],
        "relationships": [
            "many-to-1 Suppliers (via SupplierID)",
            "many-to-1 Categories (via CategoryID)",
            "1-to-many OrderDetails (via OrderDetails.ProductID)",
        ],
    },
    "Categories": {
        "columns": [
            ("CategoryID", "INTEGER PK"),
            ("CategoryName", "TEXT"),
            ("Description", "TEXT"),
        ],
        "relationships": ["1-to-many Products (via Products.CategoryID)"],
    },
    "Suppliers": {
        "columns": [
            ("SupplierID", "INTEGER PK"),
            ("CompanyName", "TEXT"),
            ("ContactName", "TEXT"),
            ("ContactTitle", "TEXT"),
            ("City", "TEXT"),
            ("Country", "TEXT"),
            ("Phone", "TEXT"),
        ],
        "relationships": ["1-to-many Products (via Products.SupplierID)"],
    },
    "Orders": {
        "columns": [
            ("OrderID", "INTEGER PK"),
            ("CustomerID", "TEXT FK -> Customers.CustomerID"),
            ("EmployeeID", "INTEGER FK -> Employees.EmployeeID"),
            ("OrderDate", "DATETIME"),
            ("RequiredDate", "DATETIME"),
            ("ShippedDate", "DATETIME"),
            ("ShipVia", "INTEGER FK -> Shippers.ShipperID"),
            ("Freight", "NUMERIC"),
            ("ShipName", "TEXT"),
            ("ShipCity", "TEXT"),
            ("ShipCountry", "TEXT"),
        ],
        "relationships": [
            "many-to-1 Customers (via CustomerID)",
            "many-to-1 Employees (via EmployeeID)",
            "many-to-1 Shippers (via ShipVia = ShipperID)",
            "1-to-many OrderDetails (via OrderDetails.OrderID)",
        ],
    },
    "OrderDetails": {
        "columns": [
            ("OrderID", "INTEGER PK FK -> Orders.OrderID"),
            ("ProductID", "INTEGER PK FK -> Products.ProductID"),
            ("UnitPrice", "NUMERIC"),
            ("Quantity", "INTEGER"),
            ("Discount", "REAL"),
        ],
        "relationships": [
            "many-to-1 Orders (via OrderID)",
            "many-to-1 Products (via ProductID)",
        ],
    },
    "Employees": {
        "columns": [
            ("EmployeeID", "INTEGER PK"),
            ("LastName", "TEXT"),
            ("FirstName", "TEXT"),
            ("Title", "TEXT"),
            ("ReportsTo", "INTEGER FK -> Employees.EmployeeID"),
            ("BirthDate", "DATE"),
            ("HireDate", "DATE"),
            ("City", "TEXT"),
            ("Country", "TEXT"),
        ],
        "relationships": [
            "1-to-many Orders (via Orders.EmployeeID)",
            "self-referential hierarchy (via ReportsTo)",
        ],
    },
    "Shippers": {
        "columns": [
            ("ShipperID", "INTEGER PK"),
            ("ShipperName", "TEXT"),
            ("CompanyName", "TEXT"),
            ("Phone", "TEXT"),
        ],
        "relationships": ["1-to-many Orders (via Orders.ShipVia = Shippers.ShipperID)"],
    },
}

RECOGNIZED_TERMS = {
    "customer", "customers", "client", "clients", "company", "companies",
    "product", "products", "item", "items", "goods", "beverage", "beverages",
    "category", "categories", "supplier", "suppliers", "vendor", "vendors",
    "shipper", "shippers", "shipping", "freight", "delivery", "ship",
    "order", "orders", "orderdetails", "ordered", "sales", "revenue", "spend", "spent", "total",
    "employee", "employees", "staff", "representative", "rep", "manager", "hire", "hired",
    "price", "unitprice", "cost", "quantity", "stock", "unitsinstock", "unitsonorder", "discount",
    "country", "countries", "city", "cities", "address", "postalcode", "phone",
    "germany", "london", "paris", "japan", "berlin", "usa", "uk", "france", "brazil", "canada",
    "chais", "chang", "tofu", "aniseed", "syrup", "anton", "cajun",
}

UNSUPPORTED_DOMAINS = [
    (r"\b(weather|temperature|forecast|rain)\b", "weather and atmospheric conditions"),
    (r"\b(stock\s+price|ticker|nasdaq|dow jones|s&p|share price|nse)\b", "external stock market ticker data"),
    (r"\b(password|wifi|credential|api key|secret|credit card|card number|bank account|ssn|pin)\b", "security credentials and payment secrets"),
    (r"\b(cafeteria|lunch|canteen)\b", "cafeteria and dining information"),
    (r"\b(posh|maternity leave|parental leave|dress code|complaint|whistleblower)\b", "HR policy documents (handled by Knowledge Service /search)"),
    (r"\b(medical|doctor|diagnosis|prescription|patient|health insurance claim)\b", "healthcare records and insurance claims"),
    (r"\b(box office|movie ticket|hollywood)\b", "cinema box office records"),
    (r"\b(bitcoin|crypto|ethereum|blockchain)\b", "cryptocurrency market feeds"),
]


class SchemaContextBuilder:
    @classmethod
    def get_compact_schema_prompt(cls) -> str:
        lines = ["Database Schema (SQLite - Northwind):\n"]
        for table_name, meta in SCHEMA_METADATA.items():
            col_strs = [f"{col_name} ({col_type})" for col_name, col_type in meta["columns"]]
            lines.append(f"- {table_name}: {', '.join(col_strs)}")
            lines.append(f"  Links: {'; '.join(meta['relationships'])}")

        lines.extend([
            "\nQuery Rules:",
            "- Products table has Price and UnitPrice.",
            "- Customers table has CustomerName, ContactName, and CompanyName.",
            "- OrderDetails (or [Order Details]) holds line items (Quantity, UnitPrice, Discount).",
            "- Line total = Quantity * UnitPrice * (1 - Discount).",
            "- Return only SQLite SELECT queries.",
        ])
        return "\n".join(lines)

    @classmethod
    def check_answerability(cls, question: str) -> Tuple[bool, Optional[str]]:
        q_lower = question.lower().strip()

        for pattern, domain_desc in UNSUPPORTED_DOMAINS:
            if re.search(pattern, q_lower):
                return False, f"Question asks for {domain_desc}, which is not in the database."

        words = set(re.findall(r"\b[a-z]{3,}\b", q_lower))
        has_relevant_concept = bool(words.intersection(RECOGNIZED_TERMS))
        if not has_relevant_concept:
            return False, "Question asks for entities that do not exist in the database schema."

        return True, None
