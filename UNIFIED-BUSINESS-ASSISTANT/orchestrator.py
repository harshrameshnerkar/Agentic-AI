"""
Role C Orchestrator Pipeline
Coordinates Interface 1 (Knowledge Service) and Interface 2 (Data Service)
driven by Interface 3 (Routing Decision).
Implements contract fallback handling, guardrails, and synthesized responses.
"""

from typing import Dict, Any, List, Optional
import json
import re
import urllib.request
import urllib.error 

from router import QueryRouter, RouteType, RoutingDecision
from mock_services import search_knowledge_mock, query_data_mock, query_sqlite

class RoleCOrchestrator:
    def __init__(
        self,
        knowledge_service_url: str = "http://127.0.0.1:8000/search",
        data_service_url: str = "http://127.0.0.1:8001/query",
        prefer_mock: bool = False
    ):
        self.router = QueryRouter()
        self.knowledge_url = knowledge_service_url
        self.data_url = data_service_url
        self.prefer_mock = prefer_mock

    # ──────────────────────────────────────────────────────────────────────────
    # Interface 1 Invocation (Knowledge Service)
    # ──────────────────────────────────────────────────────────────────────────
    def invoke_knowledge_service(self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Consumes Interface 1 (/search) from Role A."""
        if self.prefer_mock:
            return search_knowledge_mock(query=query, top_k=top_k, filters=filters)

        try:
            req_data = json.dumps({"query": query, "question": query, "top_k": top_k, "filters": filters or {}}).encode("utf-8")
            req = urllib.request.Request(
                self.knowledge_url,
                data=req_data,
                headers={"Content-Type": "application/json", "User-Agent": "RoleC-Orchestrator"}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                # Normalize results if field naming varies
                results = data.get("results", [])
                normalized_results = []
                for r in results:
                    normalized_results.append({
                        "text": r.get("text", ""),
                        "source": r.get("source") or r.get("source_file", "unknown_source.pdf"),
                        "page": r.get("page", 1),
                        "score": r.get("score", 0.0)
                    })
                return {
                    "results": normalized_results,
                    "no_match": data.get("no_match", len(normalized_results) == 0)
                }
        except Exception:
            # Automatic graceful fallback to mock service for Day 1
            return search_knowledge_mock(query=query, top_k=top_k, filters=filters)

    # ──────────────────────────────────────────────────────────────────────────
    # Interface 2 Invocation (Data Service)
    # ──────────────────────────────────────────────────────────────────────────
    def invoke_data_service(self, question: str) -> Dict[str, Any]:
        """Consumes Interface 2 (/query) from Role B."""
        if self.prefer_mock:
            return query_data_mock(question=question)

        try:
            req_data = json.dumps({"question": question}).encode("utf-8")
            req = urllib.request.Request(
                self.data_url,
                data=req_data,
                headers={"Content-Type": "application/json", "User-Agent": "RoleC-Orchestrator"}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            # Automatic graceful fallback to mock service for Day 1
            return query_data_mock(question=question)

    # ──────────────────────────────────────────────────────────────────────────
    # Orchestration Engine
    # ──────────────────────────────────────────────────────────────────────────
    def process_query(self, question: str) -> Dict[str, Any]:
        """
        End-to-End Orchestration Workflow:
        1. Classify route (Interface 3).
        2. Dispatch to appropriate interface(s).
        3. Handle fallbacks (answerable=false, no_match=true).
        4. Synthesize final answer with provenance (Citations & SQL).
        """
        decision: RoutingDecision = self.router.route_query(question)
        route = decision.route

        response_payload = {
            "question": question,
            "route": route.value,
            "routing_rule": decision.routing_rule,
            "fallback_rule": decision.fallback,
            "confidence": decision.confidence,
            "final_answer": "",
            "citations": [],
            "sql": None,
            "data_rows": None,
            "fallback_triggered": False
        }

        # ── ROUTE: NONE (Guardrails / Out-of-Scope) ───────────────────────────
        if route == RouteType.NONE:
            response_payload["final_answer"] = (
                f"I cannot fulfill or answer this request. {decision.routing_rule}."
            )
            return response_payload

        # ── ROUTE: DATA (Interface 2) ─────────────────────────────────────────
        if route == RouteType.DATA:
            data_res = self.invoke_data_service(question)
            
            # Check answerable flag
            if not data_res.get("answerable", False):
                # Fallback rule: If data returns answerable=false, try knowledge
                knowledge_res = self.invoke_knowledge_service(question)
                if not knowledge_res.get("no_match", True) and knowledge_res.get("results"):
                    response_payload["fallback_triggered"] = True
                    top_result = knowledge_res["results"][0]
                    response_payload["final_answer"] = (
                        f"Database schema could not answer this directly ({data_res.get('error')}). "
                        f"However, corporate policy records state:\n\n{top_result['text']}"
                    )
                    response_payload["citations"] = [
                        f"{r['source']} (Page {r['page']})" for r in knowledge_res["results"]
                    ]
                    return response_payload
                else:
                    response_payload["final_answer"] = (
                        f"I cannot answer this question. {data_res.get('error', 'The relational database schema does not support this query.')}"
                    )
                    return response_payload

            # Valid data response
            sql = data_res.get("sql", "")
            rows = data_res.get("rows", [])
            row_count = data_res.get("row_count", len(rows))
            response_payload["sql"] = sql
            response_payload["data_rows"] = rows

            # Format answer
            tables_data = data_res.get("tables_data")
            if not tables_data and sql and ";\n\n" in sql:
                multi_sqls = [s.strip() for s in sql.split(";\n\n") if s.strip()]
                if len(multi_sqls) >= 2:
                    tables_data = []
                    for s in multi_sqls:
                        stmt = s if s.endswith(";") else s + ";"
                        m = re.search(r'FROM\s+(\w+)', stmt, re.IGNORECASE)
                        t_name = m.group(1) if m else "Table"
                        t_rows = query_sqlite(stmt)
                        t_cols = list(t_rows[0].keys()) if t_rows else []
                        tables_data.append({
                            "table": t_name,
                            "sql": stmt,
                            "columns": t_cols,
                            "rows": t_rows,
                            "row_count": len(t_rows)
                        })
            if not tables_data and sql and ";\n\n" in sql:
                multi_sqls = [s.strip() for s in sql.split(";\n\n") if s.strip()]
                if len(multi_sqls) >= 2:
                    tables_data = []
                    for s in multi_sqls:
                        stmt = s if s.endswith(";") else s + ";"
                        m = re.search(r'FROM\s+(\w+)', stmt, re.IGNORECASE)
                        t_name = m.group(1) if m else "Table"
                        t_rows = query_sqlite(stmt)
                        t_cols = list(t_rows[0].keys()) if t_rows else []
                        tables_data.append({
                            "table": t_name,
                            "sql": stmt,
                            "columns": t_cols,
                            "rows": t_rows,
                            "row_count": len(t_rows)
                        })
                    row_count = sum(t["row_count"] for t in tables_data)

            if tables_data and len(tables_data) >= 2:
                answer_text = f"Executed independent structured queries for {len(tables_data)} unrelated tables (returned {row_count} total row(s)):\n\n"
                for i, t_info in enumerate(tables_data, 1):
                    t_name = t_info["table"]
                    t_rows = t_info["rows"]
                    t_cols = t_info["columns"]
                    t_sql = t_info["sql"]
                    answer_text += f"### {i}. Table: `{t_name}` ({len(t_rows)} row(s)):\n\n"
                    if t_rows:
                        answer_text += "| " + " | ".join(t_cols) + " |\n"
                        answer_text += "| " + " | ".join(["---"] * len(t_cols)) + " |\n"
                        for r in t_rows:
                            answer_text += "| " + " | ".join(str(r.get(c, "")) for c in t_cols) + " |\n"
                        answer_text += "\n"
                    answer_text += f"```sql\n{t_sql}\n```\n\n"
                response_payload["final_answer"] = answer_text
                return response_payload

            answer_text = f"Executed structured query successfully (returned {row_count} row(s)):\n\n"
            if rows:
                if len(rows) == 1 and len(rows[0]) == 1:
                    key, val = list(rows[0].items())[0]
                    answer_text += f"**{key}**: `{val}`\n\n"
                else:
                    columns = data_res.get("columns") or (list(rows[0].keys()) if rows else [])
                    answer_text += "| " + " | ".join(columns) + " |\n"
                    answer_text += "| " + " | ".join(["---"] * len(columns)) + " |\n"
                    for r in rows:
                        answer_text += "| " + " | ".join(str(r.get(c, "")) for c in columns) + " |\n"
                    answer_text += "\n"
            answer_text += f"```sql\n{sql}\n```"
            response_payload["final_answer"] = answer_text
            return response_payload

        # ── ROUTE: KNOWLEDGE (Interface 1) ────────────────────────────────────
        if route == RouteType.KNOWLEDGE:
            knowledge_res = self.invoke_knowledge_service(question)

            if knowledge_res.get("no_match", False) or not knowledge_res.get("results"):
                response_payload["final_answer"] = (
                    "I do not have corporate policy documentation regarding this query."
                )
                return response_payload

            results = knowledge_res["results"]
            seen_sources = set()
            unique_citations = []
            for r in results:
                src = r.get("source", "")
                if src and src not in seen_sources:
                    seen_sources.add(src)
                    unique_citations.append(f"{src} (Page {r.get('page', 1)})")
            response_payload["citations"] = unique_citations[:3]

            # Synthesize answer from primary passage
            primary_passage = results[0]["text"]
            response_payload["final_answer"] = primary_passage
            return response_payload

        # ── ROUTE: BOTH (Hybrid / Cross-Domain) ────────────────────────────────
        if route == RouteType.BOTH:
            data_res = self.invoke_data_service(question)
            knowledge_res = self.invoke_knowledge_service(question)

            sql = data_res.get("sql")
            rows = data_res.get("rows", [])
            results = knowledge_res.get("results", [])

            # Deduplicate citations across unique policy files
            seen_sources = set()
            unique_citations = []
            for r in results:
                src = r.get("source", "")
                if src and src not in seen_sources:
                    seen_sources.add(src)
                    unique_citations.append(f"{src} (Page {r.get('page', 1)})")

            response_payload["sql"] = sql
            response_payload["data_rows"] = rows
            response_payload["citations"] = unique_citations[:2]

            # Synthesize comparative answer
            combined_text = "### Cross-Domain Analysis (Database Entities + Corporate Policy):\n\n"
            
            tables_data = data_res.get("tables_data")
            if not tables_data and sql and ";\n\n" in sql:
                multi_sqls = [s.strip() for s in sql.split(";\n\n") if s.strip()]
                if len(multi_sqls) >= 2:
                    tables_data = []
                    for s in multi_sqls:
                        stmt = s if s.endswith(";") else s + ";"
                        m = re.search(r'FROM\s+(\w+)', stmt, re.IGNORECASE)
                        t_name = m.group(1) if m else "Table"
                        t_rows = query_sqlite(stmt)
                        t_cols = list(t_rows[0].keys()) if t_rows else []
                        tables_data.append({
                            "table": t_name,
                            "sql": stmt,
                            "columns": t_cols,
                            "rows": t_rows,
                            "row_count": len(t_rows)
                        })
            if data_res.get("answerable") and tables_data and len(tables_data) >= 2:
                combined_text += f"**1. Structured System Data**: Found {data_res.get('row_count', len(rows))} records across {len(tables_data)} independent tables:\n\n"
                for i, t_info in enumerate(tables_data, 1):
                    t_name = t_info["table"]
                    t_rows = t_info["rows"]
                    t_cols = t_info["columns"]
                    t_sql = t_info["sql"]
                    combined_text += f"#### {i}. Table: `{t_name}` ({len(t_rows)} row(s)):\n\n"
                    if t_rows:
                        combined_text += "| " + " | ".join(t_cols) + " |\n"
                        combined_text += "| " + " | ".join(["---"] * len(t_cols)) + " |\n"
                        for r in t_rows:
                            combined_text += "| " + " | ".join(str(r.get(c, "")) for c in t_cols) + " |\n"
                        combined_text += "\n"
                    combined_text += f"```sql\n{t_sql}\n```\n\n"
            elif data_res.get("answerable") and rows:
                combined_text += f"**1. Structured System Data**: Found {len(rows)} record(s) matching query criteria in the database:\n\n"
                if len(rows) == 1 and len(rows[0]) == 1:
                    key, val = list(rows[0].items())[0]
                    combined_text += f"**{key}**: `{val}`\n\n"
                else:
                    columns = data_res.get("columns") or (list(rows[0].keys()) if rows else [])
                    if columns:
                        combined_text += "| " + " | ".join(columns) + " |\n"
                        combined_text += "| " + " | ".join(["---"] * len(columns)) + " |\n"
                        for r in rows:
                            combined_text += "| " + " | ".join(str(r.get(c, "")) for c in columns) + " |\n"
                        combined_text += "\n"
                if sql:
                    combined_text += f"```sql\n{sql}\n```\n\n"
            else:
                combined_text += f"**1. Structured System Data**: {data_res.get('error', 'No direct relational table was found for this specific check.')}\n\n"

            if results and not knowledge_res.get("no_match"):
                combined_text += f"**2. Corporate Policy Framework**: According to company policy:\n\n> {results[0]['text']}\n\n"
                combined_text += "**Conclusion**: Policy regulations strictly govern business interactions and engagements involving these entities."
            else:
                combined_text += "**2. Corporate Policy Framework**: No specific restriction policy document was found for these entities."

            response_payload["final_answer"] = combined_text
            return response_payload

        return response_payload
