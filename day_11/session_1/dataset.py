"""
Evaluation Dataset for Day 11 Session 1: Agentic & Adaptive RAG.
Contains 20 comprehensive test cases across 4 evaluation categories:
1. Unstructured Semantic Queries (Target: Vector Search)
2. Structured Relational & Tabular Aggregations (Target: SQL Database)
3. Parametric, Conversational & Math Queries (Target: No-Retrieval)
4. Multi-Hop Hybrid Queries (Target: Multi-Hop Fusion)
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class EvaluationTestCase:
    test_id: str
    category: str
    query: str
    expected_route: str
    expected_keywords: List[str] = field(default_factory=list)
    expected_filters: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


BENCHMARK_DATASET: List[EvaluationTestCase] = [
    # -----------------------------------------------------------------------
    # CATEGORY 1: UNSTRUCTURED SEMANTIC KNOWLEDGE (Vector Search) (6 cases)
    # -----------------------------------------------------------------------
    EvaluationTestCase(
        test_id="TC-VEC-01",
        category="Vector_Search",
        query="What is the customer refund policy and what fee is charged after 30 days?",
        expected_route="vector_search",
        expected_keywords=["DOC-POL-01", "30 days", "15%"],
        expected_filters={"category": "Policy"},
        description="Verify retrieval of refund policy and late cancellation fee",
    ),
    EvaluationTestCase(
        test_id="TC-VEC-02",
        category="Vector_Search",
        query="What is the HR policy regarding home office equipment stipend for remote employees?",
        expected_route="vector_search",
        expected_keywords=["DOC-POL-02", "$1,500", "remote"],
        expected_filters={"department": "HR", "category": "Policy"},
        description="Verify self-querying filter extraction for HR remote work policy",
    ),
    EvaluationTestCase(
        test_id="TC-VEC-03",
        category="Vector_Search",
        query="According to our engineering architecture blueprint, what proxy and failover system do we use?",
        expected_route="vector_search",
        expected_keywords=["DOC-ARCH-01", "patroni", "envoy"],
        expected_filters={"department": "Engineering", "category": "Architecture"},
        description="Verify engineering architecture blueprint retrieval with self-querying",
    ),
    EvaluationTestCase(
        test_id="TC-VEC-04",
        category="Vector_Search",
        query="What are our multi-cloud Disaster Recovery RTO and RPO SLA commitments for 2025?",
        expected_route="vector_search",
        expected_keywords=["DOC-ARCH-02", "30 minutes", "5 minutes"],
        expected_filters={"year": 2025, "category": "Architecture"},
        description="Verify self-querying extraction of year 2025 filter and DR metrics",
    ),
    EvaluationTestCase(
        test_id="TC-VEC-05",
        category="Vector_Search",
        query="What MFA authentication standard is mandated by our SOC2 security access control SOP?",
        expected_route="vector_search",
        expected_keywords=["DOC-SEC-01", "fido2", "mfa"],
        expected_filters={"category": "Security_Standard", "department": "Security"},
        description="Verify SOC2 security access control policy retrieval",
    ),
    EvaluationTestCase(
        test_id="TC-VEC-06",
        category="Vector_Search",
        query="What are the hardware specifications and provisioning time for Cloud Server Pro?",
        expected_route="vector_search",
        expected_keywords=["DOC-CUST-01", "16 vcpus", "64gb"],
        expected_filters={"category": "Customer_Guide"},
        description="Verify customer guide retrieval for Cloud Server Pro specifications",
    ),

    # -----------------------------------------------------------------------
    # CATEGORY 2: STRUCTURED RELATIONAL & TABULAR AGGREGATION (SQL) (6 cases)
    # -----------------------------------------------------------------------
    EvaluationTestCase(
        test_id="TC-SQL-01",
        category="SQL_Database",
        query="How many orders in our database are currently in 'completed' status?",
        expected_route="sql_database",
        expected_keywords=["5", "completed"],
        description="Verify SQL count aggregation on orders table with status filter",
    ),
    EvaluationTestCase(
        test_id="TC-SQL-02",
        category="SQL_Database",
        query="What is the total revenue sum from all completed orders?",
        expected_route="sql_database",
        expected_keywords=["19,100", "19100", "revenue"],
        description="Verify SQL sum aggregation on orders amount column",
    ),
    EvaluationTestCase(
        test_id="TC-SQL-03",
        category="SQL_Database",
        query="What is the average salary of employees working in the Engineering department?",
        expected_route="sql_database",
        expected_keywords=["171,666", "171666", "engineering"],
        description="Verify SQL average aggregation on employees table by department",
    ),
    EvaluationTestCase(
        test_id="TC-SQL-04",
        category="SQL_Database",
        query="How many orders are currently pending in the orders table?",
        expected_route="sql_database",
        expected_keywords=["3", "pending"],
        description="Verify SQL count of pending orders",
    ),
    EvaluationTestCase(
        test_id="TC-SQL-05",
        category="SQL_Database",
        query="What is the stock quantity of GPU Inference Node A100 units in inventory?",
        expected_route="sql_database",
        expected_keywords=["8", "gpu"],
        description="Verify SQL inventory stock lookup for GPU units",
    ),
    EvaluationTestCase(
        test_id="TC-SQL-06",
        category="SQL_Database",
        query="Who is the employee with the highest salary in our company database?",
        expected_route="sql_database",
        expected_keywords=["George Clark", "220,000", "220000"],
        description="Verify SQL order by limit 1 query on employees",
    ),

    # -----------------------------------------------------------------------
    # CATEGORY 3: NO-RETRIEVAL (Chitchat, Math, Logic, General Coding) (5 cases)
    # -----------------------------------------------------------------------
    EvaluationTestCase(
        test_id="TC-NORET-01",
        category="No_Retrieval",
        query="Hello, who are you and what systems can you help me with?",
        expected_route="no_retrieval",
        expected_keywords=["hello", "copilot", "assist"],
        description="Verify conversational greeting triggers zero retrieval overhead",
    ),
    EvaluationTestCase(
        test_id="TC-NORET-02",
        category="No_Retrieval",
        query="What is 45 * 12?",
        expected_route="no_retrieval",
        expected_keywords=["540"],
        description="Verify arithmetic calculation resolved without database or vector search",
    ),
    EvaluationTestCase(
        test_id="TC-NORET-03",
        category="No_Retrieval",
        query="How do I reverse a string in Python using slice notation?",
        expected_route="no_retrieval",
        expected_keywords=["::-1"],
        description="Verify standard programming syntax query does not retrieve external documents",
    ),
    EvaluationTestCase(
        test_id="TC-NORET-04",
        category="No_Retrieval",
        query="Good morning! Hope you are having a productive day.",
        expected_route="no_retrieval",
        expected_keywords=["hello", "good morning", "copilot"],
        description="Verify courteous chitchat bypasses retrieval",
    ),
    EvaluationTestCase(
        test_id="TC-NORET-05",
        category="No_Retrieval",
        query="What is 2 + 2?",
        expected_route="no_retrieval",
        expected_keywords=["4"],
        description="Verify basic math calculation triggers zero retrieval",
    ),

    # -----------------------------------------------------------------------
    # CATEGORY 4: MULTI-HOP RETRIEVAL (Vector Knowledge + Live SQL Data) (3 cases)
    # -----------------------------------------------------------------------
    EvaluationTestCase(
        test_id="TC-MHOP-01",
        category="Multi_Hop",
        query="What is our customer refund policy, and how many orders are currently in refunded status?",
        expected_route="multi_hop",
        expected_keywords=["DOC-POL-01", "30 days", "1", "refunded"],
        description="Verify multi-hop synthesis fusing policy RAG document with live SQL count",
    ),
    EvaluationTestCase(
        test_id="TC-MHOP-02",
        category="Multi_Hop",
        query="According to our remote work policy, what is the stipend, and how many employees work in Engineering?",
        expected_route="multi_hop",
        expected_keywords=["$1,500", "3", "engineering"],
        description="Verify multi-hop fusion of HR stipend policy and SQL department headcount",
    ),
    EvaluationTestCase(
        test_id="TC-MHOP-03",
        category="Multi_Hop",
        query="Check our Cloud Server Pro specs guide, and tell me the total inventory stock quantity available.",
        expected_route="multi_hop",
        expected_keywords=["16 vcpus", "45", "stock"],
        description="Verify multi-hop fusion of server specifications guide and SQL inventory stock",
    ),
]
