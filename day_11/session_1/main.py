"""
Day 11 - Session 1: Agentic & Adaptive RAG Interactive Terminal Runner
======================================================================
Demonstrates:
  1. Multi-way Query Routing (Vector Search vs SQL vs No-Retrieval vs Multi-Hop)
  2. Self-Querying with automated metadata filter extraction
  3. Corrective RAG (CRAG) with Document Grading and Acronym Rewriting
  4. Comparative evaluation against Naive Always-Retrieve Baseline
"""

import os
import sys
import json
import time
from typing import Dict, Any

from query_router import query_router, RoutePath
from sql_database import db
from vector_store import vector_store
from crag_engine import crag_engine
from adaptive_rag import adaptive_rag
from naive_rag import naive_rag
from dataset import BENCHMARK_DATASET
from benchmark import run_benchmark


def print_banner():
    print("=" * 80)
    print("   DAY 11: ADVANCED RETRIEVAL ARCHITECTURES - SESSION 1")
    print("   AGENTIC & ADAPTIVE RAG INTERACTIVE WORKSPACE")
    print("=" * 80)
    print(" Architecture Features:")
    print("  • Intelligent Multi-Way Router (Vector vs SQL vs No-Retrieval vs Multi-Hop)")
    print("  • Self-Querying Metadata Filters (Department, Year, Category)")
    print("  • Corrective RAG (CRAG: Retrieve -> Grade -> Rewrite Loop)")
    print("  • Comparative Benchmark against Naive Always-Retrieve Baseline")
    print("=" * 80)


def show_demo_scenarios():
    scenarios = [
        ("Vector Search with Metadata Filter", "What is our company's remote work stipend policy in HR?"),
        ("SQL Tabular Aggregation", "What is the total revenue from completed orders in the database?"),
        ("Knowing When NOT to Retrieve", "Good morning! Can you help me calculate 125 * 8?"),
        ("CRAG Ambiguous / Acronym Rewrite", "What are the RTO and RPO limits in our DR plan?"),
        ("Multi-Hop Cross-Source Fusion", "What is the refund cancellation policy and how many orders are refunded?"),
    ]

    print("\n--- Preconfigured Enterprise Demonstration Scenarios ---")
    for idx, (label, q) in enumerate(scenarios, 1):
        print(f" [{idx}] {label}\n     Query: \"{q}\"")
    print(" [0] Return to Main Menu")

    choice = input("\nSelect a scenario to execute (0-5): ").strip()
    if choice in ["1", "2", "3", "4", "5"]:
        selected = scenarios[int(choice) - 1]
        process_query_inspection(selected[1])
    else:
        print("Returning to main menu...")


def process_query_inspection(query: str):
    print("\n" + "=" * 80)
    print(f"🔍 INSPECTING QUERY: \"{query}\"")
    print("=" * 80)

    # 1. Routing Inspection
    t0 = time.perf_counter()
    decision = query_router.route_query(query)
    router_time = (time.perf_counter() - t0) * 1000

    print("\n[STEP 1: QUERY ROUTER]")
    print(f" • Selected Route     : {decision.route.value.upper()}")
    print(f" • Confidence Score   : {decision.confidence:.2f}")
    print(f" • Routing Rationale  : {decision.reasoning}")
    if decision.metadata_filters:
        print(f" • Extracted Filters  : {decision.metadata_filters} (Self-Querying)")
    if decision.suggested_sql:
        print(f" • Suggested SQL      : {decision.suggested_sql}")
    print(f" • Routing Latency    : {router_time:.2f} ms")

    # 2. Execution through Adaptive RAG
    print("\n[STEP 2: ADAPTIVE RAG EXECUTION]")
    adaptive_res = adaptive_rag.run(query)
    print(f" • Execution Route    : {adaptive_res['route_chosen']}")
    print(f" • Latency            : {adaptive_res['latency_ms']:.2f} ms")
    print(f" • Tokens Consumed    : {adaptive_res['tokens_used']} tokens")
    if adaptive_res.get("sql_executed"):
        print(f" • SQL Executed       : {adaptive_res['sql_executed']}")
    if adaptive_res.get("metadata_filters"):
        print(f" • Self-Query Filters : {adaptive_res['metadata_filters']}")
    if adaptive_res.get("crag_rewrites", 0) > 0:
        print(f" • CRAG Rewrites      : {adaptive_res['crag_rewrites']} rewrite loop(s) triggered")

    print("\n [Synthesized Response]:")
    print("-" * 60)
    print(adaptive_res["final_answer"])
    print("-" * 60)

    # 3. Naive Baseline Comparison
    print("\n[STEP 3: NAIVE ALWAYS-RETRIEVE BASELINE COMPARISON]")
    naive_res = naive_rag.run(query)
    print(f" • Naive Route        : Always Vector Search (Forced)")
    print(f" • Naive Latency      : {naive_res['latency_ms']:.2f} ms")
    print(f" • Retrieved Doc(s)   : {naive_res['retrieved_doc_ids']}")
    print(f" • Context Pollution  : {'YES (Irrelevant Docs Retrieved)' if decision.route != RoutePath.VECTOR_SEARCH else 'NO'}")
    print("\n [Naive Answer Preview]:")
    print("-" * 60)
    print(naive_res["final_answer"][:300] + ("..." if len(naive_res["final_answer"]) > 300 else ""))
    print("-" * 60)


def main():
    print_banner()

    while True:
        print("\n" + "=" * 50)
        print(" MAIN MENU:")
        print("  1. Run Preconfigured Test Scenarios")
        print("  2. Enter Custom User Query")
        print("  3. Run Full 20-Query Comparative Benchmark")
        print("  4. View Database & Vector Store Inventory")
        print("  5. Exit")
        print("=" * 50)

        choice = input("Select an option (1-5): ").strip()

        if choice == "1":
            show_demo_scenarios()
        elif choice == "2":
            user_q = input("\nEnter your query: ").strip()
            if user_q:
                process_query_inspection(user_q)
            else:
                print("Query cannot be empty.")
        elif choice == "3":
            run_benchmark()
        elif choice == "4":
            print("\n--- Relational Database Schema & Summary ---")
            print(db.get_schema_summary())
            print("\n--- Vector Store Registered Documents ---")
            for doc in vector_store.documents:
                print(f" • [{doc.doc_id}] ({doc.department} | {doc.category} | {doc.year}): {doc.title}")
        elif choice == "5":
            print("\nExiting Day 11 Session 1 workspace. Goodbye!")
            sys.exit(0)
        else:
            print("Invalid option. Please enter a number between 1 and 5.")


if __name__ == "__main__":
    main()
