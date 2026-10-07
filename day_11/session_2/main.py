"""
Day 11 - Session 2: Structured & Graph Retrieval Interactive Workspace
======================================================================
Features:
  1. Text-to-SQL Query Engine with Pre-Execution Validation
  2. Security Guardrail Sandbox (DDL/DML injection blocking)
  3. Knowledge Graph Entity Linking & GraphRAG Subgraph Explorer
  4. 'When a JOIN beats an Embedding' Live Comparative Demo
  5. Hybrid Structured + Unstructured Fused Intelligence Briefing
  6. Automated 20-Case Benchmark Suite
  7. 5-Table Database Schema & Records Explorer
"""

import sys
import json
import time

from database import db
from sql_validator import sql_validator
from text_to_sql import text_to_sql_engine, TextToSQLResult
from graph_rag import knowledge_graph
from hybrid_engine import hybrid_engine
from benchmark import run_benchmark


def print_banner():
    print("=" * 80)
    print("   DAY 11: ADVANCED RETRIEVAL ARCHITECTURES - SESSION 2")
    print("   STRUCTURED & GRAPH RETRIEVAL INTERACTIVE WORKSPACE")
    print("=" * 80)
    print(" Core Architecture Capabilities:")
    print("  - Text-to-SQL over a 5-Table Enterprise Relational Schema")
    print("  - Pre-Execution SQL Validation (Injection blocking, schema integrity, LIMITs)")
    print("  - Enterprise Knowledge Graph with Entity Linking & Subgraph Extraction")
    print("  - 'When a JOIN beats an Embedding' Deterministic Multi-Hop Integrity")
    print("  - Hybrid Structured (SQL + KG) + Unstructured (SLAs) Fused Answers")
    print("=" * 80)


def demo_text_to_sql():
    print("\n--- [1] Text-to-SQL with Pre-Execution AST Validation ---")
    presets = [
        "What is the total revenue from all completed orders?",
        "Which customer has spent the most on completed orders?",
        "What are the details of open P1-Critical support tickets and their company names?",
        "What is the most popular product by total units ordered?",
        "Show the order history and amounts for Acme Global Corp.",
    ]
    print("Preset Enterprise Queries:")
    for i, p in enumerate(presets, 1):
        print(f"  [{i}] \"{p}\"")
    print("  [C] Enter custom natural language query")

    choice = input("\nSelect query (1-5 or C): ").strip()
    if choice.upper() == "C":
        q = input("Enter your natural language query: ").strip()
    elif choice in ["1", "2", "3", "4", "5"]:
        q = presets[int(choice) - 1]
    else:
        print("Invalid choice. Returning...")
        return

    print("\n" + "-" * 70)
    print(f"User Query: \"{q}\"")
    print("-" * 70)

    res: TextToSQLResult = text_to_sql_engine.generate_and_execute(q)

    print("\n[LIFECYCLE TELEMETRY]:")
    print(f" - Candidate SQL    : {res.generated_sql}")
    print(f" - Validated SQL    : {res.validated_sql}")
    print(f" - Pre-Exec Valid   : {res.is_valid}")
    print(f" - Self-Corrected   : {res.self_corrected}")
    if res.validation_warnings:
        print(f" - Warnings         : {'; '.join(res.validation_warnings)}")
    print(f" - Execution Status : {res.execution_status}")
    print(f" - Execution Latency: {res.latency_ms:.2f} ms")
    print(f" - Rows Returned    : {res.row_count}")

    if res.rows:
        print("\n[RESULT DATA (First 5 Rows)]:")
        print(json.dumps(res.rows[:5], indent=2))


def demo_security_sandbox():
    print("\n--- [2] Security Guardrail & Injection Sandbox ---")
    print("Testing malicious SQL injection attempts against the validator:")

    attacks = [
        ("DROP Table Attack", "DROP TABLE customers;"),
        ("DELETE All Records", "DELETE FROM orders WHERE 1=1;"),
        ("Stacked Semicolon", "SELECT * FROM products; DROP TABLE support_tickets;"),
        ("Unauthorized UPDATE", "UPDATE products SET unit_price = 0;"),
    ]

    for label, raw_sql in attacks:
        print(f"\n[Test: {label}]")
        print(f" Candidate SQL: {raw_sql}")
        val = sql_validator.validate(raw_sql)
        print(f" - Is Valid   : {val.is_valid}")
        print(f" - Status     : {'BLOCKED (Security Pass)' if not val.is_valid else 'VULNERABILITY'}")
        print(f" - Violations : {val.failure_reasons}")


