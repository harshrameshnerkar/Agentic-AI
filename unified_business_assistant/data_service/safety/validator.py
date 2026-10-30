import re
from typing import Optional, Tuple
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
    "EXECUTE", "LOAD_EXTENSION", "GRANT", "REVOKE",
}


class SQLSafetyValidator:
    @classmethod
    def clean_query(cls, sql: str) -> str:
        cleaned = sql.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:sql)?\n?", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\n?```$", "", cleaned).strip()
        return cleaned

    @classmethod
    def validate(cls, sql: str, dialect: str = "sqlite") -> Tuple[bool, str, Optional[str]]:
        cleaned = cls.clean_query(sql)
        if not cleaned:
            raise SQLSyntaxValidationException("Empty SQL query string provided.")

        tokens = set(re.findall(r"\b[A-Z_]+\b", cleaned.upper()))
        found_forbidden = tokens.intersection(FORBIDDEN_KEYWORDS)
        if found_forbidden:
            for kw in found_forbidden:
                if re.search(rf"(?:^|;\s*)\b{kw}\b", cleaned, re.IGNORECASE):
                    raise DestructiveSQLBlockedException(operation=kw, query=cleaned)

        try:
            parsed_statements = sqlglot.parse(cleaned, read=dialect)
        except Exception:
            try:
                parsed_statements = sqlglot.parse(cleaned)
            except Exception as e2:
                raise SQLSyntaxValidationException(f"Syntax error: {e2}")

        parsed_statements = [s for s in parsed_statements if s is not None]
        if len(parsed_statements) == 0:
            raise SQLSyntaxValidationException("No valid SQL statement parsed.")

        if len(parsed_statements) > 1:
            for st in parsed_statements:
                for kw in FORBIDDEN_KEYWORDS:
                    if st.find(getattr(exp, kw.capitalize(), None)):
                        raise DestructiveSQLBlockedException(operation=kw, query=cleaned)
            raise MultipleStatementsBlockedException(count=len(parsed_statements))

        stmt = parsed_statements[0]

        if not isinstance(stmt, (exp.Select, exp.Union)):
            for ast_type in DESTRUCTIVE_AST_TYPES:
                if stmt.find(ast_type):
                    op_name = ast_type.__name__.replace("Table", "").upper()
                    raise DestructiveSQLBlockedException(operation=op_name, query=cleaned)
            raise InvalidQueryTypeException(query_type=type(stmt).__name__)

        for ast_type in DESTRUCTIVE_AST_TYPES:
            if stmt.find(ast_type):
                op_name = ast_type.__name__.replace("Table", "").upper()
                raise DestructiveSQLBlockedException(operation=op_name, query=cleaned)

        for func in stmt.find_all(exp.Anonymous):
            if func.name.upper() == "LOAD_EXTENSION":
                raise DestructiveSQLBlockedException(operation="LOAD_EXTENSION", query=cleaned)

        return True, stmt.sql(dialect=dialect), None
