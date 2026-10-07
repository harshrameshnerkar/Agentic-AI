"""
main.py
=======
DAY 3 — SESSION 4: FULL PRODUCTION RAG PIPELINE
===============================================

Canonical Pipeline Architecture:
1. INGESTION  (ingestion.py)  -> Loads PDFs, chunks text, embeds, and stores in Chroma
2. RETRIEVAL  (retrieval.py)  -> Bi-Encoder vector search fetches Top-K candidates
3. RERANKER   (reranker.py)   -> Cross-Encoder token-level self-attention re-scores to Top-N
4. LLM        (llm.py)        -> Context Injection, Grounding prompt, and Cited LLM synthesis
5. PIPELINE   (pipeline.py)   -> Master orchestrator executing the end-to-end workflow
6. QA BOT     (qa_bot.py)     -> Interactive CLI and automated benchmark harness
"""

import sys
import time
from pathlib import Path

# Force UTF-8 terminal output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from ingestion import IngestionPipeline
from retrieval import Retriever
from reranker import CrossEncoderReranker
from llm import LLMGenerator
from pipeline import RAGPipeline
from qa_bot import format_bot_response


def main():
    print("=" * 85)
    print(" DAY 3 — SESSION 4: INGESTION -> RETRIEVAL -> RERANKER -> LLM PIPELINE")
    print("=" * 85)

    docs_dir = Path(__file__).parent / "docs"

    # -----------------------------------------------------------------------
    # STAGE 1: INGESTION PIPELINE (ingestion.py)
    # -----------------------------------------------------------------------
    print("\n" + "=" * 85)
    print(" [STAGE 1: INGESTION] Loading PDFs, Chunking, Embedding, and Storing")
    print("=" * 85)
    ingestion = IngestionPipeline(persist_directory="./chroma_db", collection_name="session_4_rag")
    doc_count = ingestion.run(docs_dir)

    # -----------------------------------------------------------------------
    # INITIALIZE RETRIEVAL, RERANKER, AND LLM GENERATOR
    # -----------------------------------------------------------------------
    retriever = Retriever(persist_directory="./chroma_db", collection_name="session_4_rag")
    reranker = CrossEncoderReranker()
    llm = LLMGenerator()

    # Compose into master pipeline
    pipeline = RAGPipeline(
        ingestion=ingestion,
        retriever=retriever,
        reranker=reranker,
        llm=llm,
    )

    # -----------------------------------------------------------------------
    # DEMONSTRATION OF STAGES 2, 3, 4: RETRIEVAL -> RERANKER -> LLM
    # -----------------------------------------------------------------------
    print("\n" + "=" * 85)
    print(" [STAGES 2, 3, 4: RETRIEVAL -> RERANKER -> LLM] Walkthrough on Enterprise Query")
    print("=" * 85)
    sample_query = "What is the daily meal per diem allowance, and what are the emergency travel insurance policy details and hotline?"
    print(f"User Query: '{sample_query}'\n")

    # Step A: Retrieval
    candidates = retriever.retrieve(sample_query, top_k=6)
    print("  • Stage 2 (Retrieval - Bi-Encoder): Retrieved Top-6 candidates from Chroma:")
    for c in candidates:
        print(f"      - Rank #{c.bi_encoder_rank}: {c.source} (Page {c.page}) | Cosine Sim: {c.similarity:.4f}")

    # Step B: Reranker
    reranked = reranker.rerank(sample_query, candidates, top_n=3)
    print("\n  • Stage 3 (Reranker - Cross-Encoder): Joint self-attention re-ordered candidates:")
    for r in reranked:
        shift = f"(moved from #{r.bi_encoder_rank} to #{r.reranker_rank})" if r.bi_encoder_rank != r.reranker_rank else "(maintained rank)"
        print(f"      - Rank #{r.reranker_rank}: {r.source} (Page {r.page}) | Logit: {r.rerank_score:+.2f} | Prob: {r.relevance_prob*100:.1f}% {shift}")

    # Step C: LLM Generation with Context Injection
    print("\n  • Stage 4 (LLM - Context Injection & Grounded Synthesis):")
    result = pipeline.query(sample_query, retrieval_top_k=6, rerank_top_n=3)
    print(format_bot_response(result))

    # -----------------------------------------------------------------------
    # DEMONSTRATION: HANDLING NO-RELEVANT-RESULTS (SAFE REFUSAL)
    # -----------------------------------------------------------------------
    print("\n" + "=" * 85)
    print(" [RELEVANCE GUARD] Demonstrating Safe Refusal on Out-of-Domain Query")
    print("=" * 85)
    trick_query = "What is the recommended recipe, baking temperature, and yeast ratio for sourdough bread?"
    print(f"Trick Query: '{trick_query}'\n")

    refusal_result = pipeline.query(trick_query, retrieval_top_k=6, rerank_top_n=3)
    print(format_bot_response(refusal_result))

    # -----------------------------------------------------------------------
    # TECHNICAL QUERY DEMONSTRATION: DATABASE MIGRATION GUIDE
    # -----------------------------------------------------------------------
    print("\n" + "=" * 85)
    print(" [TECHNICAL TEST] Evaluating Core Runbook Procedures (Database Migration)")
    print("=" * 85)
    time.sleep(3.5)  # Pace chat completions
    db_query = "When is the cutover window scheduled, what DNS TTL is required, and what conditions trigger an automated rollback?"
    print(f"Technical Query: '{db_query}'\n")

    db_result = pipeline.query(db_query, retrieval_top_k=6, rerank_top_n=3)
    print(format_bot_response(db_result))

    # -----------------------------------------------------------------------
    # ARCHITECTURAL SUMMARY
    # -----------------------------------------------------------------------
    print("\n" + "=" * 85)
    print(" PIPELINE ARCHITECTURE SUMMARY")
    print("=" * 85)
    print(
        """
Canonical Production Flow:
1. Ingestion (ingestion.py):
   PDFs -> Recursive Chunking (300 tokens) -> Gemini Embeddings -> Persistent Chroma.

2. Retrieval (retrieval.py):
   Query -> Gemini Bi-Encoder Embedding -> HNSW Cosine Search (Top-K in ~5ms).

3. Reranker (reranker.py):
   [CLS] Query [SEP] Passage [SEP] -> ms-marco Cross-Encoder (Scores Top-K in ~25ms).

4. LLM & Context Injection (llm.py):
   Provenance Excerpts -> Grounding Prompt -> gemini-3.5-flash-lite -> Cited Page Answer.

5. Orchestrator (pipeline.py):
   Chains all 4 stages cleanly with a Relevance Guard to stop hallucinations.
"""
    )


if __name__ == "__main__":
    main()
