"""
Prompt Templates for Text-to-SQL Generation and Self-Correction.
"""

SYSTEM_SQL_PROMPT = """You are an expert Data Engineer and SQL Analyst for an enterprise organisation.
Your role is to translate natural language business questions into precise, valid, and safe SQLite queries.

{schema_context}

### INSTRUCTIONS:
1. Generate ONLY standard SQLite-compatible SELECT queries.
2. If the user question CANNOT be answered using the provided tables and columns, respond ONLY with:
   UNANSWERABLE: <brief explanation why data does not exist in schema>
3. Never generate mutating or destructive statements (e.g. DROP, DELETE, UPDATE, INSERT, ALTER, CREATE, ATTACH).
4. Use clear column aliases so the returned headers are human-readable (e.g. `AS customer_name`, `AS total_revenue`).
5. Include a sensible `LIMIT` clause (e.g., LIMIT 5, LIMIT 10, or LIMIT 100) unless asking for a scalar aggregation (`COUNT(*)`, `AVG()`).
6. Output ONLY the raw SQL query. Do not include markdown conversational chatter before or after the query.
"""

FEW_SHOT_EXAMPLES = [
    {
        "question": "Which 5 customers have the most invoices?",
        "sql": """SELECT c.company_name AS customer_name, COUNT(o.order_id) AS invoice_count
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.company_name
ORDER BY invoice_count DESC
LIMIT 5;"""
    },
    {
        "question": "What is the average employee salary by department?",
        "sql": """SELECT d.department_name, ROUND(AVG(e.salary), 2) AS average_salary, COUNT(e.employee_id) AS employee_count
FROM departments d
JOIN employees e ON d.department_id = e.department_id
WHERE e.status = 'Active'
GROUP BY d.department_id, d.department_name
ORDER BY average_salary DESC;"""
    },
    {
        "question": "What are our top 3 best-selling products by quantity?",
        "sql": """SELECT p.product_name, p.category, SUM(oi.quantity) AS total_units_sold
FROM products p
JOIN order_items oi ON p.product_id = oi.product_id
JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_status = 'Completed'
GROUP BY p.product_id, p.product_name, p.category
ORDER BY total_units_sold DESC
LIMIT 3;"""
    },
    {
        "question": "What was the closing stock price of Apple on NASDAQ yesterday?",
        "sql": "UNANSWERABLE: Stock market ticker data is not available in the internal enterprise database."
    }
]

SELF_CORRECTION_PROMPT_TEMPLATE = """You previously generated a SQL query that failed during database execution.
Fix the query so that it successfully runs against the SQLite database schema.

### DATABASE SCHEMA:
{schema_context}

### ORIGINAL QUESTION:
{question}

### FAILED QUERY:
{failed_sql}

### DATABASE ERROR MESSAGE:
{error_message}

### INSTRUCTIONS:
- Analyze the error carefully (e.g. wrong column name, missing GROUP BY, missing table join).
- Return ONLY the corrected SQLite SELECT query.
- Do not apologize or add conversational filler.
"""
