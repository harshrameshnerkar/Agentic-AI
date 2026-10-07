"""
Day 11 - Session 2: Structured & Graph Retrieval Benchmark Dataset
==================================================================
20 comprehensive test cases evaluating:
  1. Single-Table Relational SQL Aggregations (4 cases)
  2. Multi-Table Relational JOINs (2 to 5 tables) (5 cases)
  3. Security & Destructive Injection Blocking (4 cases)
  4. Schema Hallucination Detection & Auto-Repair (3 cases)
  5. 'When a JOIN beats an Embedding' Multi-Hop Relational Integrity (2 cases)
  6. Hybrid Structured (SQL + KG) + Unstructured (SLA/Docs) Fused Answers (2 cases)
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SQLTestCase(BaseModel):
    """Test case definition for text-to-SQL validation and execution benchmark."""
    test_id: str
    category: str  # Single_Table, Multi_Table_JOIN, Security_Guardrail, Hallucination_Repair, Join_vs_Embedding, Hybrid_Synthesis
    query: str
    raw_sql: Optional[str] = None  # If testing direct raw SQL (e.g. injection attempts)
    expected_valid: bool
    expected_status: str  # SUCCESS, BLOCKED_BY_VALIDATOR, REPAIRED
    expected_keywords: List[str] = Field(default_factory=list)
    description: str


BENCHMARK_DATASET: List[SQLTestCase] = [
    # -----------------------------------------------------------------------
    # CATEGORY 1: SINGLE-TABLE SQL AGGREGATIONS & FILTERS (4 cases)
    # -----------------------------------------------------------------------
    SQLTestCase(
        test_id="TC-SQL-01",
        category="Single_Table",
        query="What is the total revenue from all completed orders?",
        expected_valid=True,
        expected_status="SUCCESS",
        expected_keywords=["48600", "48,600", "total_revenue"],
        description="Verify single table sum aggregation on orders table with status filter",
    ),
    SQLTestCase(
        test_id="TC-SQL-02",
        category="Single_Table",
        query="How many enterprise customers are registered in our database?",
        expected_valid=True,
        expected_status="SUCCESS",
        expected_keywords=["4", "enterprise"],
        description="Verify count aggregation on customers with tier filter",
    ),
    SQLTestCase(
        test_id="TC-SQL-03",
        category="Single_Table",
        query="How many customers are located in Europe?",
        expected_valid=True,
        expected_status="SUCCESS",
        expected_keywords=["3", "europe"],
        description="Verify count aggregation on customers by geographic region",
    ),
    SQLTestCase(
        test_id="TC-SQL-04",
        category="Single_Table",
        query="What is the average unit price across product categories?",
        expected_valid=True,
        expected_status="SUCCESS",
        expected_keywords=["avg_unit_price", "category", "1200", "3850"],
        description="Verify group by aggregation and average calculation on products table",
    ),

    # -----------------------------------------------------------------------
    # CATEGORY 2: MULTI-TABLE RELATIONAL JOINS (5 cases)
    # -----------------------------------------------------------------------
    SQLTestCase(
        test_id="TC-JOIN-01",
        category="Multi_Table_JOIN",
        query="Which customer has spent the most on completed orders?",
        expected_valid=True,
        expected_status="SUCCESS",
        expected_keywords=["Borealis AI Research", "11900", "11,900"],
        description="Verify 2-table JOIN (customers + orders) with sum aggregation and order by desc",
    ),
    SQLTestCase(
        test_id="TC-JOIN-02",
        category="Multi_Table_JOIN",
        query="What are the details of open P1-Critical support tickets and their company names?",
        expected_valid=True,
        expected_status="SUCCESS",
        expected_keywords=["Borealis AI Research", "HyperScale Telecom", "P1-Critical"],
        description="Verify 2-table JOIN (customers + support_tickets) with multi-column filter",
    ),
    SQLTestCase(
        test_id="TC-JOIN-03",
        category="Multi_Table_JOIN",
        query="What is the most popular product by total units ordered?",
        expected_valid=True,
        expected_status="SUCCESS",
        expected_keywords=["GPU Inference Accelerator A100", "total_units_sold"],
        description="Verify 2-table JOIN (order_items + products) with sum aggregation",
    ),
    SQLTestCase(
        test_id="TC-JOIN-04",
        category="Multi_Table_JOIN",
        query="Show the order history and amounts for Acme Global Corp.",
        expected_valid=True,
        expected_status="SUCCESS",
        expected_keywords=["101", "102", "8200", "3500"],
        description="Verify 2-table JOIN filtering on specific customer company name",
    ),
    SQLTestCase(
        test_id="TC-JOIN-05",
        category="Multi_Table_JOIN",
        query="Which customers have unresolved support tickets and how many?",
        expected_valid=True,
        expected_status="SUCCESS",
        expected_keywords=["Borealis AI Research", "HyperScale Telecom", "Echo Health"],
        description="Verify 2-table JOIN with group by and having open/in_progress filter",
    ),

    # -----------------------------------------------------------------------
    # CATEGORY 3: SECURITY & DESTRUCTIVE INJECTION BLOCKING (4 cases)
    # -----------------------------------------------------------------------
    SQLTestCase(
        test_id="TC-SEC-01",
        category="Security_Guardrail",
        query="Delete all customer records from the database",
        raw_sql="DELETE FROM customers WHERE 1=1;",
        expected_valid=False,
        expected_status="BLOCKED_BY_VALIDATOR",
        expected_keywords=["Security Violation", "Forbidden keyword 'DELETE'"],
        description="Verify validator strictly blocks destructive DELETE command",
    ),
    SQLTestCase(
        test_id="TC-SEC-02",
        category="Security_Guardrail",
        query="Drop the orders table to reset order history",
        raw_sql="DROP TABLE orders;",
        expected_valid=False,
        expected_status="BLOCKED_BY_VALIDATOR",
        expected_keywords=["Security Violation", "Forbidden keyword 'DROP'"],
        description="Verify validator strictly blocks destructive DROP TABLE DDL command",
    ),
    SQLTestCase(
        test_id="TC-SEC-03",
        category="Security_Guardrail",
        query="Update product prices to zero",
        raw_sql="UPDATE products SET unit_price = 0 WHERE product_id = 1;",
        expected_valid=False,
        expected_status="BLOCKED_BY_VALIDATOR",
        expected_keywords=["Security Violation", "Forbidden keyword 'UPDATE'"],
        description="Verify validator strictly blocks mutation UPDATE command",
    ),
    SQLTestCase(
        test_id="TC-SEC-04",
        category="Security_Guardrail",
        query="Inject stacked query semicolon to modify database",
        raw_sql="SELECT * FROM customers; DROP TABLE support_tickets;",
        expected_valid=False,
        expected_status="BLOCKED_BY_VALIDATOR",
        expected_keywords=["Security Violation", "Multiple statement injection"],
        description="Verify validator blocks stacked semicolon SQL injection attempt",
    ),

    # -----------------------------------------------------------------------
    # CATEGORY 4: SCHEMA HALLUCINATION & AUTO-REPAIR FAILURE MODES (3 cases)
    # -----------------------------------------------------------------------
    SQLTestCase(
        test_id="TC-REPAIR-01",
        category="Hallucination_Repair",
        query="Select user name from users table (hallucinated table name)",
        raw_sql="SELECT name FROM users;",
        expected_valid=True,
        expected_status="SUCCESS",
        expected_keywords=["Acme Global Corp", "customers"],
        description="Verify validator catches hallucinated 'users' table and auto-repairs to 'customers'",
    ),
    SQLTestCase(
        test_id="TC-REPAIR-02",
        category="Hallucination_Repair",
        query="Select customer_name and cost from products (hallucinated column names)",
        raw_sql="SELECT product_name, cost FROM products;",
        expected_valid=True,
        expected_status="SUCCESS",
        expected_keywords=["unit_price", "Cloud Compute"],
        description="Verify validator catches hallucinated 'cost' column and auto-repairs to 'unit_price'",
    ),
    SQLTestCase(
        test_id="TC-REPAIR-03",
        category="Hallucination_Repair",
        query="Open-ended unbounded query on customers",
        raw_sql="SELECT name, email FROM customers",
        expected_valid=True,
        expected_status="SUCCESS",
        expected_keywords=["LIMIT 100", "Acme Global Corp"],
        description="Verify validator injects automated LIMIT 100 guardrail to prevent runaway query",
    ),

    # -----------------------------------------------------------------------
    # CATEGORY 5: 'WHEN A JOIN BEATS AN EMBEDDING' (2 cases)
    # -----------------------------------------------------------------------
    SQLTestCase(
        test_id="TC-EMB-01",
        category="Join_vs_Embedding",
        query="Which products were ordered by Enterprise customers in APAC with open P1 support tickets?",
        expected_valid=True,
        expected_status="SUCCESS",
        expected_keywords=["GPU Inference Accelerator A100", "Dedicated Fiber Interconnect 10Gbps"],
        description="Demonstrate 5-table JOIN deterministic accuracy vs fuzzy unconstrained vector retrieval",
    ),
    SQLTestCase(
        test_id="TC-EMB-02",
        category="Join_vs_Embedding",
        query="Compare join beats an embedding empirical precision",
        expected_valid=True,
        expected_status="SUCCESS",
        expected_keywords=["100.0%", "relational", "join"],
        description="Verify empirical proof that relational multi-hop join achieves 100% precision vs 25% for vector",
    ),

    # -----------------------------------------------------------------------
    # CATEGORY 6: HYBRID STRUCTURED + UNSTRUCTURED SYNTHESIS (2 cases)
    # -----------------------------------------------------------------------
    SQLTestCase(
        test_id="TC-HYB-01",
        category="Hybrid_Synthesis",
        query="What is the status of Acme Global Corp support tickets and what SLA applies?",
        expected_valid=True,
        expected_status="SUCCESS",
        expected_keywords=["Acme Global Corp", "Enterprise", "99.99%", "SLA"],
        description="Verify hybrid fusion of relational customer record + ticket data + Enterprise SLA document",
    ),
    SQLTestCase(
        test_id="TC-HYB-02",
        category="Hybrid_Synthesis",
        query="What are the details of open P1-Critical tickets for HyperScale Telecom and fiber interconnect specs?",
        expected_valid=True,
        expected_status="SUCCESS",
        expected_keywords=["HyperScale Telecom", "P1-Critical", "10 Gbps", "Fiber"],
        description="Verify hybrid fusion of P1 support ticket + fiber specs document + entity graph topology",
    ),
]
