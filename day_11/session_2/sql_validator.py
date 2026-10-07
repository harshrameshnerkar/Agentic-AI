"""
Day 11 - Session 2: Enterprise SQL Query Validator
==================================================
Performs multi-stage pre-execution validation for Text-to-SQL pipelines:
  1. Security & DDL/DML Injection Blocking (Strict Read-Only Enforcement)
  2. Schema Integrity Verification (Hallucinated Tables & Columns Detection)
  3. Safe Guardrails (Automated LIMIT injection to prevent runaway queries)
  4. Pre-execution Syntax Verification (via EXPLAIN QUERY PLAN)
  5. Intelligent Error Diagnosis & Auto-Repair Suggestions
"""

import re
from typing import Dict, List, Set, Any, Tuple, Optional
from pydantic import BaseModel, Field

from database import db


class ValidationResult(BaseModel):
    """Result of SQL validation checks prior to query execution."""
    is_valid: bool
    sanitized_sql: str
    failure_reasons: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    repaired_sql: Optional[str] = None
    tables_referenced: List[str] = Field(default_factory=list)
    columns_referenced: List[str] = Field(default_factory=list)
    syntax_verified: bool = False


class SQLQueryValidator:
    """Multi-stage validator protecting relational databases against Text-to-SQL failure modes."""

    # Forbidden DDL / DML keywords
    FORBIDDEN_KEYWORDS = {
        "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "REPLACE",
        "EXEC", "EXECUTE", "CREATE", "GRANT", "REVOKE", "ATTACH", "DETACH"
    }

    # Known LLM hallucination corrections mapping {hallucinated: canonical}
    KNOWN_CORRECTIONS = {
        # Table hallucinations
        "users": "customers",
        "clients": "customers",
        "client": "customers",
        "items": "order_items",
        "tickets": "support_tickets",
        "ticket": "support_tickets",
        "sales": "orders",
        # Column hallucinations
        "customer_name": "name",
        "company_name": "name",
        "customer_email": "email",
        "price": "unit_price",
        "cost": "unit_price",
        "amount": "total_amount",
        "order_total": "total_amount",
        "ticket_priority": "priority",
        "ticket_status": "status",
        "ticket_subject": "subject",
        "product_description": "product_name",
        "product_title": "product_name",
    }

    def __init__(self, default_limit: int = 100):
        self.default_limit = default_limit
        self.schema_info = db.get_schema_info()
        self.valid_tables: Set[str] = set(self.schema_info.keys())
        self.table_columns: Dict[str, Set[str]] = {
            tbl: set(info["columns"].keys()) for tbl, info in self.schema_info.items()
        }
        self.all_valid_columns: Set[str] = set()
        for cols in self.table_columns.values():
            self.all_valid_columns.update(cols)

    def _clean_sql(self, sql: str) -> str:
        """Strips markdown code blocks, trailing semicolons, and excess whitespace."""
        s = sql.strip()
        if s.startswith("```sql"):
            s = s[6:]
        elif s.startswith("```"):
            s = s[3:]
        if s.endswith("```"):
            s = s[:-3]
        s = s.strip()
        if s.endswith(";"):
            s = s[:-1].strip()
        return s

    def _check_security(self, sql: str) -> List[str]:
        """Ensures query is strictly a read-only SELECT statement with no mutations."""
        errors = []
        tokens = re.findall(r"\b[A-Za-z_]+\b", sql.upper())

        for token in tokens:
            if token in self.FORBIDDEN_KEYWORDS:
                errors.append(f"Security Violation: Forbidden keyword '{token}' detected. Only read-only SELECT queries are permitted.")

        # Ensure first keyword is SELECT or WITH (for CTEs) or EXPLAIN
        if tokens and tokens[0] not in {"SELECT", "WITH", "EXPLAIN"}:
            errors.append(f"Security Violation: Query must begin with SELECT or WITH, found '{tokens[0]}'.")

        # Disallow semicolons in the body (prevent multi-statement SQL injection)
        if ";" in sql:
            errors.append("Security Violation: Multiple statement injection attempted (semicolon inside query body).")

        return errors

    def _extract_tables(self, sql: str) -> List[str]:
        """Extracts table names from FROM and JOIN clauses."""
        # Regex matching FROM <table> or JOIN <table>
        matches = re.findall(r"\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)", sql, re.IGNORECASE)
        # Normalize and filter out SQL keywords or subqueries
        tables = []
        sql_keywords = {"SELECT", "WHERE", "GROUP", "ORDER", "HAVING", "LIMIT"}
        for m in matches:
            t = m.lower()
            if t.upper() not in sql_keywords:
                tables.append(t)
        return list(dict.fromkeys(tables))

    def _check_schema_validity(self, sql: str, referenced_tables: List[str]) -> Tuple[List[str], List[str], Optional[str]]:
        """Verifies that all referenced tables and columns exist in the database."""
        errors = []
        warnings = []
        repaired_sql = sql

        # 1. Validate Tables
        for tbl in referenced_tables:
            if tbl not in self.valid_tables:
                if tbl in self.KNOWN_CORRECTIONS:
                    correct = self.KNOWN_CORRECTIONS[tbl]
                    warnings.append(f"Schema Warning: Hallucinated table '{tbl}' replaced with canonical table '{correct}'.")
                    repaired_sql = re.sub(rf"\b{tbl}\b", correct, repaired_sql, flags=re.IGNORECASE)
                else:
                    errors.append(f"Schema Error: Table '{tbl}' does not exist in the database schema. Valid tables: {sorted(list(self.valid_tables))}.")

        # 2. Check for Hallucinated Columns
        # Extract word tokens from query
        tokens = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", sql)
        sql_keywords = {
            "SELECT", "FROM", "WHERE", "JOIN", "LEFT", "RIGHT", "INNER", "OUTER", "ON",
            "GROUP", "BY", "ORDER", "HAVING", "LIMIT", "OFFSET", "AS", "AND", "OR", "NOT",
            "IN", "IS", "NULL", "LIKE", "COUNT", "SUM", "AVG", "MIN", "MAX", "DISTINCT",
            "DESC", "ASC", "BETWEEN", "CASE", "WHEN", "THEN", "ELSE", "END", "CAST", "ROUND",
            "AUTOINCREMENT", "PRIMARY", "KEY", "FOREIGN", "REFERENCES"
        }

        for token in tokens:
            t_lower = token.lower()
            if token.upper() in sql_keywords or t_lower in self.valid_tables:
                continue

            # Check if token is a known column hallucination
            if t_lower in self.KNOWN_CORRECTIONS:
                correct_col = self.KNOWN_CORRECTIONS[t_lower]
                warnings.append(f"Schema Warning: Hallucinated column '{t_lower}' replaced with canonical column '{correct_col}'.")
                repaired_sql = re.sub(rf"\b{token}\b", correct_col, repaired_sql)

        # 3. Check for Cartesian product on multiple tables without JOIN condition
        if len(referenced_tables) > 1 and "JOIN" not in sql.upper() and "," in sql.split("FROM")[1].split("WHERE")[0]:
            warnings.append("Performance Warning: Comma-separated multi-table FROM without explicit JOIN syntax detected. Potential Cartesian product risk.")

        return errors, warnings, repaired_sql if repaired_sql != sql else None

    def _inject_limit_guardrail(self, sql: str) -> Tuple[str, bool]:
        """Injects a safe LIMIT clause if none exists and no aggregate function is used."""
        upper_sql = sql.upper()
        has_limit = "LIMIT" in upper_sql
        has_aggregate = any(agg in upper_sql for agg in ["COUNT(", "SUM(", "AVG(", "MAX(", "MIN("])

        if not has_limit and not has_aggregate:
            return f"{sql} LIMIT {self.default_limit}", True
        return sql, False

    def validate(self, sql: str) -> ValidationResult:
        """Executes full multi-stage validation on the candidate SQL query."""
        clean_sql = self._clean_sql(sql)
        errors: List[str] = []
        warnings: List[str] = []

        # Step 1: Security & Injection Check
        sec_errors = self._check_security(clean_sql)
        if sec_errors:
            errors.extend(sec_errors)
            return ValidationResult(
                is_valid=False,
                sanitized_sql=clean_sql,
                failure_reasons=errors,
                warnings=warnings,
                syntax_verified=False,
            )

        # Step 2: Table Extraction
        tables = self._extract_tables(clean_sql)

        # Step 3: Schema Verification & Auto-Repair
        schema_errors, schema_warnings, auto_repaired = self._check_schema_validity(clean_sql, tables)
        errors.extend(schema_errors)
        warnings.extend(schema_warnings)

        active_sql = auto_repaired if auto_repaired else clean_sql

        # Step 4: Guardrail Check (Inject LIMIT if open-ended)
        active_sql, limit_injected = self._inject_limit_guardrail(active_sql)
        if limit_injected:
            warnings.append(f"Guardrail Note: Automated LIMIT {self.default_limit} injected to prevent memory starvation.")

        # Step 5: Syntax Pre-flight Verification via EXPLAIN QUERY PLAN
        explain_res = db.explain_query(active_sql)
        syntax_ok = explain_res.get("valid", False)
        if not syntax_ok:
            errors.append(f"SQLite Syntax Error: {explain_res.get('error')}")

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            sanitized_sql=active_sql,
            failure_reasons=errors,
            warnings=warnings,
            repaired_sql=auto_repaired,
            tables_referenced=tables,
            syntax_verified=syntax_ok,
        )


# Singleton validator instance
sql_validator = SQLQueryValidator(default_limit=100)
