"""
Prompt Compression & Observation Compactor Module.
Implements:
1. System Prompt Compression (Stripping few-shot bloat & verbosity).
2. Tool Schema Compaction (Concise parameter definitions).
3. Observation Compaction (Minifying raw database and log outputs to slash prompt token bloat).
"""

import json
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# 1. Baseline System Prompt (Monolithic & Bloated: ~950 tokens)
# ---------------------------------------------------------------------------
BASELINE_BLOATED_SYSTEM_PROMPT = """You are an Enterprise Virtual Autonomous Assistant Agent operating on behalf of the internal engineering, operations, finance, and customer support organizations.

DETAILED MANDATORY OPERATIONAL GUIDELINES AND PHILOSOPHICAL CONSTRAINTS:
1. Always strive to provide exhaustive, fully fleshed out, and elaborately structured responses to every question asked by any user under any circumstance.
2. When interacting with relational databases, make sure to consider all aspects of relational calculus, schema consistency, entity relationships, and table integrity before and after executing queries.
3. When searching documentation, carefully read every single sentence of internal policies, standard operating procedures, technical architecture documents, and security protocols.
4. When performing mathematical calculations, double-check all arithmetic operations, floating-point precision, rounding rules, and algebraic properties.
5. When inspecting filesystem paths, always verify directory existence, file permissions, and timestamp metadata.

FEW-SHOT DEMONSTRATION EXAMPLES:
Example 1:
User: "Show me customer C-101."
Thought: The user is asking for customer record C-101. I should query the database table named customers with filter column customer_id and value C-101.
Action: query_database(table="customers", filter_column="customer_id", filter_value="C-101")
Observation: [{"customer_id": "C-101", "name": "Acme Corp", "tier": "Enterprise", "mrr": 12500, "status": "Active"}]
Answer: Customer C-101 is Acme Corp, which is in the Enterprise tier with an MRR of $12,500 and an Active status.

Example 2:
User: "What is 50 * 20?"
Thought: The user wants me to calculate 50 times 20.
Action: calculate(expression="50 * 20")
Observation: 1000.0
Answer: The product of 50 and 20 is 1000.

Example 3:
User: "Check /var/log/syslog."
Thought: The user wants to inspect the syslog file.
Action: read_log(path="/var/log/syslog")
Observation: 2026-10-06T04:12:00Z [INFO] Service started...
Answer: The syslog file shows that the service started at 04:12:00Z.

Please follow these detailed patterns, verbose thinking steps, and thorough methodologies at all times.
"""

# ---------------------------------------------------------------------------
# 2. Optimized System Prompt (Lean & Compressed: ~75 tokens)
# ---------------------------------------------------------------------------
OPTIMIZED_COMPRESSED_SYSTEM_PROMPT = """You are an accurate, concise Enterprise Assistant.
Tools available: query_database, search_docs, calculate, read_log.
Use the most specific tool, perform necessary calculations, and provide direct, factual answers.
"""


class ObservationCompactor:
    """Compacts tool outputs into token-efficient representations."""

    @staticmethod
    def compact_db_output(raw_rows: List[Dict[str, Any]]) -> str:
        """Converts bloated JSON array into compact pipe-delimited records."""
        if not raw_rows:
            return "rows: 0"
        # Extract headers from first row
        headers = list(raw_rows[0].keys())
        lines = [",".join(headers)]
        for r in raw_rows:
            lines.append(",".join(str(r.get(h, "")) for h in headers))
        return "\n".join(lines)

    @staticmethod
    def compact_log_output(log_text: str, max_lines: int = 4) -> str:
        """Filters log to error/warning lines only, truncating noise."""
        lines = log_text.strip().split("\n")
        relevant = [l for l in lines if any(lvl in l for lvl in ["[WARN]", "[ERROR]", "[FATAL]", "timeout"])]
        if not relevant:
            relevant = lines[-max_lines:]
        return "\n".join(relevant[:max_lines])

    @staticmethod
    def compact_doc_output(docs: List[Dict[str, Any]]) -> str:
        """Condenses doc search results to key excerpts."""
        if not docs:
            return "no matches"
        summaries = [f"{d.get('doc_id')}: {d.get('content', '')[:120]}" for d in docs]
        return " | ".join(summaries)
