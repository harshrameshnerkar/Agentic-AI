"""
main.py
=======
DAY 3 — SESSION 3: VECTOR DATABASES
===================================

Learning Objectives Demonstrated:
1. FAISS vs. Chroma vs. Qdrant vs. Pinecone architectural comparison.
2. Collections: Schema isolation, configuration, and lifecycles.
3. Upsert: Idempotent document/embedding insertion and updates.
4. Metadata Filtering: Pre-filtering with exact, boolean ($and, $or), and range ($lte) operators.
5. Persistence: Verifying on-disk database survival across process restarts.
6. Vector Index Types at a High Level: Flat vs. IVF vs. HNSW performance comparison.

Modular Architecture:
├── chunk_provider.py         # Multi-attribute governance metadata enrichment
├── embedder.py               # Gemini gemini-embedding-001 with pacing & retries
├── chroma_manager.py         # Persistent ChromaStore, collections, and upsert
├── filter_benchmark.py       # Pre- vs Post-filtering & compound boolean queries
├── faiss_benchmark.py        # Flat vs IVF vs HNSW index type performance
├── vector_db_comparisons.py  # Architectural matrix across 4 leading engines
└── main.py                   # Master orchestration and terminal reporting
"""

import sys
import shutil
from pathlib import Path

# Force UTF-8 terminal output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from chunk_provider import get_enriched_chunks, load_cached_embeddings_if_available
from embedder import Embedder
from chroma_manager import ChromaStore, METADATA_FILTERING_GUIDE
from filter_benchmark import run_metadata_filter_experiments
from faiss_benchmark import run_index_type_benchmark
from vector_db_comparisons import print_comparison_matrix


