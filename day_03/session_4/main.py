"""
Day 03 - Session 04: Full Production RAG Pipeline
Orchestrates:
  1. Ingestion: PDF chunking & ChromaDB storage
  2. Retrieval: Bi-encoder vector search
  3. Reranker: Cross-encoder scoring
  4. LLM Generation: Grounded answer synthesis with source citations
"""

from pathlib import Path
from ingestion import IngestionPipeline
from retrieval import Retriever
from reranker import CrossEncoderReranker
from llm import LLMGenerator
from pipeline import RAGPipeline
from qa_bot import format_bot_response


def main():
    print("=== Day 3 Session 4: Full RAG Pipeline ===")
    docs_dir = Path(__file__).parent / "docs"

    # 1. Ingest documents
    ingestion = IngestionPipeline(persist_directory="./chroma_db", collection_name="session_4_rag")
    ingestion.run(docs_dir)

    # 2. Setup pipeline components
    retriever = Retriever(persist_directory="./chroma_db", collection_name="session_4_rag")
    reranker = CrossEncoderReranker()
    llm = LLMGenerator()

    pipeline = RAGPipeline(
        ingestion=ingestion,
        retriever=retriever,
        reranker=reranker,
        llm=llm,
    )

    # 3. Test on an enterprise query
    query = "What is the daily meal per diem allowance, and what are the emergency travel insurance policy details?"
    print(f"\nUser Query: '{query}'")
    result = pipeline.query(query, retrieval_top_k=6, rerank_top_n=3)
    print(format_bot_response(result))

    # 4. Test safe refusal on out-of-domain query
    out_of_domain = "What is the recommended recipe and baking temperature for sourdough bread?"
    print(f"\nTesting Out-of-Domain Query: '{out_of_domain}'")
    refusal = pipeline.query(out_of_domain, retrieval_top_k=6, rerank_top_n=3)
    print(format_bot_response(refusal))


if __name__ == "__main__":
    main()
