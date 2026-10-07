"""
Day 11 - Session 3: 10 Questions Requiring Reading a Table Benchmark Dataset
============================================================================
Defines the required 10 enterprise evaluation queries specifically requiring reading
complex tables (with coordinates, aggregations, deltas, and footnotes), plus visual chart tests.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class TableEvaluationQuestion(BaseModel):
    """Evaluation test case for table-reading RAG."""
    question_id: str
    category: str  # Cell_Lookup, ArgMax_Comparison, Arithmetic_Delta, Multi_Attribute, Footnote_Reading, Visual_Chart
    question: str
    expected_doc_id: str
    expected_table_or_chart_id: str
    expected_exact_value: str
    expected_keywords: List[str]
    expected_row: Optional[str] = None
    expected_col: Optional[str] = None
    description: str


TEN_TABLE_QUESTIONS: List[TableEvaluationQuestion] = [
    # -----------------------------------------------------------------------
    # QUESTION 1: Atomic Exact Cell Lookup
    # -----------------------------------------------------------------------
    TableEvaluationQuestion(
        question_id="Q-TBL-01",
        category="Cell_Lookup",
        question="What was the Gross Margin for AI & LLM Inference in Q3 2024?",
        expected_doc_id="DOC-FIN-2024",
        expected_table_or_chart_id="TBL-FIN-01",
        expected_exact_value="74.2%",
        expected_keywords=["74.2%", "AI & LLM Inference", "Gross_Margin"],
        expected_row="AI & LLM Inference",
        expected_col="Gross_Margin",
        description="Verify atomic cell coordinate lookup at Row 1 x Col 5 in financial table",
    ),

    # -----------------------------------------------------------------------
    # QUESTION 2: Cross-Row ArgMax Comparison
    # -----------------------------------------------------------------------
    TableEvaluationQuestion(
        question_id="Q-TBL-02",
        category="ArgMax_Comparison",
        question="Which GPU accelerator has the highest memory bandwidth and what is its value?",
        expected_doc_id="DOC-HW-2024",
        expected_table_or_chart_id="TBL-HW-01",
        expected_exact_value="3350 GB/s",
        expected_keywords=["NVIDIA H100 SXM5", "3350", "GB/s"],
        expected_row="NVIDIA H100 SXM5",
        expected_col="Memory_Bandwidth_GBs",
        description="Verify column scan on Memory_Bandwidth_GBs with argmax row identification",
    ),

    # -----------------------------------------------------------------------
    # QUESTION 3: Multi-Cell Arithmetic / Delta
    # -----------------------------------------------------------------------
    TableEvaluationQuestion(
        question_id="Q-TBL-03",
        category="Arithmetic_Delta",
        question="What was the revenue increase for Cloud Compute between Q1 and Q3 2024?",
        expected_doc_id="DOC-FIN-2024",
        expected_table_or_chart_id="TBL-FIN-01",
        expected_exact_value="+$6.3M",
        expected_keywords=["6.3M", "18.5M", "24.8M"],
        expected_row="Cloud Compute",
        expected_col="Q3_2024",
        description="Verify multi-cell subtraction between Q3_2024 ($24.8M) and Q1_2024 ($18.5M)",
    ),

    # -----------------------------------------------------------------------
    # QUESTION 4: Unit Cost Cell Lookup
    # -----------------------------------------------------------------------
    TableEvaluationQuestion(
        question_id="Q-TBL-04",
        category="Cell_Lookup",
        question="What is the hourly rental cost of NVIDIA H100 SXM5?",
        expected_doc_id="DOC-HW-2024",
        expected_table_or_chart_id="TBL-HW-01",
        expected_exact_value="$4.25",
        expected_keywords=["$4.25", "NVIDIA H100 SXM5", "Hourly_Cost_USD"],
        expected_row="NVIDIA H100 SXM5",
        expected_col="Hourly_Cost_USD",
        description="Verify hardware unit pricing cell coordinate extraction",
    ),

    # -----------------------------------------------------------------------
    # QUESTION 5: Two-Cell Co-Extraction (Spend + Variance)
    # -----------------------------------------------------------------------
    TableEvaluationQuestion(
        question_id="Q-TBL-05",
        category="Multi_Attribute",
        question="What was Research & Development operating expense in Q3 2024 and its budget variance?",
        expected_doc_id="DOC-FIN-2024",
        expected_table_or_chart_id="TBL-FIN-02",
        expected_exact_value="$14.2M",
        expected_keywords=["$14.2M", "+4.5%", "Research & Development"],
        expected_row="Research & Development (R&D)",
        expected_col="Q3_2024",
        description="Verify extraction of spend amount and budget variance across the same row",
    ),

    # -----------------------------------------------------------------------
    # QUESTION 6: Minimum ArgMin Row Lookup
    # -----------------------------------------------------------------------
    TableEvaluationQuestion(
        question_id="Q-TBL-06",
        category="ArgMax_Comparison",
        question="Which global freight transit lane has the lowest on-time delivery rate?",
        expected_doc_id="DOC-LOG-2024",
        expected_table_or_chart_id="TBL-LOG-01",
        expected_exact_value="83.4%",
        expected_keywords=["RT-104", "83.4%", "Santos"],
        expected_row="RT-104",
        expected_col="On_Time_Rate",
        description="Verify column scan on On_Time_Rate with argmin selection",
    ),

    # -----------------------------------------------------------------------
    # QUESTION 7: Multi-Attribute Filtering (Origin & Destination)
    # -----------------------------------------------------------------------
    TableEvaluationQuestion(
        question_id="Q-TBL-07",
        category="Multi_Attribute",
        question="How many transit days does it take to ship from Singapore to Rotterdam and which carrier operates it?",
        expected_doc_id="DOC-LOG-2024",
        expected_table_or_chart_id="TBL-LOG-01",
        expected_exact_value="22 days",
        expected_keywords=["EuroGlobal", "22 days", "Singapore", "Rotterdam"],
        expected_row="RT-102",
        expected_col="Transit_Days",
        description="Verify 2-column condition (Origin='Singapore' AND Destination='Rotterdam') row filter",
    ),

    # -----------------------------------------------------------------------
    # QUESTION 8: Cross-Row Cell Summation
    # -----------------------------------------------------------------------
    TableEvaluationQuestion(
        question_id="Q-TBL-08",
        category="Arithmetic_Delta",
        question="What is the total combined power consumption (TDP Watts) of NVIDIA H100 and A100?",
        expected_doc_id="DOC-HW-2024",
        expected_table_or_chart_id="TBL-HW-01",
        expected_exact_value="1100 Watts",
        expected_keywords=["1100", "700", "400", "Watts"],
        expected_row="NVIDIA H100 SXM5",
        expected_col="TDP_Watts",
        description="Verify arithmetic summation across H100 TDP (700W) and A100 TDP (400W)",
    ),

    # -----------------------------------------------------------------------
    # QUESTION 9: Footnote & Accounting Policy Reading
    # -----------------------------------------------------------------------
    TableEvaluationQuestion(
        question_id="Q-TBL-09",
        category="Footnote_Reading",
        question="Do reported gross margin percentages include stock-based compensation amortization according to table footnotes?",
        expected_doc_id="DOC-FIN-2024",
        expected_table_or_chart_id="TBL-FIN-01",
        expected_exact_value="exclude stock-based compensation",
        expected_keywords=["exclude", "stock-based compensation", "footnote"],
        expected_row="Footnote",
        expected_col="Footnote",
        description="Verify layout parser extracts and grounds answer in official table footnote",
    ),

    # -----------------------------------------------------------------------
    # QUESTION 10: Percentage Rate Lookup
    # -----------------------------------------------------------------------
    TableEvaluationQuestion(
        question_id="Q-TBL-10",
        category="Cell_Lookup",
        question="What was the YoY revenue growth rate of the AI & LLM Inference segment?",
        expected_doc_id="DOC-FIN-2024",
        expected_table_or_chart_id="TBL-FIN-01",
        expected_exact_value="+139.0%",
        expected_keywords=["+139.0%", "139%", "AI & LLM Inference", "YoY_Growth"],
        expected_row="AI & LLM Inference",
        expected_col="YoY_Growth",
        description="Verify growth percentage cell coordinate extraction at Row 1 x Col 4",
    ),

    # -----------------------------------------------------------------------
    # BONUS VISUAL QUESTIONS (Multimodal Chart Reasoning)
    # -----------------------------------------------------------------------
    TableEvaluationQuestion(
        question_id="Q-CHART-01",
        category="Visual_Chart",
        question="What was the peak operating expense quarter and spend driver in the spend trend chart?",
        expected_doc_id="DOC-FIN-2024",
        expected_table_or_chart_id="CHART-FIN-01",
        expected_exact_value="$29.6M",
        expected_keywords=["Q3 2024", "$29.6M", "R&D", "$14.2M"],
        description="Verify visual chart decomposition on stacked bar chart for operating expenses",
    ),
    TableEvaluationQuestion(
        question_id="Q-CHART-02",
        category="Visual_Chart",
        question="Which accelerator offers the highest throughput in the efficiency scatter plot?",
        expected_doc_id="DOC-HW-2024",
        expected_table_or_chart_id="CHART-HW-01",
        expected_exact_value="284.0 Tokens/Sec",
        expected_keywords=["NVIDIA H100 SXM5", "284", "Tokens"],
        description="Verify visual scatter plot reasoning on throughput vs cost efficiency",
    ),
]
