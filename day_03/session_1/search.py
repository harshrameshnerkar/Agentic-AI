"""
SEARCH MODULE: Top-K Vector Search Engine built on NumPy.
"""

import numpy as np
from embedder import get_single_embedding
from metrics import cosine_similarity, euclidean_distance


def search_top_k(
    query: str,
    corpus_texts: list[str],
    corpus_matrix: np.ndarray,
    k: int = 5
) -> list[dict]:
    """
    Executes a top-k nearest neighbor search using Cosine Similarity in pure NumPy.

    Args:
        query: User input query string.
        corpus_texts: List of document strings corresponding to corpus_matrix.
        corpus_matrix: 2D NumPy array of shape (N, d) containing precomputed embeddings.
        k: Number of top results to retrieve.

    Returns:
        list[dict]: Top-k matches sorted by descending cosine similarity.
    """
    # 1. Embed query
    query_vec = get_single_embedding(query)

    # 2. Compute similarity metrics across all corpus vectors
    cos_sims = cosine_similarity(query_vec, corpus_matrix)
    euc_dists = euclidean_distance(query_vec, corpus_matrix)

    # 3. Rank indices by highest cosine score (descending order)
    top_indices = np.argsort(cos_sims)[::-1][:k]

    results = []
    for idx in top_indices:
        results.append({
            "index": int(idx) + 1,
            "text": corpus_texts[idx],
            "cosine_sim": float(cos_sims[idx]),
            "euclidean_dist": float(euc_dists[idx])
        })

    return results
