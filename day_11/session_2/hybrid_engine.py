"""
Day 11 - Session 2: Hybrid Structured + Unstructured Retrieval Engine
=====================================================================
Fuses:
  1. Structured Relational Data (SQL Database queries over 5 tables)
  2. Knowledge Graph Relational Subgraphs (Entities & Typed Edges)
  3. Unstructured Policy Documents (Tier SLAs, Escalation Policies, Product Specs)
To generate complete, grounded enterprise answers.
"""

import time
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

from database import db
from text_to_sql import text_to_sql_engine, TextToSQLResult
from graph_rag import knowledge_graph, EntityNode


# Authoritative Unstructured Enterprise Policy & SLA Documents
ENTERPRISE_UNSTRUCTURED_DOCS = {
    "enterprise_sla": {
        "title": "Enterprise Tier Service Level Agreement (SLA) & Escalation Policy",
        "category": "SLA_Policy",
        "content": (
            "Enterprise tier customers receive 99.99% monthly infrastructure uptime guarantee. "
            "Guaranteed response times: P1-Critical tickets require initial engineering engagement within 15 minutes "
            "with continuous 24/7 incident updates. P2-High tickets require engagement within 1 hour. "
            "Every Enterprise customer is assigned a designated Technical Account Manager (TAM) and 24/7 dedicated "
            "phone bridge. Financial service penalty: 10% monthly service credit if P1 SLA is breached for > 30 minutes."
        )
    },
    "pro_sla": {
        "title": "Pro Tier Support & Operational Guidelines",
        "category": "SLA_Policy",
        "content": (
            "Pro tier customers receive 99.9% uptime guarantee with business-hours priority queue (8 AM - 8 PM EST). "
            "P1-Critical incidents guarantee response within 1 hour; P2-High within 4 hours; P3-Normal within 24 hours. "
            "Pro tier includes standard email and portal ticketing support without dedicated phone escalation bridges."
        )
    },
    "starter_sla": {
        "title": "Starter Tier Community & Self-Service Support Terms",
        "category": "SLA_Policy",
        "content": (
            "Starter tier accounts include community forum access and standard ticket queue with best-effort 48-hour SLA. "
            "No financial uptime credits or live phone support are available for Starter tier subscribers."
        )
    },
    "gpu_a100_specs": {
        "title": "GPU Inference Accelerator A100 Deployment & Disaster Recovery Specs",
        "category": "Product_Spec",
        "content": (
            "The GPU Inference Accelerator A100 features 80GB SXM4 High-Bandwidth Memory (HBM2e) with 2.0 TB/s memory bandwidth. "
            "Recommended deployment architecture: Minimum 2-node redundancy cluster per availability zone. "
            "In case of node hardware degradation, automated failover triggers within 45 seconds to healthy hot-standby nodes."
        )
    },
    "fiber_specs": {
        "title": "Dedicated Fiber Interconnect 10Gbps Latency & Routing Policy",
        "category": "Product_Spec",
        "content": (
            "Dedicated Fiber Interconnect provides guaranteed low-latency point-to-point bandwidth of 10 Gbps with < 5ms intra-region latency. "
            "Packet loss SLA: Must remain strictly under 0.05%. Any sustained packet loss exceeding 5% triggers immediate automated "
            "route failover to BGP transit backup."
        )
    }
}


class HybridSynthesisResult(BaseModel):
    """Result of fused structured (SQL + KG) and unstructured (SLA/Docs) retrieval."""
    query: str
    structured_sql: str
    structured_rows: List[Dict[str, Any]] = Field(default_factory=list)
    linked_entities: List[str] = Field(default_factory=list)
    graph_triples: List[str] = Field(default_factory=list)
    unstructured_sources: List[str] = Field(default_factory=list)
    fused_answer: str
    latency_ms: float = 0.0


