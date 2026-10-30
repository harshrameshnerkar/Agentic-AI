SYSTEM_SQL_PROMPT = """Translate the business question into a valid SQLite SELECT query for the Northwind database.

{schema_context}

Rules:
1. Generate only SQLite SELECT queries.
2. If the question cannot be answered using the schema, respond with:
   UNANSWERABLE: <reason>
3. Never generate DROP, DELETE, UPDATE, INSERT, ALTER, CREATE, or ATTACH statements.
4. Output only the raw SQL query without markdown fences or extra text.
"""

FEW_SHOT_EXAMPLES = [
    {
        "question": "Show all product names and their corresponding prices.",
        "sql": "SELECT ProductName, Price FROM Products;",
    },
    {
        "question": "Find the total number of customers registered from Germany.",
        "sql": "SELECT COUNT(*) FROM Customers WHERE Country = 'Germany';",
    },
    {
        "question": "List the unique countries where our suppliers are located.",
        "sql": "SELECT DISTINCT Country FROM Suppliers;",
    },
    {
        "question": "Show the first name and last name of all employees.",
        "sql": "SELECT FirstName, LastName FROM Employees;",
    },
    {
        "question": "Get the maximum price among all products.",
        "sql": "SELECT MAX(Price) FROM Products;",
    },
    {
        "question": "Show all product names along with their category name.",
        "sql": "SELECT p.ProductName, c.CategoryName FROM Products p JOIN Categories c ON p.CategoryID = c.CategoryID;",
    },
    {
        "question": "What was the closing stock price of Apple on NASDAQ yesterday?",
        "sql": "UNANSWERABLE: Stock market ticker data is not in the database.",
    },
]

SELF_CORRECTION_PROMPT_TEMPLATE = """Fix the failed SQLite query using the schema and database error below.

Schema:
{schema_context}

Question:
{question}

Failed Query:
{failed_sql}

Database Error:
{error_message}

Return only the corrected SQLite SELECT query.
"""
