"""
Custom Exception Classes for Role B SQL Safety and Validation.
"""

class SQLSecurityException(Exception):
    """Base exception for all SQL safety and security violations."""
    pass


class DestructiveSQLBlockedException(SQLSecurityException):
    """
    Raised when an AST node or keyword corresponds to a destructive/mutating operation
    (e.g., DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE, ATTACH).
    Must be raised during the VALIDATION phase PRIOR to database execution.
    """
    def __init__(self, operation: str, query: str):
        self.operation = operation.upper()
        self.query = query
        super().__init__(
            f"SECURITY BLOCK [Validation Phase]: Destructive operation '{self.operation}' is strictly prohibited. "
            f"Query execution aborted before touching the database."
        )


class MultipleStatementsBlockedException(SQLSecurityException):
    """Raised when more than one SQL statement is chained (SQL injection vector)."""
    def __init__(self, count: int):
        super().__init__(
            f"SECURITY BLOCK [Validation Phase]: Multiple statements detected ({count} found). "
            f"Only single read-only SELECT statements are permitted."
        )


class InvalidQueryTypeException(SQLSecurityException):
    """Raised when the parsed AST is not a SELECT or UNION query."""
    def __init__(self, query_type: str):
        super().__init__(
            f"SECURITY BLOCK [Validation Phase]: Forbidden query expression type '{query_type}'. "
            f"Only read-only SELECT queries are allowed."
        )


class SQLSyntaxValidationException(SQLSecurityException):
    """Raised when the SQL query is unparseable or has syntax errors."""
    def __init__(self, error_msg: str):
        super().__init__(f"VALIDATION ERROR: Failed to parse SQL query: {error_msg}")
