"""
Day 11 - Session 01: Adaptive & Corrective RAG (CRAG)
Demonstrates:
1. Multi-way query routing (Vector vs SQL vs Direct vs Multi-Hop).
2. Self-querying with metadata filters.
3. Corrective RAG (CRAG) document grading and query rewrite loops.
4. Comparison against a naive always-retrieve baseline.
"""

from __future__ import annotations
import time
from dotenv import load_dotenv

load_dotenv()

from query_router import query_router
from adaptive_rag import adaptive_rag
from naive_rag import naive_rag
from benchmark import run_benchmark


def inspect_query(query: str):
    print(f"\nQuery: '{query}'")

    # 1. Routing
    decision = query_router.route_query(query)
    print(f"  Route: {decision.route.value.upper()} (Confidence: {decision.confidence:.2f})")
    if decision.metadata_filters:
        print(f"  Self-Query Filters: {decision.metadata_filters}")

    # 2. Adaptive RAG
    res = adaptive_rag.run(query)
    print(f"  Adaptive RAG: {res['latency_ms']:.1f}ms | Tokens: {res['tokens_used']}")
    print(f"  Answer: {res['final_answer'][:160]}...")

    # 3. Naive Baseline
    naive_res = naive_rag.run(query)
    print(f"  Naive RAG:    {naive_res['latency_ms']:.1f}ms | Docs: {naive_res['retrieved_doc_ids']}")


def main():
    print("Day 11 Session 01: Adaptive RAG Demonstration\n")

    demo_queries = [
        "What is our company's remote work stipend policy in HR?",
        "What is the total revenue from completed orders in the database?",
        "Good morning! Can you help me calculate 125 * 8?",
        "What are the RTO and RPO limits in our DR plan?",
    ]

    for q in demo_queries:
        inspect_query(q)

    print("\nRunning Adaptive RAG Benchmark...")
    run_benchmark()


if __name__ == "__main__":
    main()
