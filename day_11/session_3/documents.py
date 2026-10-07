"""
Day 11 - Session 3: Multimodal & Complex Document Corpus
========================================================
Contains realistic enterprise multimodal documents featuring:
  - Document 1: Q3 Enterprise Financial Performance Report (Multi-header tables, margin %, R&D expense bar chart)
  - Document 2: Cloud Hardware Benchmark & Accelerator Specs (Hardware metrics, TFLOPS, TDP, cost/hour)
  - Document 3: Global Logistics & Supply Chain Operations (International lanes, on-time %, transit days)
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class TableCell(BaseModel):
    """Represents a single atomic table cell with coordinates."""
    row_idx: int
    row_header: str
    col_idx: int
    col_header: str
    value: str
    numeric_value: Optional[float] = None


class TableStructure(BaseModel):
    """Structured representation of a table extracted by layout-aware parser."""
    table_id: str
    doc_id: str
    page: int
    title: str
    column_headers: List[str]
    rows: List[Dict[str, str]]
    cells: List[TableCell] = Field(default_factory=list)
    footnote: str = ""


class ChartStructure(BaseModel):
    """Structured visual representation of a chart or graphical figure."""
    chart_id: str
    doc_id: str
    page: int
    title: str
    chart_type: str  # Bar, Line, Scatter, Pie
    x_axis_label: str
    y_axis_label: str
    series_data: Dict[str, Any]
    visual_summary: str


class MultimodalDocument(BaseModel):
    """Full multimodal document containing text sections, tables, and charts."""
    doc_id: str
    title: str
    pages: int
    narrative_text: str
    tables: List[TableStructure]
    charts: List[ChartStructure]


# ---------------------------------------------------------------------------
# DOCUMENT 1: Q3 Enterprise Financial Performance Report
# ---------------------------------------------------------------------------
DOC_FINANCIALS = MultimodalDocument(
    doc_id="DOC-FIN-2024",
    title="Q3 2024 Enterprise Financial Performance & Earnings Report",
    pages=1,
    narrative_text=(
        "Q3 2024 demonstrated strong revenue expansion across all segments, led by explosive "
        "demand for AI & LLM Inference services. Consolidated revenue reached $67.2M, representing "
        "a 42.4% year-over-year growth rate. Gross margin expanded to 67.8%. Research & Development "
        "investments accelerated to support next-generation sovereign inference clusters."
    ),
    tables=[
        TableStructure(
            table_id="TBL-FIN-01",
            doc_id="DOC-FIN-2024",
            page=1,
            title="Quarterly Segment Revenue & Gross Margins (in Millions USD)",
            column_headers=["Segment", "Q1_2024", "Q2_2024", "Q3_2024", "YoY_Growth", "Gross_Margin"],
            rows=[
                {"Segment": "Cloud Compute", "Q1_2024": "$18.5M", "Q2_2024": "$21.2M", "Q3_2024": "$24.8M", "YoY_Growth": "+34.1%", "Gross_Margin": "68.5%"},
                {"Segment": "AI & LLM Inference", "Q1_2024": "$8.2M", "Q2_2024": "$12.4M", "Q3_2024": "$19.6M", "YoY_Growth": "+139.0%", "Gross_Margin": "74.2%"},
                {"Segment": "Enterprise Storage", "Q1_2024": "$14.1M", "Q2_2024": "$14.8M", "Q3_2024": "$15.5M", "YoY_Growth": "+9.9%", "Gross_Margin": "62.0%"},
                {"Segment": "Networking & CDN", "Q1_2024": "$6.4M", "Q2_2024": "$6.9M", "Q3_2024": "$7.3M", "YoY_Growth": "+14.1%", "Gross_Margin": "58.4%"},
                {"Segment": "Total Consolidated", "Q1_2024": "$47.2M", "Q2_2024": "$55.3M", "Q3_2024": "$67.2M", "YoY_Growth": "+42.4%", "Gross_Margin": "67.8%"},
            ],
            footnote="Note: Revenue figures are GAAP compliant. Gross margins exclude stock-based compensation amortization.",
        ),
        TableStructure(
            table_id="TBL-FIN-02",
            doc_id="DOC-FIN-2024",
            page=1,
            title="Operating Expense Breakdown by Department (in Millions USD)",
            column_headers=["Expense_Category", "Q1_2024", "Q2_2024", "Q3_2024", "Budget_Variance"],
            rows=[
                {"Expense_Category": "Research & Development (R&D)", "Q1_2024": "$9.8M", "Q2_2024": "$11.5M", "Q3_2024": "$14.2M", "Budget_Variance": "+4.5%"},
                {"Expense_Category": "Sales & Marketing (S&M)", "Q1_2024": "$7.2M", "Q2_2024": "$8.1M", "Q3_2024": "$8.9M", "Budget_Variance": "-2.1%"},
                {"Expense_Category": "General & Administrative (G&A)", "Q1_2024": "$3.4M", "Q2_2024": "$3.6M", "Q3_2024": "$3.8M", "Budget_Variance": "-0.5%"},
                {"Expense_Category": "Stock-Based Compensation (SBC)", "Q1_2024": "$2.1M", "Q2_2024": "$2.4M", "Q3_2024": "$2.7M", "Budget_Variance": "+1.2%"},
            ],
            footnote="Budget variance indicates divergence from preliminary FY2024 operating plan.",
        ),
    ],
    charts=[
        ChartStructure(
            chart_id="CHART-FIN-01",
            doc_id="DOC-FIN-2024",
            page=1,
            title="Operating Expenses Trend (Q1 - Q3 2024)",
            chart_type="Stacked_Bar",
            x_axis_label="Fiscal Quarter",
            y_axis_label="Spend in Millions USD",
            series_data={
                "Q1_2024": {"R&D": 9.8, "S&M": 7.2, "G&A": 3.4, "SBC": 2.1, "Total": 22.5},
                "Q2_2024": {"R&D": 11.5, "S&M": 8.1, "G&A": 3.6, "SBC": 2.4, "Total": 25.6},
                "Q3_2024": {"R&D": 14.2, "S&M": 8.9, "G&A": 3.8, "SBC": 2.7, "Total": 29.6},
            },
            visual_summary="Stacked bar chart illustrates R&D as the primary spend driver, expanding by $2.7M in Q3 2024.",
        )
    ],
)

# ---------------------------------------------------------------------------
# DOCUMENT 2: Cloud Hardware Benchmark & Accelerator Specs
# ---------------------------------------------------------------------------
DOC_HARDWARE = MultimodalDocument(
    doc_id="DOC-HW-2024",
    title="Cloud Accelerator Hardware Specifications & Benchmark Matrix",
    pages=1,
    narrative_text=(
        "Engineering evaluation of accelerated compute instances for large-scale transformer "
        "inference and fine-tuning workloads. Test environment deployed under Kubernetes 1.29 "
        "with CUDA 12.4 and PyTorch 2.3."
    ),
    tables=[
        TableStructure(
            table_id="TBL-HW-01",
            doc_id="DOC-HW-2024",
            page=1,
            title="AI Accelerator Compute, Memory & Cost Comparison",
            column_headers=["Accelerator_Model", "Architecture", "FP16_TFLOPS", "Memory_Bandwidth_GBs", "TDP_Watts", "P99_Latency_ms", "Hourly_Cost_USD"],
            rows=[
                {"Accelerator_Model": "NVIDIA H100 SXM5", "Architecture": "Hopper", "FP16_TFLOPS": "1979", "Memory_Bandwidth_GBs": "3350", "TDP_Watts": "700", "P99_Latency_ms": "14.2", "Hourly_Cost_USD": "$4.25"},
                {"Accelerator_Model": "NVIDIA A100 80GB", "Architecture": "Ampere", "FP16_TFLOPS": "312", "Memory_Bandwidth_GBs": "2039", "TDP_Watts": "400", "P99_Latency_ms": "28.5", "Hourly_Cost_USD": "$2.50"},
                {"Accelerator_Model": "Google TPU v5e", "Architecture": "TPU", "FP16_TFLOPS": "197", "Memory_Bandwidth_GBs": "820", "TDP_Watts": "250", "P99_Latency_ms": "36.1", "Hourly_Cost_USD": "$1.20"},
                {"Accelerator_Model": "AWS Trainium Trn1", "Architecture": "Neuron", "FP16_TFLOPS": "420", "Memory_Bandwidth_GBs": "820", "TDP_Watts": "300", "P99_Latency_ms": "32.4", "Hourly_Cost_USD": "$1.35"},
            ],
            footnote="Latency measured on Llama-3-70B batch-1 token-to-token inference under FP16 precision.",
        )
    ],
    charts=[
        ChartStructure(
            chart_id="CHART-HW-01",
            doc_id="DOC-HW-2024",
            page=1,
            title="Accelerator Throughput vs Hourly Cost Efficiency",
            chart_type="Scatter_Plot",
            x_axis_label="Hourly Rental Cost ($ USD)",
            y_axis_label="Throughput (Tokens / Sec)",
            series_data={
                "NVIDIA H100 SXM5": {"Cost": 4.25, "Tokens_Sec": 284.0},
                "NVIDIA A100 80GB": {"Cost": 2.50, "Tokens_Sec": 142.5},
                "Google TPU v5e": {"Cost": 1.20, "Tokens_Sec": 88.0},
                "AWS Trainium Trn1": {"Cost": 1.35, "Tokens_Sec": 105.2},
            },
            visual_summary="Scatter plot demonstrates NVIDIA H100 achieves superior absolute throughput, while Google TPU v5e yields highest tokens per dollar.",
        )
    ],
)

# ---------------------------------------------------------------------------
# DOCUMENT 3: Global Logistics & Supply Chain Operations
# ---------------------------------------------------------------------------
DOC_LOGISTICS = MultimodalDocument(
    doc_id="DOC-LOG-2024",
    title="Global Supply Chain Logistics & Transit Lane Reliability",
    pages=1,
    narrative_text=(
        "Quarterly logistics review tracking sea and air freight lanes, carrier compliance, "
        "and fuel surcharges across key manufacturing corridors."
    ),
    tables=[
        TableStructure(
            table_id="TBL-LOG-01",
            doc_id="DOC-LOG-2024",
            page=1,
            title="Primary Global Freight Transit Lanes Performance",
            column_headers=["Route_ID", "Origin", "Destination", "Carrier", "Transit_Days", "On_Time_Rate", "Fuel_Surcharge_USD"],
            rows=[
                {"Route_ID": "RT-101", "Origin": "Shanghai (PVG)", "Destination": "Los Angeles (LAX)", "Carrier": "Pacific Freight", "Transit_Days": "14", "On_Time_Rate": "94.2%", "Fuel_Surcharge_USD": "$480"},
                {"Route_ID": "RT-102", "Origin": "Singapore (SIN)", "Destination": "Rotterdam (RTM)", "Carrier": "EuroGlobal", "Transit_Days": "22", "On_Time_Rate": "91.5%", "Fuel_Surcharge_USD": "$620"},
                {"Route_ID": "RT-103", "Origin": "Tokyo (NRT)", "Destination": "Frankfurt (FRA)", "Carrier": "Lufthansa Cargo", "Transit_Days": "3", "On_Time_Rate": "98.7%", "Fuel_Surcharge_USD": "$890"},
                {"Route_ID": "RT-104", "Origin": "Busan (PUS)", "Destination": "Santos (SSZ)", "Carrier": "OceanAlliance", "Transit_Days": "31", "On_Time_Rate": "83.4%", "Fuel_Surcharge_USD": "$710"},
            ],
            footnote="On-time delivery defined as arrival within +/- 12 hours of estimated schedule.",
        )
    ],
    charts=[
        ChartStructure(
            chart_id="CHART-LOG-01",
            doc_id="DOC-LOG-2024",
            page=1,
            title="Carrier Route Delays Breakdown",
            chart_type="Bar_Chart",
            x_axis_label="Carrier",
            y_axis_label="Average Delay Hours",
            series_data={
                "Lufthansa Cargo": 1.2,
                "Pacific Freight": 8.5,
                "EuroGlobal": 14.2,
                "OceanAlliance": 48.6,
            },
            visual_summary="Bar chart highlights OceanAlliance encountering substantial port congestion delays (48.6 hours average).",
        )
    ],
)

CORPUS: Dict[str, MultimodalDocument] = {
    DOC_FINANCIALS.doc_id: DOC_FINANCIALS,
    DOC_HARDWARE.doc_id: DOC_HARDWARE,
    DOC_LOGISTICS.doc_id: DOC_LOGISTICS,
}
