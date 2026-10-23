"""
AST-Based SQL Safety Validator for Role B (Data Service).

Guarantees that NO destructive, mutating, or multi-statement query can ever
reach the database executor. Validation occurs ENTIRELY BEFORE EXECUTION.
"""
import re
from typing import List, Optional, Tuple
import sqlglot
from sqlglot import exp

from safety.errors import (
    DestructiveSQLBlockedException,
    InvalidQueryTypeException,
    MultipleStatementsBlockedException,
    SQLSyntaxValidationException,
)

DESTRUCTIVE_AST_TYPES = (
    exp.Drop,
    exp.Delete,
    exp.Update,
    exp.Insert,
    exp.Create,
    exp.Alter,
    exp.Command,
    exp.TruncateTable,
)

FORBIDDEN_KEYWORDS = {
    "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE",
    "TRUNCATE", "REPLACE", "ATTACH", "DETACH", "PRAGMA", "EXEC",
    "EXECUTE", "LOAD_EXTENSION", "GRANT", "REVOKE"
}


class SQLSafetyValidator:
    """Validates SQL queries against AST, expression type, and keyword safety policies."""

    @classmethod
    def clean_query(cls, sql: str) -> str:
        """Removes trailing semicolons, markdown fences, and excessive whitespace."""
        cleaned = sql.strip()
        # Remove markdown code blocks if the LLM outputted them
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:sql)?\n?", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\n?```$", "", cleaned)
            cleaned = cleaned.strip()
        return cleaned

    @classmethod
    def validate(cls, sql: str, dialect: str = "sqlite") -> Tuple[bool, str, Optional[str]]:
        """
        Validates the SQL query before execution.

        Returns:
            (is_valid, cleaned_sql, error_message)
        Raises:
            DestructiveSQLBlockedException: if any mutation or destructive AST/keyword is found.
            MultipleStatementsBlockedException: if multiple queries are chained.
            InvalidQueryTypeException: if query is not a read-only SELECT.
            SQLSyntaxValidationException: if query cannot be parsed.
        """
        cleaned = cls.clean_query(sql)

        if not cleaned:
            raise SQLSyntaxValidationException("Empty SQL query string provided.")

        # 1. Fast Lexical Check for immediate destructive tokens outside strings
        # Tokenize roughly on word boundaries
        tokens = set(re.findall(r"\b[A-Z_]+\b", cleaned.upper()))
        found_forbidden = tokens.intersection(FORBIDDEN_KEYWORDS)
        if found_forbidden:
            # Check if any forbidden keyword appears in an active statement role
            for kw in found_forbidden:
                # If query starts with forbidden keyword or has '; <KW>'
                if re.search(rf"(?:^|;\s*)\b{kw}\b", cleaned, re.IGNORECASE):
                    raise DestructiveSQLBlockedException(operation=kw, query=cleaned)

        # 2. Multi-Statement Detection via AST Parsing
        try:
            parsed_statements = sqlglot.parse(cleaned, read=dialect)
        except Exception as e:
            # Fallback parsing with generic dialect if sqlite specific parse fails
            try:
                parsed_statements = sqlglot.parse(cleaned)
            except Exception as e2:
                raise SQLSyntaxValidationException(f"Syntax error: {str(e2)}")

        # Remove None or empty statement ASTs
        parsed_statements = [s for s in parsed_statements if s is not None]

        if len(parsed_statements) == 0:
            raise SQLSyntaxValidationException("No valid SQL statement parsed.")

        if len(parsed_statements) > 1:
            # Check if any subsequent statement is destructive
            for st in parsed_statements:
                for kw in FORBIDDEN_KEYWORDS:
                    if st.find(getattr(exp, kw.capitalize(), None)):
                        raise DestructiveSQLBlockedException(operation=kw, query=cleaned)
            raise MultipleStatementsBlockedException(count=len(parsed_statements))

        stmt = parsed_statements[0]

        # 3. Check AST Expression Hierarchy
        # Root expression MUST be exp.Select or exp.Union
        if not isinstance(stmt, (exp.Select, exp.Union)):
            # Find specific destructive node type if present
            for ast_type in DESTRUCTIVE_AST_TYPES:
                if stmt.find(ast_type):
                    op_name = ast_type.__name__.replace("Table", "").upper()
                    raise DestructiveSQLBlockedException(operation=op_name, query=cleaned)
            raise InvalidQueryTypeException(query_type=type(stmt).__name__)

        # 4. Deep Inspection of Sub-Expressions (e.g. nested subqueries attempting mutations)
        for ast_type in DESTRUCTIVE_AST_TYPES:
            found_node = stmt.find(ast_type)
            if found_node:
                op_name = ast_type.__name__.replace("Table", "").upper()
                raise DestructiveSQLBlockedException(operation=op_name, query=cleaned)

        # 5. Check for dangerous function calls (e.g. SQLite load_extension)
        for func in stmt.find_all(exp.Anonymous):
            if func.name.upper() in {"LOAD_EXTENSION", "CHAR", "HEX"}:
                if func.name.upper() == "LOAD_EXTENSION":
                    raise DestructiveSQLBlockedException(operation="LOAD_EXTENSION", query=cleaned)

        # Generate canonical standard SQL without trailing semicolon for execution
        canonical_sql = stmt.sql(dialect=dialect)
        return True, canonical_sql, None
