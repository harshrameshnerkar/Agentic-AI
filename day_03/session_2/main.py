"""
Day 03 - Session 02: Chunking & Ingestion
Compares small (300 tokens) vs large (800 tokens) chunking strategies
for retrieval accuracy and token efficiency.
"""

from pathlib import Path
from pdf_loader import load_all_pdfs
from chunker import chunk_documents
from embedder import Embedder
from retriever import VectorRetriever
from evaluator import BenchmarkEvaluator


def main():
    print("=== Day 3 Session 2: Chunking Benchmark ===")
    docs_dir = Path(__file__).parent / "docs"

    if not docs_dir.exists() or len(list(docs_dir.glob("*.pdf"))) < 3:
        print("Generating sample PDFs...")
        from generate_sample_docs import generate_all_sample_pdfs
        generate_all_sample_pdfs()

    # 1. Load PDFs
    documents = load_all_pdfs(docs_dir)
    print(f"Loaded {len(documents)} document pages.")

    # 2. Chunk documents with two strategies
    chunks_300 = chunk_documents(documents, chunk_size_tokens=300, chunk_overlap_tokens=50)
    chunks_800 = chunk_documents(documents, chunk_size_tokens=800, chunk_overlap_tokens=100)
    print(f"Generated {len(chunks_300)} small chunks (300 tokens) and {len(chunks_800)} large chunks (800 tokens).")

    # 3. Embed chunks
    embedder = Embedder()
    vectors_300 = embedder.embed_texts([c.page_content for c in chunks_300], cache_key="chunks_300_embeddings")
    vectors_800 = embedder.embed_texts([c.page_content for c in chunks_800], cache_key="chunks_800_embeddings")

    # 4. Evaluate retrieval accuracy
    retriever_300 = VectorRetriever("300-Token", chunks_300, vectors_300)
    retriever_800 = VectorRetriever("800-Token", chunks_800, vectors_800)

    evaluator = BenchmarkEvaluator(embedder, retriever_300, retriever_800)
    results = evaluator.run_benchmark(top_k=2)

    print("\nBenchmark Results Summary:")
    for r in results:
        t300 = r["config_300"]["total_tokens"]
        t800 = r["config_800"]["total_tokens"]
        f300 = r["config_300"]["answer_fact_coverage"]
        f800 = r["config_800"]["answer_fact_coverage"]
        print(f"  Q: '{r['question'][:40]}...'")
        print(f"     300-tok: {t300} tokens, {f300:.0f}% fact coverage")
        print(f"     800-tok: {t800} tokens, {f800:.0f}% fact coverage\n")


if __name__ == "__main__":
    main()
