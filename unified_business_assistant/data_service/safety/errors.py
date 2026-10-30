class SQLSecurityException(Exception):
    pass


class DestructiveSQLBlockedException(SQLSecurityException):
    def __init__(self, operation: str, query: str):
        self.operation = operation.upper()
        self.query = query
        super().__init__(
            f"SECURITY BLOCK [Validation Phase]: Destructive operation '{self.operation}' is prohibited. "
            f"Query execution aborted before touching the database."
        )


class MultipleStatementsBlockedException(SQLSecurityException):
    def __init__(self, count: int):
        super().__init__(
            f"SECURITY BLOCK [Validation Phase]: Multiple statements detected ({count} found). "
            f"Only single read-only SELECT statements are permitted."
        )


class InvalidQueryTypeException(SQLSecurityException):
    def __init__(self, query_type: str):
        super().__init__(
            f"SECURITY BLOCK [Validation Phase]: Forbidden query expression type '{query_type}'. "
            f"Only read-only SELECT queries are allowed."
        )


class SQLSyntaxValidationException(SQLSecurityException):
    def __init__(self, error_msg: str):
        super().__init__(f"VALIDATION ERROR: Failed to parse SQL query: {error_msg}")
