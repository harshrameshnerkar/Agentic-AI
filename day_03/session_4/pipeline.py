"""
pipeline.py
===========
END-TO-END RAG PIPELINE (Day 3 - Session 4)

Composes the 4 specialized stages into a unified, production-grade architecture:
1. IngestionPipeline (ingestion.py) -> Loads, chunks, embeds, and indexes PDFs
2. Retriever         (retrieval.py) -> Performs fast Bi-Encoder vector candidate search
3. CrossEncoderReranker (reranker.py) -> Jointly re-scores candidates with self-attention
4. LLMGenerator     (llm.py)       -> Injects context, enforces grounding, and cites pages
"""

import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from ingestion import IngestionPipeline
from retrieval import Retriever, CandidatePassage
from reranker import CrossEncoderReranker, RerankedPassage
from llm import LLMGenerator, LLMResponse

DEFAULT_RELEVANCE_THRESHOLD = -2.5


class RAGQueryResult:
    """
    Comprehensive result object encapsulating answer, citations, candidate telemetry,
    and stage-by-stage latency.
    """
    def __init__(
        self,
        query: str,
        answer: str,
        citations: List[str],
        is_refusal: bool,
        refusal_reason: Optional[str] = None,
        retrieved_candidates: Optional[List[CandidatePassage]] = None,
        reranked_candidates: Optional[List[RerankedPassage]] = None,
        latency: Optional[Dict[str, float]] = None,
    ):
        self.query = query
        self.answer = answer
        self.citations = citations
        self.is_refusal = is_refusal
        self.refusal_reason = refusal_reason
        self.retrieved_candidates = retrieved_candidates or []
        self.reranked_candidates = reranked_candidates or []
        self.latency = latency or {}

    @property
    def total_latency_ms(self) -> float:
        return self.latency.get("total_ms", 0.0)


class RAGPipeline:
    """
    Master pipeline unifying Ingestion, Retrieval, Reranking, and LLM Generation.
    """
    def __init__(
        self,
        ingestion: Optional[IngestionPipeline] = None,
        retriever: Optional[Retriever] = None,
        reranker: Optional[CrossEncoderReranker] = None,
        llm: Optional[LLMGenerator] = None,
        relevance_threshold: float = DEFAULT_RELEVANCE_THRESHOLD,
    ):
        self.ingestion = ingestion or IngestionPipeline()
        self.retriever = retriever or Retriever()
        self.reranker = reranker or CrossEncoderReranker()
        self.llm = llm or LLMGenerator()
        self.relevance_threshold = relevance_threshold

    def ingest_documents(self, docs_directory: Path) -> int:
        """Runs Stage 1: Document Ingestion into Vector Store."""
        return self.ingestion.run(docs_directory)

    def query(
        self,
        user_query: str,
        retrieval_top_k: int = 6,
        rerank_top_n: int = 3,
        temperature: float = 0.0,
    ) -> RAGQueryResult:
        """
        Executes query pipeline:
        1. Retrieval (Bi-Encoder)
        2. Reranking (Cross-Encoder)
        3. Relevance Guard (No-Relevant-Results check)
        4. Context Injection & Grounded LLM Answer Synthesis
        """
        t_start = time.perf_counter()

        # -------------------------------------------------------------------
        # 1. RETRIEVAL (Bi-Encoder Vector Search)
        # -------------------------------------------------------------------
        t0 = time.perf_counter()
        candidates = self.retriever.retrieve(user_query, top_k=retrieval_top_k)
        retrieval_ms = (time.perf_counter() - t0) * 1000

        if not candidates:
            return RAGQueryResult(
                query=user_query,
                answer="No documents found in the vector index.",
                citations=[],
                is_refusal=True,
                refusal_reason="Vector database returned zero candidates.",
                latency={"total_ms": (time.perf_counter() - t_start) * 1000},
            )

        # -------------------------------------------------------------------
        # 2. RERANKING (Cross-Encoder Token-Level Scoring)
        # -------------------------------------------------------------------
        t0 = time.perf_counter()
        reranked = self.reranker.rerank(user_query, candidates, top_n=rerank_top_n)
        rerank_ms = (time.perf_counter() - t0) * 1000

        top_score = reranked[0].rerank_score if reranked else -999.0

        # -------------------------------------------------------------------
        # 3. RELEVANCE GUARD (Handling No-Relevant-Results)
        # -------------------------------------------------------------------
        if top_score < self.relevance_threshold:
            refusal_text = (
                "I am sorry, but the provided enterprise documentation (CloudPlatform SLA, "
                "Employee Travel Policy, Database Migration Guide) does not contain information "
                f"relevant to answer your question: '{user_query}'."
            )
            total_ms = (time.perf_counter() - t_start) * 1000
            return RAGQueryResult(
                query=user_query,
                answer=refusal_text,
                citations=[],
                is_refusal=True,
                refusal_reason=f"Top cross-encoder score ({top_score:.2f}) was below threshold ({self.relevance_threshold}).",
                retrieved_candidates=candidates,
                reranked_candidates=reranked,
                latency={
                    "retrieval_ms": round(retrieval_ms, 1),
                    "rerank_ms": round(rerank_ms, 1),
                    "total_ms": round(total_ms, 1),
                },
            )

        # -------------------------------------------------------------------
        # 4. CONTEXT INJECTION & GROUNDED LLM SYNTHESIS
        # -------------------------------------------------------------------
        t0 = time.perf_counter()
        llm_response = self.llm.generate(user_query, reranked, temperature=temperature)
        llm_ms = (time.perf_counter() - t0) * 1000

        total_ms = (time.perf_counter() - t_start) * 1000

        return RAGQueryResult(
            query=user_query,
            answer=llm_response.answer,
            citations=llm_response.citations,
            is_refusal=False,
            retrieved_candidates=candidates,
            reranked_candidates=reranked,
            latency={
                "retrieval_ms": round(retrieval_ms, 1),
                "rerank_ms": round(rerank_ms, 1),
                "llm_ms": round(llm_ms, 1),
                "total_ms": round(total_ms, 1),
            },
        )


if __name__ == "__main__":
    pipeline = RAGPipeline()
    docs_dir = Path(__file__).parent / "docs"
    pipeline.ingest_documents(docs_dir)

    result = pipeline.query("What is the guaranteed Monthly Uptime Percentage for Tier 1 services?")
    print("\n--- Pipeline Result ---")
    print("Answer:\n", result.answer)
    print("\nCitations:", result.citations)
    print("Latency:", result.latency)
