"""
Day 11 - Session 3: Multimodal & Complex Documents Interactive Workspace
========================================================================
Demonstrates:
  1. Answering 10 Complex Questions Requiring Reading a Table
  2. Pinpoint Cell Citations (Row/Col coordinates vs Vague Page References)
  3. Visual Chart Decomposition (Vision Page Model)
  4. Layout-Aware Table Browser (Markdown rendering of extracted 2D matrices)
  5. Automated Benchmark Suite
"""

import sys
import json
import time

from layout_parser import layout_parser
from vision_page_model import vision_page_model
from table_retriever import table_retriever, TableRetrievalResponse
from dataset import TEN_TABLE_QUESTIONS
from benchmark import run_benchmark


def print_banner():
    print("=" * 80)
    print("   DAY 11: ADVANCED RETRIEVAL ARCHITECTURES - SESSION 3")
    print("   MULTIMODAL & COMPLEX DOCUMENTS INTERACTIVE WORKSPACE")
    print("=" * 80)
    print(" Core Architecture Capabilities:")
    print("  - Layout-Aware 2D Table Matrix & Grid Coordinate Parsing")
    print("  - Pinpoint Cell-Level Citations (Citing Table Cell rather than whole Page)")
    print("  - Visual Chart Decomposition & Reasoning (Vision Page Model)")
    print("  - Benchmark Suite Answering 10 Complex Table-Reading Questions")
    print("=" * 80)


def demo_table_qa():
    print("\n--- [1] Answering Questions That Require Reading a Table ---")
    print("Preset Table-Reading Evaluation Queries:")
    for idx, tc in enumerate(TEN_TABLE_QUESTIONS[:10], 1):
        print(f"  [{idx:2d}] {tc.question}")
    print("  [ C] Enter custom table-reading query")

    choice = input("\nSelect query (1-10 or C): ").strip()
    if choice.upper() == "C":
        q = input("Enter your table-reading question: ").strip()
    elif choice.isdigit() and 1 <= int(choice) <= 10:
        q = TEN_TABLE_QUESTIONS[int(choice) - 1].question
    else:
        print("Invalid selection. Returning...")
        return

    print("\n" + "-" * 75)
    print(f"Question: \"{q}\"")
    print("-" * 75)

    resp: TableRetrievalResponse = table_retriever.answer_table_question(q)

    print("\n[GROUNDED SYNTHESIS]:")
    print(resp.answer)

    if resp.primary_cell_citation:
        cit = resp.primary_cell_citation
        print("\n[PINPOINT CELL CITATION]:")
        print(f"  - Citation Badge  : {cit.citation_badge}")
        print(f"  - Document        : {cit.doc_title} [{cit.doc_id}] (Page {cit.page})")
        print(f"  - Table           : {cit.table_title} [{cit.table_id}]")
        print(f"  - Row Coordinate  : Index {cit.row_index} -> \"{cit.row_header}\"")
        print(f"  - Col Coordinate  : Index {cit.col_index} -> \"{cit.col_header}\"")
        print(f"  - Exact Cell Value: \"{cit.exact_cell_value}\"")

    if resp.supporting_cell_citations:
        print("\n[SUPPORTING CELL CITATIONS]:")
        for sc in resp.supporting_cell_citations:
            print(f"  * {sc.citation_badge} (Row: {sc.row_header}, Col: {sc.col_header})")

    if resp.visual_citation:
        vc = resp.visual_citation
        print("\n[VISUAL CHART CITATION]:")
        print(f"  - Chart ID        : {vc.get('chart_id')}")
        print(f"  - Chart Title     : {vc.get('chart_title')} (Type: {vc.get('chart_type')})")
        print(f"  - Grounded Metric : {vc.get('grounded_metric')}")

    print(f"\n[EXECUTION METRICS]:")
    print(f"  - Reasoning Path  : {resp.reasoning_path}")
    print(f"  - Query Latency   : {resp.latency_ms:.2f} ms")


def demo_cell_vs_page_citation():
    print("\n--- [2] 'Citing a Table Cell Rather Than a Page' Live Comparison ---")
    q = "What was the Gross Margin for AI & LLM Inference in Q3 2024?"
    print(f"Query: \"{q}\"\n")

    demo = table_retriever.demonstrate_cell_vs_page_citation(q)

    print("[APPROACH A: LAYOUT-AWARE PINPOINT CELL CITATION]")
    lac = demo["layout_aware_pinpoint_citation"]
    print(f"  - Badge       : {lac['citation_badge']}")
    print(f"  - Document    : {lac['document']}")
    print(f"  - Table       : {lac['table_id']}")
    print(f"  - Coordinates : Row {lac['row_index']} ('{lac['row_header']}') x Col {lac['col_index']} ('{lac['col_header']}')")
    print(f"  - Exact Value : {lac['exact_cell_value']}")
    print(f"  - Verification: {lac['user_verification_effort']}")

    print("\n[APPROACH B: NAIVE 500-TOKEN CHUNK / PAGE-LEVEL CITATION]")
    nc = demo["naive_chunk_citation"]
    print(f"  - Citation    : {nc['citation_text']}")
    print(f"  - Row Info    : {nc['row_coordinates']}")
    print(f"  - Col Info    : {nc['col_coordinates']}")
    print(f"  - Verification: {nc['user_verification_effort']}")

    print(f"\n[VERDICT]:\n  {demo['provenance_advantage']}")


def demo_visual_charts():
    print("\n--- [3] Multimodal Visual Chart Reasoning (Vision Page Model) ---")
    charts = [
        ("Operating Expense Trend", "What was the peak operating expense quarter and spend driver in the spend trend chart?"),
        ("Accelerator Efficiency", "Which accelerator offers the highest throughput in the efficiency scatter plot?"),
        ("Carrier Route Delays", "Which carrier suffered the highest delays according to the carrier delays chart?"),
    ]
    for idx, (title, q) in enumerate(charts, 1):
        print(f"\n[Chart {idx}: {title}]")
        print(f" Question: \"{q}\"")
        ans = vision_page_model.answer_chart_query(q)
        if ans:
            print(f" Answer  : {ans.answer}")
            print(f" Citation: Chart [{ans.visual_citation.chart_id}] -> {ans.visual_citation.grounded_metric}")


def demo_table_browser():
    print("\n--- [4] Layout-Aware Extracted Table Browser ---")
    for tbl_id, tbl in layout_parser.table_index.items():
        print("\n" + "=" * 70)
        print(layout_parser.format_table_as_markdown(tbl_id))


def main():
    print_banner()

    while True:
        print("\n" + "=" * 50)
        print(" MAIN MENU:")
        print("  1. Answer Table-Reading Questions (10 Scenarios)")
        print("  2. Cell-Level vs Page Citation Comparison")
        print("  3. Visual Chart Decomposition (Vision Page Model)")
        print("  4. Browse Extracted 2D Markdown Tables")
        print("  5. Run 12-Test Automated Benchmark Suite")
        print("  6. Exit")
        print("=" * 50)

        choice = input("Select an option (1-6): ").strip()

        if choice == "1":
            demo_table_qa()
        elif choice == "2":
            demo_cell_vs_page_citation()
        elif choice == "3":
            demo_visual_charts()
        elif choice == "4":
            demo_table_browser()
        elif choice == "5":
            run_benchmark()
        elif choice == "6":
            print("\nExiting Day 11 Session 3 workspace. Goodbye!")
            sys.exit(0)
        else:
            print("Invalid option. Please choose between 1 and 6.")


if __name__ == "__main__":
    main()
