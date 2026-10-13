"""
Day 11 - Session 03: Multimodal & Complex Documents (Tables & Charts)
Demonstrates:
1. Answering questions that require reading 2D tables.
2. Pinpoint cell citations (row/column coordinates).
3. Vision page model chart decomposition.
4. Benchmark suite for complex document retrieval.
"""

from __future__ import annotations
from dotenv import load_dotenv

load_dotenv()

from table_retriever import table_retriever
from vision_page_model import vision_page_model
from dataset import TEN_TABLE_QUESTIONS
from benchmark import run_benchmark


def demo_table_qa():
    print("\n--- 1. Answering Questions Requiring Table Reading ---")
    for tc in TEN_TABLE_QUESTIONS[:3]:
        print(f"\nQuestion: '{tc.question}'")
        resp = table_retriever.answer_table_question(tc.question)
        print(f"Answer: {resp.answer[:120]}...")
        if resp.cell_citations:
            c = resp.cell_citations[0]
            print(f"Cell Citation: Table '{c.table_name}', Row {c.row_idx}, Col '{c.col_name}' -> '{c.cell_value}'")


def demo_vision_chart():
    print("\n--- 2. Vision Chart Decomposition ---")
    chart_res = vision_page_model.analyze_chart("chart_revenue_breakdown")
    print(f"Chart: {chart_res.get('title', 'Revenue Breakdown')}")
    print(f"Key Data Points: {chart_res.get('data_points', [])[:3]}")


def main():
    print("Day 11 Session 03: Multimodal & Complex Document QA\n")
    demo_table_qa()
    demo_vision_chart()

    print("\nRunning Table QA Benchmark...")
    run_benchmark()


if __name__ == "__main__":
    main()
