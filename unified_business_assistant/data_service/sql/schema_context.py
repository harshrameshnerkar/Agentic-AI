"""
Compact Schema Context Builder for Role B (Data Service).

Extracts and formats a token-efficient representation of the database schema
specifically designed for text-to-SQL LLM prompts (UNIFIED-BUSINESS-ASSISTAN.md §4.3).
Also provides semantic domain classification to identify unanswerable questions.
"""
import re
from typing import Dict, List, Optional, Set, Tuple

# Schema definition with primary keys, foreign keys, and column meanings
SCHEMA_METADATA = {
    "departments": {
        "columns": [
            ("department_id", "INTEGER PK"),
            ("department_name", "TEXT UK"),
            ("code", "TEXT UK (e.g. ENG, SALES, FIN)"),
            ("budget", "REAL (annual budget in USD)"),
            ("location", "TEXT (city/state)"),
            ("created_at", "TEXT (YYYY-MM-DD)"),
        ],
        "relationships": ["1-to-many employees (via employees.department_id)"],
    },
    "employees": {
        "columns": [
            ("employee_id", "INTEGER PK"),
            ("first_name", "TEXT"),
            ("last_name", "TEXT"),
            ("email", "TEXT UK"),
            ("department_id", "INTEGER FK -> departments.department_id"),
            ("role", "TEXT (job title)"),
            ("salary", "REAL (annual base salary in USD)"),
            ("hire_date", "TEXT (YYYY-MM-DD)"),
            ("status", "TEXT ('Active', 'On Leave', 'Terminated')"),
        ],
        "relationships": [
            "many-to-1 departments (via department_id)",
            "1-to-many orders (via orders.employee_id for Sales Reps in dept 2)",
        ],
    },
    "customers": {
        "columns": [
            ("customer_id", "INTEGER PK"),
            ("company_name", "TEXT UK"),
            ("contact_name", "TEXT"),
            ("contact_email", "TEXT"),
            ("industry", "TEXT ('Technology', 'Healthcare', 'Finance', 'Retail', 'Manufacturing', 'Education')"),
            ("region", "TEXT ('North America', 'Europe', 'Asia-Pacific', 'Latin America')"),
            ("country", "TEXT"),
            ("tier", "TEXT ('Enterprise', 'Mid-Market', 'Startup')"),
            ("created_at", "TEXT (YYYY-MM-DD)"),
        ],
        "relationships": ["1-to-many orders (via orders.customer_id)"],
    },
    "products": {
        "columns": [
            ("product_id", "INTEGER PK"),
            ("product_name", "TEXT UK"),
            ("category", "TEXT ('Software Licenses', 'Cloud Services', 'Hardware', 'Consulting Services', 'Support Packages')"),
            ("unit_price", "REAL (list selling price)"),
            ("cost_price", "REAL (cost of goods sold)"),
            ("stock_quantity", "INTEGER"),
            ("status", "TEXT ('Active', 'Discontinued')"),
        ],
        "relationships": ["1-to-many order_items (via order_items.product_id)"],
    },
    "orders": {
        "columns": [
            ("order_id", "INTEGER PK"),
            ("customer_id", "INTEGER FK -> customers.customer_id"),
            ("employee_id", "INTEGER FK -> employees.employee_id (sales rep)"),
            ("order_date", "TEXT (YYYY-MM-DD)"),
            ("order_status", "TEXT ('Completed', 'Processing', 'Cancelled', 'Refunded')"),
            ("payment_status", "TEXT ('Paid', 'Pending', 'Failed')"),
            ("total_amount", "REAL (gross revenue sum of line items)"),
            ("channel", "TEXT ('Direct Sales', 'Online Portal', 'Partner Referral')"),
        ],
        "relationships": [
            "many-to-1 customers (via customer_id)",
            "many-to-1 employees (via employee_id)",
            "1-to-many order_items (via order_items.order_id)",
        ],
    },
    "order_items": {
        "columns": [
            ("item_id", "INTEGER PK"),
            ("order_id", "INTEGER FK -> orders.order_id"),
            ("product_id", "INTEGER FK -> products.product_id"),
            ("quantity", "INTEGER"),
            ("unit_price", "REAL"),
            ("discount_pct", "REAL (e.g. 0.10 for 10%)"),
            ("line_total", "REAL (quantity * unit_price * (1 - discount_pct))"),
        ],
        "relationships": [
            "many-to-1 orders (via order_id)",
            "many-to-1 products (via product_id)",
        ],
    },
}