class HybridRetrievalEngine:
    """Orchestrates Text-to-SQL, Knowledge Graph traversal, and Unstructured document grounding."""

    def __init__(self):
        self.sql_engine = text_to_sql_engine
        self.kg = knowledge_graph
        self.docs = ENTERPRISE_UNSTRUCTURED_DOCS

    def answer_query(self, query: str) -> HybridSynthesisResult:
        """Executes full hybrid structured + unstructured retrieval pipeline."""
        t0 = time.perf_counter()
        q_lower = query.lower()

        # Step 1: Entity Linking & Knowledge Graph Subgraph Extraction
        linked_nodes: List[EntityNode] = self.kg.link_entities(query)
        subgraph = self.kg.get_subgraph_context(linked_nodes)

        # Step 2: Structured Relational SQL Retrieval with Pre-Execution Validation
        sql_res: TextToSQLResult = self.sql_engine.generate_and_execute(query)

        # Step 3: Unstructured Knowledge Document Matching
        matched_docs = []
        if "enterprise" in q_lower or any(n.properties.get("tier") == "Enterprise" for n in linked_nodes):
            matched_docs.append(self.docs["enterprise_sla"])
        elif "pro" in q_lower or any(n.properties.get("tier") == "Pro" for n in linked_nodes):
            matched_docs.append(self.docs["pro_sla"])
        elif "starter" in q_lower:
            matched_docs.append(self.docs["starter_sla"])

        if "gpu" in q_lower or "a100" in q_lower:
            matched_docs.append(self.docs["gpu_a100_specs"])
        if "fiber" in q_lower or "packet loss" in q_lower or "telecom" in q_lower:
            matched_docs.append(self.docs["fiber_specs"])

        # Fallback doc if none matched
        if not matched_docs:
            matched_docs.append(self.docs["enterprise_sla"])

        # Step 4: Fused Synthesis
        fused_answer = self._synthesize_hybrid_answer(
            query=query,
            sql_res=sql_res,
            subgraph=subgraph,
            matched_docs=matched_docs,
        )

        latency_ms = (time.perf_counter() - t0) * 1000.0

        return HybridSynthesisResult(
            query=query,
            structured_sql=sql_res.validated_sql,
            structured_rows=sql_res.rows,
            linked_entities=subgraph["linked_entities"],
            graph_triples=subgraph["relationship_triples"],
            unstructured_sources=[d["title"] for d in matched_docs],
            fused_answer=fused_answer,
            latency_ms=round(latency_ms, 2),
        )

    def _synthesize_hybrid_answer(
        self,
        query: str,
        sql_res: TextToSQLResult,
        subgraph: Dict[str, Any],
        matched_docs: List[Dict[str, str]],
    ) -> str:
        """Assembles structured database metrics, graph relations, and SLA documentation."""
        sections = []

        # Section 1: Executive Summary
        sections.append(f"### [Hybrid Enterprise Intelligence Briefing]\n**Query**: *\"{query}\"*\n")

        # Section 2: Structured Relational Database Findings (SQL)
        sections.append("#### 1. Live Relational Database Telemetry (Structured SQL)")
        sections.append(f"```sql\n{sql_res.validated_sql}\n```")
        if sql_res.execution_status == "SUCCESS":
            if sql_res.row_count == 1 and len(sql_res.columns) == 1:
                val = list(sql_res.rows[0].values())[0]
                col = sql_res.columns[0]
                sections.append(f"- **Database Result**: `{col}` = **{val}**")
            else:
                sections.append(f"- **Records Retrieved**: Found **{sql_res.row_count} matching record(s)**:")
                for r in sql_res.rows[:5]:
                    row_str = ", ".join([f"**{k}**: {v}" for k, v in r.items()])
                    sections.append(f"  * {row_str}")
        else:
            sections.append(f"- **SQL Notice**: {sql_res.error_message}")

        # Section 3: Entity Linking & Knowledge Graph Topology
        if subgraph.get("linked_entities"):
            sections.append("\n#### 2. Knowledge Graph Entity Linking & Topology")
            sections.append(f"- **Linked Entities**: {', '.join(subgraph['linked_entities'])}")
            if subgraph.get("relationship_triples"):
                sections.append("- **Relational Neighborhood (Graph Triples)**:")
                for trip in subgraph["relationship_triples"][:4]:
                    sections.append(f"  * `{trip}`")

        # Section 4: Grounded Unstructured Policy & SLA Documents
        if matched_docs:
            sections.append("\n#### 3. Authoritative Policy & SLA Documentation (Unstructured Context)")
            for d in matched_docs:
                sections.append(f"- **[{d['title']}]**:\n  > {d['content']}")

        return "\n".join(sections)


# Singleton hybrid engine instance
hybrid_engine = HybridRetrievalEngine()
