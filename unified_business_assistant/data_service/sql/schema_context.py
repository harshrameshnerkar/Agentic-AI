"""
Compact Schema Context Builder for Role B (Data Service).

Extracts and formats a token-efficient representation of the authentic Chinook
database schema for text-to-SQL LLM prompts (UNIFIED-BUSINESS-ASSISTAN.md §4.3).
"""
import re
from typing import Dict, List, Optional, Set, Tuple

# Schema definition for the authentic Chinook enterprise relational database (15,607 real rows)
SCHEMA_METADATA = {
    "Customer": {
        "columns": [
            ("CustomerId", "INTEGER PK"),
            ("FirstName", "NVARCHAR(40)"),
            ("LastName", "NVARCHAR(20)"),
            ("Company", "NVARCHAR(80)"),
            ("Address", "NVARCHAR(70)"),
            ("City", "NVARCHAR(40)"),
            ("State", "NVARCHAR(40)"),
            ("Country", "NVARCHAR(40)"),
            ("PostalCode", "NVARCHAR(10)"),
            ("Phone", "NVARCHAR(24)"),
            ("Email", "NVARCHAR(60)"),
            ("SupportRepId", "INTEGER FK -> Employee.EmployeeId"),
        ],
        "relationships": [
            "1-to-many Invoice (via Invoice.CustomerId)",
            "many-to-1 Employee (via SupportRepId)",
        ],
    },
    "Invoice": {
        "columns": [
            ("InvoiceId", "INTEGER PK"),
            ("CustomerId", "INTEGER FK -> Customer.CustomerId"),
            ("InvoiceDate", "DATETIME (YYYY-MM-DD HH:MM:SS)"),
            ("BillingAddress", "NVARCHAR(70)"),
            ("BillingCity", "NVARCHAR(40)"),
            ("BillingState", "NVARCHAR(40)"),
            ("BillingCountry", "NVARCHAR(40)"),
            ("BillingPostalCode", "NVARCHAR(10)"),
            ("Total", "NUMERIC(10,2) (total revenue/amount for invoice)"),
        ],
        "relationships": [
            "many-to-1 Customer (via CustomerId)",
            "1-to-many InvoiceLine (via InvoiceLine.InvoiceId)",
        ],
    },
    "InvoiceLine": {
        "columns": [
            ("InvoiceLineId", "INTEGER PK"),
            ("InvoiceId", "INTEGER FK -> Invoice.InvoiceId"),
            ("TrackId", "INTEGER FK -> Track.TrackId"),
            ("UnitPrice", "NUMERIC(10,2)"),
            ("Quantity", "INTEGER"),
        ],
        "relationships": [
            "many-to-1 Invoice (via InvoiceId)",
            "many-to-1 Track (via TrackId)",
        ],
    },
    "Employee": {
        "columns": [
            ("EmployeeId", "INTEGER PK"),
            ("LastName", "NVARCHAR(20)"),
            ("FirstName", "NVARCHAR(20)"),
            ("Title", "NVARCHAR(30) (e.g. Sales Manager, Sales Support Agent)"),
            ("ReportsTo", "INTEGER FK -> Employee.EmployeeId"),
            ("BirthDate", "DATETIME"),
            ("HireDate", "DATETIME"),
            ("City", "NVARCHAR(40)"),
            ("Country", "NVARCHAR(40)"),
            ("Email", "NVARCHAR(60)"),
        ],
        "relationships": [
            "1-to-many Customer (via Customer.SupportRepId)",
            "self-referential hierarchy (via ReportsTo)",
        ],
    },
    "Track": {
        "columns": [
            ("TrackId", "INTEGER PK"),
            ("Name", "NVARCHAR(200) (song/track title)"),
            ("AlbumId", "INTEGER FK -> Album.AlbumId"),
            ("MediaTypeId", "INTEGER FK -> MediaType.MediaTypeId"),
            ("GenreId", "INTEGER FK -> Genre.GenreId"),
            ("Composer", "NVARCHAR(220)"),
            ("Milliseconds", "INTEGER (duration)"),
            ("Bytes", "INTEGER (file size)"),
            ("UnitPrice", "NUMERIC(10,2)"),
        ],
        "relationships": [
            "many-to-1 Album (via AlbumId)",
            "many-to-1 Genre (via GenreId)",
            "many-to-1 MediaType (via MediaTypeId)",
            "1-to-many InvoiceLine (via InvoiceLine.TrackId)",
        ],
    },
    "Album": {
        "columns": [
            ("AlbumId", "INTEGER PK"),
            ("Title", "NVARCHAR(160)"),
            ("ArtistId", "INTEGER FK -> Artist.ArtistId"),
        ],
        "relationships": [
            "many-to-1 Artist (via ArtistId)",
            "1-to-many Track (via Track.AlbumId)",
        ],
    },
    "Artist": {
        "columns": [
            ("ArtistId", "INTEGER PK"),
            ("Name", "NVARCHAR(120)"),
        ],
        "relationships": ["1-to-many Album (via Album.ArtistId)"],
    },
    "Genre": {
        "columns": [
            ("GenreId", "INTEGER PK"),
            ("Name", "NVARCHAR(120) (e.g. Rock, Jazz, Metal)"),
        ],
        "relationships": ["1-to-many Track (via Track.GenreId)"],
    },
    "MediaType": {
        "columns": [
            ("MediaTypeId", "INTEGER PK"),
            ("Name", "NVARCHAR(120) (e.g. MPEG audio file)"),
        ],
        "relationships": ["1-to-many Track (via Track.MediaTypeId)"],
    },
}

