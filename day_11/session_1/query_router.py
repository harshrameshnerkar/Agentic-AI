"""
Query Router & Self-Querying Engine for Day 11 Session 1.
Implements:
1. Multi-Way Routing:
   - VECTOR_SEARCH: Unstructured conceptual knowledge (policies, architecture, guides)
   - SQL_DATABASE: Tabular aggregations, metrics, counts, exact relational filters
   - NO_RETRIEVAL: Conversational greetings, pure math, general programming/logic
   - MULTI_HOP: Composite queries requiring both vector knowledge and SQL tabular data
2. Self-Querying with Metadata Filters:
   - Extracts structured attributes: department, year, category
   - Cleans semantic search query for improved retrieval recall
"""

import re
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class RoutePath(str, Enum):
    VECTOR_SEARCH = "vector_search"
    SQL_DATABASE = "sql_database"
    NO_RETRIEVAL = "no_retrieval"
    MULTI_HOP = "multi_hop"


class RoutingDecision(BaseModel):
    route: RoutePath
    confidence: float
    reasoning: str
    metadata_filters: Dict[str, Any] = Field(default_factory=dict)
    clean_query: str
    suggested_sql: Optional[str] = None


class AdaptiveQueryRouter:
    """Intelligent router that chooses between Vector Search, SQL, No-Retrieval, and Multi-Hop."""

    def __init__(self):
        # Keywords indicating tabular / aggregation SQL intent
        self.sql_indicators = [
            "how many", "count", "total", "sum", "average", "avg", "highest", "lowest",
            "maximum", "minimum", "salary", "salaries", "revenue", "stock", "quantity",
            "inventory", "orders", "table", "rows", "database", "units in stock",
            "pending orders", "completed orders", "cancelled orders", "hired in"
        ]

        # Keywords indicating unstructured semantic vector search
        self.vector_indicators = [
            "policy", "guideline", "standard", "procedure", "blueprint", "architecture",
            "how do i", "how to", "setup guide", "instructions", "rto", "rpo", "soc2",
            "mfa", "stipend", "remote work", "refund rule", "cancellation fee", "specs"
        ]

        # Keywords indicating pure conversational / chitchat / parametric math
        self.no_retrieval_indicators = [
            "hello", "hi", "hey", "who are you", "what is your name", "good morning",
            "thank you", "thanks", "calculate", "what is 2 + 2", "write a python",
            "reverse a string", "fibonacci", "tell me a joke"
        ]

    def _extract_metadata_filters(self, query: str) -> Dict[str, Any]:
        """Self-querying: Extracts structured metadata filters from natural language."""
        filters: Dict[str, Any] = {}
        q_lower = query.lower()

        # Department extraction
        departments = ["engineering", "hr", "security", "finance", "support", "sales"]
        for dept in departments:
            if re.search(rf"\b{dept}\b", q_lower):
                filters["department"] = dept.capitalize() if dept != "hr" else "HR"
                break

        # Year extraction
        year_match = re.search(r"\b(202[4-6])\b", query)
        if year_match:
            filters["year"] = int(year_match.group(1))

        # Category extraction
        if "policy" in q_lower or "guideline" in q_lower:
            filters["category"] = "Policy"
        elif "architecture" in q_lower or "blueprint" in q_lower:
            filters["category"] = "Architecture"
        elif "security" in q_lower or "compliance" in q_lower or "soc2" in q_lower:
            filters["category"] = "Security_Standard"
        elif "guide" in q_lower or "setup" in q_lower:
            filters["category"] = "Customer_Guide"

        return filters

    def _generate_sql_for_intent(self, query: str) -> Optional[str]:
        """Translates natural language analytical queries to SQL templates."""
        q_lower = query.lower()

        if "how many orders" in q_lower or "count of orders" in q_lower:
            if "completed" in q_lower:
                return "SELECT COUNT(*) as count FROM orders WHERE status = 'completed';"
            elif "pending" in q_lower:
                return "SELECT COUNT(*) as count FROM orders WHERE status = 'pending';"
            elif "refunded" in q_lower:
                return "SELECT COUNT(*) as count FROM orders WHERE status = 'refunded';"
            return "SELECT COUNT(*) as total_orders FROM orders;"

        if "total revenue" in q_lower or "sum of completed" in q_lower or "total amount" in q_lower:
            return "SELECT SUM(amount) as total_revenue FROM orders WHERE status = 'completed';"

        if "average salary" in q_lower or "avg salary" in q_lower:
            if "engineering" in q_lower:
                return "SELECT AVG(salary) as avg_salary FROM employees WHERE department = 'Engineering';"
            return "SELECT AVG(salary) as avg_company_salary FROM employees;"

        if "highest salary" in q_lower or "highest paid" in q_lower:
            return "SELECT name, title, salary FROM employees ORDER BY salary DESC LIMIT 1;"

        if "inventory" in q_lower or "stock" in q_lower:
            if "gpu" in q_lower or "a100" in q_lower:
                return "SELECT product_name, stock_quantity, unit_price FROM inventory WHERE product_name LIKE '%GPU%';"
            if "cloud server" in q_lower:
                return "SELECT product_name, stock_quantity, unit_price FROM inventory WHERE product_name LIKE '%Cloud Server%';"
            return "SELECT product_name, stock_quantity, warehouse_location FROM inventory ORDER BY stock_quantity ASC;"

        return None

    def route_query(self, query: str) -> RoutingDecision:
        """Classifies query into RoutePath with metadata extraction and confidence scoring."""
        q_clean = query.strip()
        q_lower = q_clean.lower()

        # 1. Check for Multi-Hop (Both Vector and SQL indicators present)
        has_vector = any(v in q_lower for v in self.vector_indicators)
        has_sql = any(s in q_lower for s in self.sql_indicators)

        if has_vector and has_sql:
            filters = self._extract_metadata_filters(q_clean)
            sql = self._generate_sql_for_intent(q_clean)
            return RoutingDecision(
                route=RoutePath.MULTI_HOP,
                confidence=0.92,
                reasoning="Query requires both unstructured policy/blueprint knowledge and structured SQL aggregation.",
                metadata_filters=filters,
                clean_query=q_clean,
                suggested_sql=sql,
            )

        # 2. Check for No-Retrieval (Chitchat, greetings, arithmetic, code syntax)
        is_math = bool(re.search(r"\b(\d+\s*[\+\-\*\/]\s*\d+)\b", q_clean))
        is_greeting = any(g in q_lower for g in ["hello", "hi", "hey", "who are you", "good morning", "thank you", "thanks"])
        is_generic_coding = any(c in q_lower for c in ["write a python", "reverse a string", "fibonacci", "what is a tuple", "slice notation", "python code"])

        # Enterprise document indicators that genuinely require vector store retrieval
        has_doc_indicators = any(v in q_lower for v in [
            "policy", "guideline", "standard", "procedure", "blueprint", "architecture",
            "setup guide", "rto", "rpo", "soc2", "mfa", "stipend", "remote work",
            "refund rule", "cancellation fee", "specs", "sla"
        ])

        if (is_greeting or is_math or is_generic_coding) and not has_doc_indicators and not has_sql:
            return RoutingDecision(
                route=RoutePath.NO_RETRIEVAL,
                confidence=0.98,
                reasoning="Query is conversational, arithmetic, or general parametric knowledge that does not require external retrieval.",
                metadata_filters={},
                clean_query=q_clean,
            )

        # 3. Check for SQL Database
        if has_sql and not has_vector:
            sql = self._generate_sql_for_intent(q_clean)
            return RoutingDecision(
                route=RoutePath.SQL_DATABASE,
                confidence=0.95,
                reasoning="Query targets structured relational records (aggregations, counts, exact tabular filters).",
                metadata_filters={},
                clean_query=q_clean,
                suggested_sql=sql or "SELECT * FROM orders LIMIT 5;",
            )

        # 4. Check for Vector Search (Default to Vector for substantive knowledge queries)
        filters = self._extract_metadata_filters(q_clean)
        return RoutingDecision(
            route=RoutePath.VECTOR_SEARCH,
            confidence=0.88 if has_vector else 0.75,
            reasoning="Query targets unstructured conceptual knowledge, operational procedures, or enterprise policies.",
            metadata_filters=filters,
            clean_query=q_clean,
        )


# Singleton router
query_router = AdaptiveQueryRouter()
