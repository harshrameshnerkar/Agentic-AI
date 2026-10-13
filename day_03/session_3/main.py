"""
Day 03 - Session 03: Vector Databases & Metadata Filtering
Demonstrates Chroma vector database lifecycle:
  1. Chunk loading & metadata enrichment
  2. Idempotent upsert & persistence
  3. Pre-filtering vs post-filtering
  4. FAISS index benchmarks (Flat vs IVF vs HNSW)
"""

from pathlib import Path
from chunk_provider import get_enriched_chunks, load_cached_embeddings_if_available
from embedder import Embedder
from chroma_manager import ChromaStore
from filter_benchmark import run_metadata_filter_experiments
from faiss_benchmark import run_index_type_benchmark
from vector_db_comparisons import print_comparison_matrix


def main():
    print("=== Day 3 Session 3: Vector Databases & Filtering ===")
    persist_dir = Path(__file__).parent / "chroma_db"

    # 1. Load chunks
    chunks = get_enriched_chunks()
    print(f"Loaded {len(chunks)} enriched chunks.")

    # 2. Get embeddings
    embeddings = load_cached_embeddings_if_available(chunks)
    if embeddings is None:
        embedder = Embedder()
        embeddings = embedder.embed_texts([c.page_content for c in chunks], cache_key="session_3_chunks")
    else:
        embedder = Embedder()

    # 3. Initialize ChromaStore and upsert
    store = ChromaStore(
        persist_directory=str(persist_dir),
        collection_name="enterprise_governance",
        distance_metric="cosine",
    )
    store.upsert_chunks(chunks, embeddings)
    print(f"Collection count: {store.count()} chunks in Chroma.")

    # 4. Metadata filtering experiments
    print("\nRunning metadata filter experiments...")
    filter_experiments = run_metadata_filter_experiments(store, embedder)
    for exp in filter_experiments:
        print(f"  [{exp['id']}] {exp['title']}")

    # 5. Index type performance benchmark
    print("\nBenchmarking index types (Flat vs IVF vs HNSW)...")
    index_results = run_index_type_benchmark(embeddings)
    for name, data in index_results.items():
        print(f"  {name:<14}: {data['query_latency_us']:.1f} µs latency, {data['recall']*100:.0f}% recall")

    # 6. Database comparison matrix
    print("\nVector Database Comparison:")
    print_comparison_matrix()


if __name__ == "__main__":
    main()