# Domain vocabulary of real business terms supported by Chinook
RECOGNIZED_TERMS = {
    "customer", "customers", "client", "clients", "company", "companies",
    "invoice", "invoices", "sales", "revenue", "spend", "spent", "total", "billing",
    "employee", "employees", "staff", "support", "rep", "reps", "title", "hire", "hired",
    "track", "tracks", "song", "songs", "music", "audio", "artist", "artists", "band", "bands",
    "album", "albums", "genre", "genres", "rock", "jazz", "metal", "media", "format",
    "country", "countries", "city", "cities", "unitprice", "price", "quantity", "unit", "units",
    "duration", "milliseconds", "bytes", "line", "items", "item"
}

# Terms that are clearly OUT-OF-SCOPE for our structured database
UNSUPPORTED_DOMAINS = [
    (r"\b(weather|temperature|forecast|rain)\b", "weather and atmospheric conditions"),
    (r"\b(stock\s+price|ticker|nasdaq|dow jones|s&p|share price)\b", "external stock market ticker data"),
    (r"\b(password|wifi|credential|api key|secret|credit card|card number|bank account|ssn|pin)\b", "internal security credentials and payment secrets"),
    (r"\b(cafeteria|lunch|menu|food|canteen)\b", "company cafeteria and dining information"),
    (r"\b(policy|handbook|posh|maternity leave|parental leave|dress code|complaint)\b", "unstructured HR policy documents (owned by Knowledge Service /search)"),
    (r"\b(medical|doctor|diagnosis|prescription|patient|health insurance claim)\b", "personal healthcare records and insurance claims"),
    (r"\b(box office|movie ticket|hollywood)\b", "cinema box office records"),
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
            "### DATABASE SCHEMA (SQLite - Chinook Real Enterprise Database):",
            "You have read-only access to a real relational enterprise database with 11 tables:\n",
        ]

        for table_name, meta in SCHEMA_METADATA.items():
            col_strs = [f"{col_name} ({col_type})" for col_name, col_type in meta["columns"]]
            lines.append(f"• **{table_name}**:")
            lines.append(f"  Columns: {', '.join(col_strs)}")
            lines.append(f"  FK / Links: {'; '.join(meta['relationships'])}\n")

        lines.extend([
            "### BUSINESS RULES:",
            "- Total Revenue = `SUM(Invoice.Total)`",
            "- Customer full name = `FirstName || ' ' || LastName`",
            "- Support / Sales Rep = `Employee` linked via `Customer.SupportRepId = Employee.EmployeeId`",
            "- Track Sales = `InvoiceLine` joined with `Track`",
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
            if not has_relevant_concept:
                return False, "The question asks for concepts or entities that do not exist in the enterprise database schema."

        return True, None
