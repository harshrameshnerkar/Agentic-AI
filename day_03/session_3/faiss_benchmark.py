"""
faiss_benchmark.py
==================
Vector Index Types at a High Level (Day 3 - Session 3)

Learning Goals Covered:
1. IndexFlat (Exact brute force, O(N), 100% recall)
2. IndexIVFFlat (Inverted File / Centroid Clustering, faster, requires training)
3. IndexHNSWFlat (Hierarchical Navigable Small World graph, O(log N), default in Chroma/Qdrant)
4. Empirical comparison of index build time, search speed, and recall.
"""

import time
from typing import Dict, Any, List
import numpy as np
import faiss


def run_index_type_benchmark(vectors: np.ndarray, num_queries: int = 10, top_k: int = 5) -> Dict[str, Any]:
    """
    Constructs and compares Flat, IVF, and HNSW indexes over a normalized vector space.

    Args:
        vectors: Normalized dataset embeddings (N, dimension).
        num_queries: Number of query vectors to simulate.
        top_k: Top-K neighbors to retrieve.

    Returns:
        Dictionary containing comparative benchmarks.
    """
    num_vectors, dim = vectors.shape

    # For a robust index demonstration, if dataset is small, augment with synthetic vectors
    if num_vectors < 1000:
        rng = np.random.default_rng(42)
        noise = rng.normal(0, 0.05, (2000, dim)).astype(np.float32)
        expanded_vectors = np.vstack([vectors, noise])
        # Re-normalize
        norms = np.linalg.norm(expanded_vectors, axis=1, keepdims=True)
        expanded_vectors = expanded_vectors / np.maximum(norms, 1e-9)
    else:
        expanded_vectors = vectors

    total_n, d = expanded_vectors.shape
    queries = expanded_vectors[:num_queries]

    benchmark_records = {}

    # -----------------------------------------------------------------------
    # 1. EXACT BRUTE FORCE: IndexFlatIP (Cosine via Inner Product)
    # -----------------------------------------------------------------------
    t0 = time.perf_counter()
    index_flat = faiss.IndexFlatIP(d)
    index_flat.add(expanded_vectors)
    flat_build_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    flat_distances, flat_indices = index_flat.search(queries, top_k)
    flat_search_time = (time.perf_counter() - t0) / num_queries

    benchmark_records["IndexFlatIP"] = {
        "type": "Exact (Brute-Force)",
        "complexity": "O(N)",
        "recall": 1.0,  # Ground truth baseline
        "build_time_ms": round(flat_build_time * 1000, 2),
        "query_latency_us": round(flat_search_time * 1_000_000, 2),
        "pros": "100% exact accuracy, zero training required, supports dynamic deletes.",
        "cons": "Scales poorly to millions of vectors (O(N) distance checks per query).",
    }

    # -----------------------------------------------------------------------
    # 2. INVERTED FILE INDEX: IndexIVFFlat (Clustering / Voronoi Cells)
    # -----------------------------------------------------------------------
    nlist = 32  # Number of Voronoi centroids
    nprobe = 8  # Number of nearby centroids to inspect at search time
    quantizer = faiss.IndexFlatIP(d)
    index_ivf = faiss.IndexIVFFlat(quantizer, d, nlist, faiss.METRIC_INNER_PRODUCT)

    t0 = time.perf_counter()
    index_ivf.train(expanded_vectors)  # Requires k-means clustering training
    index_ivf.add(expanded_vectors)
    ivf_build_time = time.perf_counter() - t0

    index_ivf.nprobe = nprobe
    t0 = time.perf_counter()
    ivf_distances, ivf_indices = index_ivf.search(queries, top_k)
    ivf_search_time = (time.perf_counter() - t0) / num_queries

    # Calculate recall against exact flat results
    matches = 0
    total_slots = num_queries * top_k
    for q in range(num_queries):
        matches += len(set(ivf_indices[q]).intersection(set(flat_indices[q])))
    ivf_recall = matches / total_slots

    benchmark_records["IndexIVFFlat"] = {
        "type": "Approximate (Inverted List / Centroids)",
        "complexity": "O(N / nlist * nprobe)",
        "recall": round(ivf_recall, 4),
        "build_time_ms": round(ivf_build_time * 1000, 2),
        "query_latency_us": round(ivf_search_time * 1_000_000, 2),
        "pros": "Drastically reduces distance calculations, low memory footprint.",
        "cons": "Requires a training phase; vectors near cluster boundaries can be missed.",
    }

    # -----------------------------------------------------------------------
    # 3. HIERARCHICAL GRAPH: IndexHNSWFlat (Chroma / Qdrant default)
    # -----------------------------------------------------------------------
    M = 32  # Number of bi-directional links per vector node
    index_hnsw = faiss.IndexHNSWFlat(d, M, faiss.METRIC_INNER_PRODUCT)
    index_hnsw.hnsw.efSearch = 64  # Depth of beam search at query time

    t0 = time.perf_counter()
    index_hnsw.add(expanded_vectors)  # No training needed, builds multi-layer graph
    hnsw_build_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    hnsw_distances, hnsw_indices = index_hnsw.search(queries, top_k)
    hnsw_search_time = (time.perf_counter() - t0) / num_queries

    # Calculate recall against exact flat results
    matches = 0
    for q in range(num_queries):
        matches += len(set(hnsw_indices[q]).intersection(set(flat_indices[q])))
    hnsw_recall = matches / total_slots

    benchmark_records["IndexHNSWFlat"] = {
        "type": "Approximate (Hierarchical Navigable Graph)",
        "complexity": "O(log N)",
        "recall": round(hnsw_recall, 4),
        "build_time_ms": round(hnsw_build_time * 1000, 2),
        "query_latency_us": round(hnsw_search_time * 1_000_000, 2),
        "pros": "State-of-the-art speed/recall trade-off; sub-linear search time.",
        "cons": "Higher RAM overhead to maintain graph edge connections.",
    }

    return benchmark_records


if __name__ == "__main__":
    from chunk_provider import get_enriched_chunks, load_cached_embeddings_if_available
    chunks = get_enriched_chunks()
    vecs = load_cached_embeddings_if_available(chunks)
    if vecs is not None:
        print("Running Index Types Benchmark...")
        results = run_index_type_benchmark(vecs)
        for k, v in results.items():
            print(f"\n[{k}] ({v['type']})")
            print(f"  Recall vs Exact: {v['recall'] * 100:.1f}%")
            print(f"  Query Latency:   {v['query_latency_us']} µs")
            print(f"  Complexity:      {v['complexity']}")