# Domain vocabulary of terms our database supports
RECOGNIZED_TERMS = {
    "customer", "customers", "client", "clients", "company", "companies",
    "order", "orders", "invoice", "invoices", "sales", "revenue", "spend",
    "spent", "employee", "employees", "staff", "salary", "salaries", "compensation",
    "department", "departments", "role", "roles", "product", "products",
    "discount", "discounts", "category", "categories", "region", "regions",
    "country", "countries", "industry", "industries", "tier", "channel",
    "active", "terminated", "completed", "paid", "pending", "budget",
    "hardware", "software", "license", "licenses", "stock", "quantity", "units",
    "cost", "margin", "price", "unit_price", "cost_price"
}

# Terms that are clearly OUT-OF-SCOPE for our structured database
UNSUPPORTED_DOMAINS = [
    (r"\b(weather|temperature|forecast|rain)\b", "weather and atmospheric conditions"),
    (r"\b(stock\s+price|ticker|nasdaq|dow jones|s&p|share price)\b", "external stock market ticker data"),
    (r"\b(password|wifi|credential|api key|secret|credit card|card number|bank account|ssn|pin)\b", "internal security credentials and payment secrets"),
    (r"\b(cafeteria|lunch|menu|food|canteen)\b", "company cafeteria and dining information"),
    (r"\b(policy|handbook|posh|maternity leave|parental leave|dress code|complaint)\b", "unstructured HR policy documents (owned by Knowledge Service /search)"),
    (r"\b(medical|doctor|diagnosis|prescription|patient|health insurance claim)\b", "personal healthcare records and insurance claims"),
    (r"\b(movie|cinema|actor|film|box office)\b", "entertainment and film data"),
]


class SchemaContextBuilder:
    """Formats concise schema context for LLM prompts and handles domain classification."""

    @classmethod
    def get_compact_schema_prompt(cls) -> str:
        """
        Builds a compact, token-efficient string representation of the schema.
        Consumes < 450 tokens.
        """
        lines = [
            "### DATABASE SCHEMA (SQLite):",
            "You have read-only access to an enterprise SQLite database with 6 tables:\n",
        ]

        for table_name, meta in SCHEMA_METADATA.items():
            col_strs = [f"{col_name} ({col_type})" for col_name, col_type in meta["columns"]]
            lines.append(f"• **{table_name}**:")
            lines.append(f"  Columns: {', '.join(col_strs)}")
            lines.append(f"  FK / Links: {'; '.join(meta['relationships'])}\n")

        lines.extend([
            "### BUSINESS RULES:",
            "- Completed revenue = `orders.total_amount WHERE order_status = 'Completed' AND payment_status = 'Paid'`",
            "- Sales reps = `employees` in department_id = 2 ('Sales & Business Development')",
            "- Always use table aliases and explicit JOIN conditions.",
            "- Return ONLY standard SQLite SELECT queries. Never generate destructive statements.",
        ])

        return "\n".join(lines)

    @classmethod
    def check_answerability(cls, question: str) -> Tuple[bool, Optional[str]]:
        """
        Evaluates whether the question can be answered from the available schema.
        Returns:
            (answerable: bool, reason: Optional[str])
        """
        q_lower = question.lower().strip()

        # Check explicit out-of-scope domain patterns
        for pattern, domain_desc in UNSUPPORTED_DOMAINS:
            if re.search(pattern, q_lower):
                return False, f"The question asks for {domain_desc}, which is not present in the structured business database."

        # Extract words from question
        words = set(re.findall(r"\b[a-z]{3,}\b", q_lower))

        # Check if the question overlaps with any known business concepts
        has_relevant_concept = bool(words.intersection(RECOGNIZED_TERMS))

        # Check for generic data query keywords
        generic_data_words = {"how", "many", "what", "which", "who", "top", "list", "total", "average", "count", "sum", "highest", "lowest"}
        if words.issubset(generic_data_words) or not has_relevant_concept:
            # If there are zero matching business terms, question cannot be answered
            if not has_relevant_concept:
                return False, "The question asks for concepts or entities that do not exist in the enterprise database schema."

        return True, None
