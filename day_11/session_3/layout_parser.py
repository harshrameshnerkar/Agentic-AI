"""
Day 11 - Session 3: Layout-Aware Document & Table Parser
========================================================
Implements:
  1. 2D Table Matrix & Grid Coordinate Extraction
  2. Cell-Level Indexing (Mapping row headers, column headers, and atomic values)
  3. Visual Chart Decomposition (Chart type, axes, data series, captions)
  4. Preserving Relational Semantics across Multi-Column Complex Layouts
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from pydantic import BaseModel, Field

from documents import MultimodalDocument, TableStructure, TableCell, ChartStructure, CORPUS


class ParsedCellCoordinate(BaseModel):
    """Pinpoint cell coordinate in a complex document layout."""
    doc_id: str
    doc_title: str
    table_id: str
    table_title: str
    page: int
    row_idx: int
    row_header: str
    col_idx: int
    col_header: str
    cell_value: str
    numeric_value: Optional[float] = None


class LayoutAwareParser:
    """Parses multimodal documents preserving 2D table structures and chart semantics."""

    def __init__(self, corpus: Dict[str, MultimodalDocument] = CORPUS):
        self.corpus = corpus
        self.cell_index: List[ParsedCellCoordinate] = []
        self.table_index: Dict[str, TableStructure] = {}
        self.chart_index: Dict[str, ChartStructure] = {}
        self._index_all_documents()

    def _parse_numeric(self, val_str: str) -> Optional[float]:
        """Safely extracts numeric float from strings like '$19.6M', '74.2%', '14 days'."""
        cleaned = val_str.replace("$", "").replace(",", "").replace("%", "").strip()
        # Handle Million ($M)
        if cleaned.endswith("M"):
            try:
                return float(cleaned[:-1]) * 1_000_000.0
            except ValueError:
                pass
        # Handle plain numbers
        match = re.search(r"[-+]?\d*\.?\d+", cleaned)
        if match:
            try:
                return float(match.group(0))
            except ValueError:
                pass
        return None

    def _index_all_documents(self):
        """Indexes every table cell with exact 2D coordinates across the corpus."""
        for doc_id, doc in self.corpus.items():
            # 1. Index Tables & Cells
            for tbl in doc.tables:
                self.table_index[tbl.table_id] = tbl
                row_key = tbl.column_headers[0]  # First column is typically the row header

                for row_idx, row_dict in enumerate(tbl.rows):
                    row_header_val = row_dict.get(row_key, f"Row_{row_idx}")

                    for col_idx, col_header in enumerate(tbl.column_headers):
                        val = row_dict.get(col_header, "")
                        num_val = self._parse_numeric(val)

                        cell_coord = ParsedCellCoordinate(
                            doc_id=doc.doc_id,
                            doc_title=doc.title,
                            table_id=tbl.table_id,
                            table_title=tbl.title,
                            page=tbl.page,
                            row_idx=row_idx,
                            row_header=row_header_val,
                            col_idx=col_idx,
                            col_header=col_header,
                            cell_value=val,
                            numeric_value=num_val,
                        )
                        self.cell_index.append(cell_coord)
                        tbl.cells.append(TableCell(
                            row_idx=row_idx,
                            row_header=row_header_val,
                            col_idx=col_idx,
                            col_header=col_header,
                            value=val,
                            numeric_value=num_val,
                        ))

            # 2. Index Charts
            for chart in doc.charts:
                self.chart_index[chart.chart_id] = chart

    def format_table_as_markdown(self, table_id: str) -> str:
        """Renders table structure as an aligned Markdown table."""
        tbl = self.table_index.get(table_id)
        if not tbl:
            return ""

        headers = tbl.column_headers
        lines = [
            f"### {tbl.title} [{tbl.table_id} - Page {tbl.page}]",
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
        ]

        for r in tbl.rows:
            row_vals = [r.get(h, "") for h in headers]
            lines.append("| " + " | ".join(row_vals) + " |")

        if tbl.footnote:
            lines.append(f"\n*{tbl.footnote}*")

        return "\n".join(lines)

    def search_cells(
        self,
        row_query: Optional[str] = None,
        col_query: Optional[str] = None,
        table_id: Optional[str] = None,
    ) -> List[ParsedCellCoordinate]:
        """Finds matching cells based on row and column header semantics."""
        matches = []
        for cell in self.cell_index:
            if table_id and cell.table_id != table_id:
                continue

            row_match = True
            if row_query:
                row_match = row_query.lower() in cell.row_header.lower()

            col_match = True
            if col_query:
                col_match = col_query.lower() in cell.col_header.lower()

            if row_match and col_match:
                matches.append(cell)

        return matches


# Singleton parser instance
layout_parser = LayoutAwareParser()