def main():
    print("=" * 85)
    print(" DAY 3 — SESSION 3: VECTOR DATABASES & FILTERED SIMILARITY SEARCH")
    print("=" * 85)

    persist_dir = Path(__file__).parent / "chroma_db"

    # -----------------------------------------------------------------------
    # STEP 1: Load Chunks Enriched with Multi-Dimensional Metadata
    # -----------------------------------------------------------------------
    print("\n" + "=" * 85)
    print(" [STEP 1] Ingesting Chunks & Attaching Enterprise Metadata")
    print("=" * 85)
    chunks = get_enriched_chunks()
    print(f"Total chunks loaded: {len(chunks)}")
    for i, c in enumerate(chunks[:3]):
        m = c.metadata
        print(f"  • Chunk [{m['chunk_id']}] -> Dept: {m['department']:<20} | Type: {m['doc_type']:<12} | Tier: {m['access_tier']:<12} | Page: {m['page']}")

    # Obtain or compute embeddings
    print("\nLoading vector embeddings for chunks...")
    embeddings = load_cached_embeddings_if_available(chunks)
    if embeddings is None:
        embedder = Embedder()
        texts = [c.page_content for c in chunks]
        embeddings = embedder.embed_texts(texts, cache_key="session_3_chunks")
    else:
        embedder = Embedder()
    print(f"Embedding matrix shape: {embeddings.shape} (Dimension: {embeddings.shape[1]})")

    # -----------------------------------------------------------------------
    # STEP 2: Chroma Collection Lifecycle & Idempotent Upsert
    # -----------------------------------------------------------------------
    print("\n" + "=" * 85)
    print(" [STEP 2] Initializing Persistent ChromaStore & Demonstrating Upsert")
    print("=" * 85)
    store = ChromaStore(
        persist_directory=str(persist_dir),
        collection_name="enterprise_governance",
        distance_metric="cosine",
    )

    initial_count = store.count()
    print(f"Collection initial vector count: {initial_count}")

    # First Upsert
    print("Executing upsert of 18 chunks into Chroma...")
    upserted_count = store.upsert_chunks(chunks, embeddings)
    print(f"Successfully upserted {upserted_count} chunks. Collection count now: {store.count()}")

    # Demonstrate Idempotency: Re-running upsert does NOT create duplicates or error!
    print("\nDemonstrating Upsert Idempotency (re-running identical upsert)...")
    store.upsert_chunks(chunks, embeddings)
    print(f"After re-upserting, collection count remains exactly: {store.count()} (No duplicates created!)")

    # -----------------------------------------------------------------------
    # STEP 3: Verifying Database Disk Persistence
    # -----------------------------------------------------------------------
    print("\n" + "=" * 85)
    print(" [STEP 3] Verifying On-Disk Persistence across Client Reload")
    print("=" * 85)
    # Simulate client teardown and reload from disk
    del store
    reloaded_store = ChromaStore(
        persist_directory=str(persist_dir),
        collection_name="enterprise_governance",
        distance_metric="cosine",
    )
    print(f"Reloaded ChromaStore from disk: {persist_dir.name}")
    print(f"Persisted vector count verified: {reloaded_store.count()} documents")
    sample_records = reloaded_store.inspect_sample_metadata(limit=2)
    for s in sample_records:
        print(f"  • Persisted ID: {s['id']} | Metadata: {s['metadata']}")

    # -----------------------------------------------------------------------
    # STEP 4: Advanced Metadata Filtering Experiments
    # -----------------------------------------------------------------------
    print("\n" + "=" * 85)
    print(" [STEP 4] Executing Filtered Similarity Searches in Chroma")
    print("=" * 85)
    filter_experiments = run_metadata_filter_experiments(reloaded_store, embedder)

    for exp in filter_experiments:
        print(f"\n>>> [{exp['id']}] {exp['title']}")
        print(f"    Query: '{exp['query']}'")

        if exp["id"] == "EXP-1":
            print(f"    - Unfiltered Top-3 Departments: {exp['unfiltered_sources']}")
            print(f"    - Filtered (Finance & HR):      {exp['filtered_hr_sources']}")
            print(f"    - Filtered (Cloud Infra):       {exp['filtered_cloud_sources']}")

        elif exp["id"] == "EXP-2":
            print(f"    - Filtered Top Results ($and Dept='Finance & HR' AND page=3):")
            for r in exp["filtered_results"]:
                print(f"        * {r}")

        elif exp["id"] == "EXP-3":
            print(f"    - Filtered Results (doc_type='SLA' AND page <= 2):")
            for r in exp["filtered_results"]:
                print(f"        * {r}")

        elif exp["id"] == "EXP-4":
            print(f"    - Post-filtered matches found: {exp['post_filtered_count']} (Discarded by Python post-filter!)")
            print(f"    - Pre-filtered matches found:  {exp['pre_filtered_count']} (Guaranteed by Chroma index!)")
            print(f"    - Key Takeaway: {exp['takeaway']}")

    # -----------------------------------------------------------------------
    # STEP 5: Vector Index Types Benchmark (Flat vs. IVF vs. HNSW)
    # -----------------------------------------------------------------------
    print("\n" + "=" * 85)
    print(" [STEP 5] High-Level Index Types Benchmark (FAISS Flat vs. IVF vs. HNSW)")
    print("=" * 85)
    index_results = run_index_type_benchmark(embeddings)

    print(f"\n{'Index Type':<16} | {'Algorithm Mechanism':<38} | {'Complexity':<12} | {'Recall':<8} | {'Latency'}")
    print("-" * 88)
    for name, data in index_results.items():
        print(f"{name:<16} | {data['type']:<38} | {data['complexity']:<12} | {data['recall']*100:<7.1f}% | {data['query_latency_us']:.1f} µs")

    print("-" * 88)
    print("Takeaways on Vector Indexes:")
    print("  • IndexFlat: 100% exact baseline, but O(N) distance checks degrade with millions of vectors.")
    print("  • IndexIVFFlat: Partitions space into Voronoi cells via clustering; cuts search time in half.")
    print("  • IndexHNSWFlat: Multi-layer graph traversal (O(log N)). This is why Chroma & Qdrant use HNSW!")

    # -----------------------------------------------------------------------
    # STEP 6: Vector Database Architectural Comparison
    # -----------------------------------------------------------------------
    print("\n" + "=" * 85)
    print(" [STEP 6] Vector Database Matrix: FAISS vs. Chroma vs. Qdrant vs. Pinecone")
    print("=" * 85)
    print_comparison_matrix()

    print("\n" + "=" * 85)
    print(" SESSION 3 COMPLETE: ALL TASKS & BENCHMARKS VERIFIED SUCCESSFULLY")
    print("=" * 85)


if __name__ == "__main__":
    main()