def demo_join_vs_embedding():
    print("\n--- [3] 'When a JOIN beats an Embedding' Demonstration ---")
    demo = knowledge_graph.demonstrate_join_vs_embedding()

    print(f"Complex Multi-Hop Query:\n  \"{demo['query']}\"\n")
    print("[1. 5-Table Relational SQL JOIN Method]:")
    print(f"  SQL Executed:\n{demo['relational_join']['sql']}")
    print(f"  Execution Time   : {demo['relational_join']['execution_time_ms']} ms")
    print(f"  Accuracy         : {demo['relational_join']['deterministic_accuracy']}")
    print(f"  Verified Products: {demo['relational_join']['verified_products']}")
    print(f"  Matched Customers: {demo['relational_join']['matching_customers']}")

    print("\n[2. Unconstrained Vector Embedding Method]:")
    print(f"  Precision        : {demo['vector_embedding']['precision']}")
    print(f"  Core Failure     : {demo['vector_embedding']['failure_mode']}")
    print("  Retrieved Chunks :")
    for item in demo["vector_embedding"]["retrieved_results"]:
        print(f"    * Product: {item['product']:<35} (Score: {item['score']}) -> {item['match']}")

    print(f"\n[VERDICT]:\n  {demo['verdict']}")


def demo_hybrid_synthesis():
    print("\n--- [4] Hybrid Structured + Unstructured Fused Intelligence ---")
    q = "What is the status of Acme Global Corp support tickets and what SLA applies?"
    print(f"Query: \"{q}\"\n")

    res = hybrid_engine.answer_query(q)
    print(f"Structured SQL Executed:\n{res.structured_sql}\n")
    print(f"Linked Graph Entities: {res.linked_entities}")
    print(f"Relational Triples   : {res.graph_triples}")
    print(f"Grounded Docs        : {res.unstructured_sources}")
    print(f"Latency              : {res.latency_ms:.2f} ms")
    print("\n[Fused Executive Briefing]:")
    print("-" * 65)
    print(res.fused_answer)
    print("-" * 65)


def demo_schema_explorer():
    print("\n--- [5] 5-Table Schema & Records Explorer ---")
    info = db.get_schema_info()
    for tbl, data in info.items():
        print(f"\nTABLE: {tbl}")
        print(f"  Columns      : {list(data['columns'].keys())}")
        if data['foreign_keys']:
            print(f"  Foreign Keys : {data['foreign_keys']}")
        cur = db.conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM {tbl};")
        cnt = cur.fetchone()[0]
        print(f"  Total Records: {cnt}")


def main():
    print_banner()

    while True:
        print("\n" + "=" * 50)
        print(" MAIN MENU:")
        print("  1. Text-to-SQL with Pre-Execution Validation")
        print("  2. Security & Injection Guardrail Sandbox")
        print("  3. 'When a JOIN beats an Embedding' Live Demo")
        print("  4. Hybrid Structured + Unstructured Synthesis")
        print("  5. Run 20-Case Benchmark Suite")
        print("  6. Explore 5-Table Database Schema")
        print("  7. Exit")
        print("=" * 50)

        choice = input("Select an option (1-7): ").strip()

        if choice == "1":
            demo_text_to_sql()
        elif choice == "2":
            demo_security_sandbox()
        elif choice == "3":
            demo_join_vs_embedding()
        elif choice == "4":
            demo_hybrid_synthesis()
        elif choice == "5":
            run_benchmark()
        elif choice == "6":
            demo_schema_explorer()
        elif choice == "7":
            print("\nExiting Day 11 Session 2 workspace. Goodbye!")
            sys.exit(0)
        else:
            print("Invalid option. Please choose between 1 and 7.")


if __name__ == "__main__":
    main()
