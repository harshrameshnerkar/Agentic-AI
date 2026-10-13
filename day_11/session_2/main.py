"""
Day 11 - Session 02: Structured & Graph Retrieval (Text-to-SQL & GraphRAG)
Demonstrates:
1. Text-to-SQL with pre-execution AST validation.
2. Injection blocking and schema integrity checks.
3. Knowledge graph entity linking (GraphRAG).
4. Hybrid structured + unstructured fused queries.
"""

from __future__ import annotations
from dotenv import load_dotenv

load_dotenv()

from text_to_sql import text_to_sql_engine
from graph_rag import knowledge_graph
from hybrid_engine import hybrid_engine
from benchmark import run_benchmark


def demo_text_to_sql():
    print("\n--- 1. Text-to-SQL with Safety Validation ---")
    queries = [
        "What is the total revenue from all completed orders?",
        "What are the details of open P1-Critical support tickets and their company names?",
    ]
    for q in queries:
        print(f"\nUser Query: '{q}'")
        res = text_to_sql_engine.generate_and_execute(q)
        print(f"  SQL: {res.sql_query}")
        print(f"  Valid: {res.is_valid} | Rows: {len(res.results)}")
        print(f"  Answer: {res.final_answer.strip()[:140]}...")


def demo_graph_rag():
    print("\n--- 2. GraphRAG & Entity Linking ---")
    entity = "Acme Global Corp"
    subgraph = knowledge_graph.get_entity_subgraph(entity)
    print(f"Entity: {entity}")
    print(f"Connected Relationships ({len(subgraph)}):")
    for r in subgraph[:4]:
        print(f"  • {r['source']} -[{r['relation']}]-> {r['target']}")


def demo_hybrid():
    print("\n--- 3. Hybrid Structured (SQL + KG) & Unstructured Retrieval ---")
    query = "What is the order history and SLA tier for Acme Global Corp?"
    print(f"Query: '{query}'")
    res = hybrid_engine.run(query)
    print(f"Fused Answer:\n{res['final_answer'].strip()[:200]}...")


def main():
    print("Day 11 Session 02: Structured & Graph Retrieval\n")
    demo_text_to_sql()
    demo_graph_rag()
    demo_hybrid()

    print("\nRunning Structured & Graph Benchmark...")
    run_benchmark()


if __name__ == "__main__":
    main()
