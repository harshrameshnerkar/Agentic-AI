"""
Naive Always-Retrieve Baseline System for Day 11 Session 1.
Implements the standard un-routed baseline:
- Always performs vector retrieval for every query, regardless of intent.
- Injects top-k retrieved documents into prompt context.
- Suffers from context pollution on SQL queries, chitchat, and math.
"""

import time
from typing import Dict, Any, List
from vector_store import EnterpriseVectorStore, vector_store


class NaiveAlwaysRetrieveRAG:
    """Baseline RAG system that blindly retrieves vector chunks for all queries."""

    def __init__(self, store: EnterpriseVectorStore = vector_store):
        self.store = store

    def run(self, query: str, top_k: int = 2) -> Dict[str, Any]:
        t0 = time.perf_counter()

        # Step 1: Blind vector retrieval (No routing, no filter extraction)
        retrieved_docs = self.store.search(query=query, top_k=top_k)

        # Step 2: Context Assembly
        context_str = "\n\n".join([
            f"[{d['doc_id']}: {d['title']}]\n{d['content']}"
            for d in retrieved_docs
        ]) if retrieved_docs else "No documents found."

        # Step 3: Synthesis
        # Check if the retrieved documents actually answer the query
        q_lower = query.lower()

        # Handle greetings / math under naive RAG (often polluted by retrieved context)
        if any(g in q_lower for g in ["hello", "hi", "who are you"]):
            final_answer = (
                f"Hello! I am an enterprise assistant. (Note: Retrieved context from "
                f"{[d['doc_id'] for d in retrieved_docs]}: {retrieved_docs[0]['title'] if retrieved_docs else 'None'})."
            )
        elif any(c in q_lower for c in ["calculate", "what is 2 + 2", "15 * 80", "reverse a string"]):
            final_answer = "420 (calculated, but context was retrieved unnecessarily)."
        elif any(s in q_lower for s in ["how many", "count", "total revenue", "average salary", "orders", "inventory", "stock"]):
            # Naive RAG FAILS on SQL tabular data: documents do not contain live database rows!
            final_answer = (
                f"Based on the retrieved documentation ({[d['doc_id'] for d in retrieved_docs]}), "
                f"I cannot determine the exact database count or quantitative metric because our unstructured documents "
                f"do not contain live SQL records."
            )
        else:
            # Semantic query answering using retrieved docs
            if retrieved_docs:
                top_doc = retrieved_docs[0]
                final_answer = (
                    f"According to **[{top_doc['doc_id']}: {top_doc['title']}]**:\n\n"
                    f"{top_doc['content']}"
                )
            else:
                final_answer = "No relevant enterprise documentation was found."

        latency_ms = (time.perf_counter() - t0) * 1000.0

        # Estimated token consumption (system prompt + context chunks + query + output)
        prompt_tokens = 150 + sum(len(d["content"].split()) for d in retrieved_docs)
        completion_tokens = len(final_answer.split())
        total_tokens = prompt_tokens + completion_tokens

        return {
            "query": query,
            "architecture": "Naive_Always_Retrieve",
            "route_chosen": "vector_search",  # Always forced to vector
            "docs_retrieved_count": len(retrieved_docs),
            "retrieved_doc_ids": [d["doc_id"] for d in retrieved_docs],
            "context_pollution": len(retrieved_docs) > 0 and any(
                k in q_lower for k in ["hello", "count", "salary", "orders", "calculate"]
            ),
            "final_answer": final_answer,
            "latency_ms": round(latency_ms, 2),
            "tokens_used": total_tokens,
            "cost_usd": round(total_tokens * (0.1425 / 1_000_000), 8),
        }


# Singleton baseline
naive_rag = NaiveAlwaysRetrieveRAG()
