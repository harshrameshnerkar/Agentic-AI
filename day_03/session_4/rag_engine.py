"""
rag_engine.py
=============
Full Production RAG Engine (Day 3 - Session 4)

Pipeline Architecture (5 Stages):
1. Retrieve: Fast Bi-Encoder vector search in Chroma (Top-K candidates)
2. Rerank: Cross-Encoder token-level self-attention re-scoring (Top-N)
3. Relevance Guard: Refusal to hallucinate when context relevance is below threshold
4. Assemble: Provenance-tagged context assembly with strict grounding instructions
5. Answer: LLM synthesis with verifiable per-page source citations
"""

import os
import time
import re
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

from vector_store import VectorStore
from reranker import CrossEncoderReranker

load_dotenv()

BASE_URL = os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
API_KEY = os.getenv("OPENAI_API_KEY")
CHAT_MODEL = os.getenv("OPENAI_MODEL", "gemini-3.5-flash-lite")

# Relevance threshold: cross-encoder logits below this value indicate irrelevant queries
RELEVANCE_THRESHOLD = -2.5


class RAGEngine:
    """
    End-to-end RAG orchestrator integrating Bi-Encoder retrieval,
    Cross-Encoder reranking, grounding guards, and cited answer synthesis.
    """
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        reranker: Optional[CrossEncoderReranker] = None,
        relevance_threshold: float = RELEVANCE_THRESHOLD,
    ):
        self.vector_store = vector_store or VectorStore()
        self.reranker = reranker or CrossEncoderReranker()
        self.relevance_threshold = relevance_threshold
        self.openai_client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

    def answer_query(
        self,
        query: str,
        retrieval_top_k: int = 6,
        rerank_top_n: int = 3,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Executes the full RAG pipeline for a given user query.

        Args:
            query: User's question.
            retrieval_top_k: Number of candidates to fetch in Stage 1.
            rerank_top_n: Number of candidates to select after Cross-Encoder Stage 2.
            temperature: LLM sampling temperature (0.0 for strict factual answers).

        Returns:
            Dictionary with generated answer, citations, candidate comparisons,
            and refusal telemetry.
        """
        t_start = time.perf_counter()

        # -------------------------------------------------------------------
        # STAGE 1: Bi-Encoder Candidate Retrieval
        # -------------------------------------------------------------------
        t0 = time.perf_counter()
        initial_candidates = self.vector_store.retrieve_candidates(query, top_k=retrieval_top_k)
        retrieval_latency = time.perf_counter() - t0

        if not initial_candidates:
            return {
                "query": query,
                "answer": "No relevant documentation could be retrieved from the vector index.",
                "is_refusal": True,
                "retrieved_candidates": [],
                "reranked_candidates": [],
                "citations": [],
                "total_latency_ms": round((time.perf_counter() - t_start) * 1000, 2),
            }

        # -------------------------------------------------------------------
        # STAGE 2: Cross-Encoder Reranking
        # -------------------------------------------------------------------
        t0 = time.perf_counter()
        reranked_candidates = self.reranker.rerank(query, initial_candidates, top_n=rerank_top_n)
        rerank_latency = time.perf_counter() - t0

        top_score = reranked_candidates[0]["rerank_score"] if reranked_candidates else -999.0

        # -------------------------------------------------------------------
        # STAGE 3: Relevance Guard (Handling No-Relevant-Results)
        # -------------------------------------------------------------------
        if top_score < self.relevance_threshold:
            # Query is out-of-domain or semantically irrelevant. Refuse to hallucinate!
            refusal_answer = (
                "I am sorry, but the provided enterprise documentation (CloudPlatform SLA, "
                "Employee Travel Policy, Database Migration Guide) does not contain information "
                f"relevant to answer your question: '{query}'."
            )
            return {
                "query": query,
                "answer": refusal_answer,
                "is_refusal": True,
                "refusal_reason": f"Top cross-encoder score ({top_score:.2f}) fell below relevance threshold ({self.relevance_threshold}).",
                "retrieved_candidates": initial_candidates,
                "reranked_candidates": reranked_candidates,
                "citations": [],
                "total_latency_ms": round((time.perf_counter() - t_start) * 1000, 2),
            }

        # -------------------------------------------------------------------
        # STAGE 4: Assemble Context with Grounding Rules & Provenance
        # -------------------------------------------------------------------
        context_blocks = []
        for c in reranked_candidates:
            header = f"[DOCUMENT EXCERPT: {c['source']} | Page: {c['page']} | Chunk: {c['id']}]"
            context_blocks.append(f"{header}\n{c['content']}")

        joined_context = "\n\n" + ("=" * 60) + "\n\n".join(context_blocks)

        system_prompt = """You are an enterprise compliance and technical Q&A assistant.
Your answers MUST be strictly grounded in the provided document excerpts.

MANDATORY GROUNDING RULES:
1. Strict Fidelity: Answer solely using the facts explicitly stated in the context. Never speculate or extrapolate.
2. In-Line Citations: For EVERY factual rule, metric, policy number, or threshold you state, you MUST cite the exact source and page in square brackets, for example:
   [Source: employee_travel_policy.pdf, Page: 2]
3. Missing Details: If the context answers only part of the question, state what is known and explicitly add:
   "The documentation does not provide details regarding [missing part]."
4. Structured Formatting: Use bullet points and bold headers for clarity."""

        user_prompt = f"""CONTEXT EXCERPTS:
{joined_context}

QUESTION:
{query}

ANSWER (with in-line source and page citations):"""

        # -------------------------------------------------------------------
        # STAGE 5: LLM Synthesis with Citations
        # -------------------------------------------------------------------
        t0 = time.perf_counter()
        try:
            response = self.openai_client.chat.completions.create(
                model=CHAT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                timeout=30.0,
            )
            generated_answer = response.choices[0].message.content.strip()
        except Exception as e:
            generated_answer = f"Error during answer generation: {e}"
        llm_latency = time.perf_counter() - t0

        # Extract cited pages from generated text via regex
        citations_found = list(set(re.findall(r"\[Source:\s*([^,\]]+),\s*Page:\s*(\d+)\]", generated_answer)))

        total_latency = time.perf_counter() - t_start

        return {
            "query": query,
            "answer": generated_answer,
            "is_refusal": False,
            "top_rerank_score": top_score,
            "retrieved_candidates": initial_candidates,
            "reranked_candidates": reranked_candidates,
            "citations": [f"{doc} (P{page})" for doc, page in citations_found],
            "latency": {
                "retrieval_ms": round(retrieval_latency * 1000, 1),
                "rerank_ms": round(rerank_latency * 1000, 1),
                "llm_ms": round(llm_latency * 1000, 1),
                "total_ms": round(total_latency * 1000, 1),
            },
        }


if __name__ == "__main__":
    from pathlib import Path

    print("Initializing RAGEngine...")
    engine = RAGEngine()
    docs_dir = Path(__file__).parent / "docs"
    engine.vector_store.ingest_documents(docs_dir)

    test_q = "What is the emergency medical travel insurance policy number and 24/7 hotline?"
    print(f"\nAsking test question: '{test_q}'")
    res = engine.answer_query(test_q)
    print("\n--- Answer Generated ---")
    print(res["answer"])
    print("\nCitations Detected:", res["citations"])
    print("Latency:", res["latency"])
