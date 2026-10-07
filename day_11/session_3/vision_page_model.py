"""
Day 11 - Session 3: Vision Page Model & Multimodal Chart Understanding
======================================================================
Simulates modern Vision-Language Page Models (e.g., ColPali, Gemini Vision, LayoutLMv3):
  1. Visual chart comprehension (interpreting trends, axes, extrema, and series data)
  2. Image & visual figure embeddings representation
  3. Visual grounding citations for non-tabular graphical components
"""

import time
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from documents import ChartStructure, CORPUS
from layout_parser import layout_parser


class VisualCitation(BaseModel):
    """Citation pointing to a visual chart or layout bounding box."""
    doc_id: str
    page: int
    chart_id: str
    chart_title: str
    chart_type: str
    grounded_metric: str


class VisionAnswer(BaseModel):
    """Answer synthesized from multimodal visual page or chart analysis."""
    query: str
    answer: str
    visual_citation: VisualCitation
    confidence: float
    latency_ms: float


class VisionPageModel:
    """Multimodal vision-language model for page layouts and chart visual reasoning."""

    def __init__(self):
        self.charts = layout_parser.chart_index

    def answer_chart_query(self, query: str) -> Optional[VisionAnswer]:
        """Interprets graphical charts and answers visual trend questions."""
        t0 = time.perf_counter()
        q_lower = query.lower()

        # Chart 1: Financial Operating Expenses Trend (CHART-FIN-01)
        if "operating expense" in q_lower or "spend trend" in q_lower or "highest total" in q_lower or "primary spend driver" in q_lower:
            chart = self.charts.get("CHART-FIN-01")
            if chart:
                # In Q3, Total was $29.6M with R&D at $14.2M
                ans_text = (
                    "According to the Operating Expenses Trend stacked bar chart [CHART-FIN-01], "
                    "Q3 2024 exhibited the peak total operating spend at **$29.6M** (up from $22.5M in Q1 and $25.6M in Q2). "
                    "The primary spend driver was **Research & Development (R&D)**, which surged to **$14.2M** in Q3."
                )
                lat = (time.perf_counter() - t0) * 1000.0
                return VisionAnswer(
                    query=query,
                    answer=ans_text,
                    visual_citation=VisualCitation(
                        doc_id=chart.doc_id,
                        page=chart.page,
                        chart_id=chart.chart_id,
                        chart_title=chart.title,
                        chart_type=chart.chart_type,
                        grounded_metric="Q3_2024 Total = $29.6M (R&D = $14.2M)",
                    ),
                    confidence=0.96,
                    latency_ms=round(lat, 2),
                )

        # Chart 2: Accelerator Throughput vs Cost Efficiency (CHART-HW-01)
        if "throughput" in q_lower or "cost efficiency" in q_lower or "tokens per dollar" in q_lower or "scatter" in q_lower:
            chart = self.charts.get("CHART-HW-01")
            if chart:
                ans_text = (
                    "Based on the Accelerator Throughput vs Hourly Cost Efficiency scatter plot [CHART-HW-01], "
                    "**NVIDIA H100 SXM5** achieves the highest absolute throughput at **284.0 Tokens/Sec** (at $4.25/hr), "
                    "while **Google TPU v5e** provides the highest cost efficiency at **73.3 Tokens per Dollar** (88.0 Tokens/Sec at $1.20/hr)."
                )
                lat = (time.perf_counter() - t0) * 1000.0
                return VisionAnswer(
                    query=query,
                    answer=ans_text,
                    visual_citation=VisualCitation(
                        doc_id=chart.doc_id,
                        page=chart.page,
                        chart_id=chart.chart_id,
                        chart_title=chart.title,
                        chart_type=chart.chart_type,
                        grounded_metric="H100 = 284 Tokens/Sec ($4.25); TPU v5e = 88 Tokens/Sec ($1.20)",
                    ),
                    confidence=0.95,
                    latency_ms=round(lat, 2),
                )

        # Chart 3: Carrier Route Delays (CHART-LOG-01)
        if "delay" in q_lower or "port congestion" in q_lower or "carrier delay" in q_lower:
            chart = self.charts.get("CHART-LOG-01")
            if chart:
                ans_text = (
                    "Analyzing the Carrier Route Delays bar chart [CHART-LOG-01], **OceanAlliance** suffered the "
                    "highest average delay at **48.6 hours** due to Santos port congestion. In contrast, "
                    "**Lufthansa Cargo** maintained minimal air freight delay at **1.2 hours**."
                )
                lat = (time.perf_counter() - t0) * 1000.0
                return VisionAnswer(
                    query=query,
                    answer=ans_text,
                    visual_citation=VisualCitation(
                        doc_id=chart.doc_id,
                        page=chart.page,
                        chart_id=chart.chart_id,
                        chart_title=chart.title,
                        chart_type=chart.chart_type,
                        grounded_metric="OceanAlliance = 48.6 hrs delay; Lufthansa Cargo = 1.2 hrs delay",
                    ),
                    confidence=0.94,
                    latency_ms=round(lat, 2),
                )

        return None


# Singleton vision model
vision_page_model = VisionPageModel()
