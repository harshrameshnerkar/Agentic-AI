"""
METRICS MODULE: Pure NumPy Vector Math for Similarity and Distance Calculations.
"""

import numpy as np


def cosine_similarity(query_vec: np.ndarray, corpus_matrix: np.ndarray) -> np.ndarray:
    """
    Computes Cosine Similarity between a 1D query vector and a 2D matrix of corpus vectors:
        Cosine_Sim(u, v) = (u . v) / (||u||_2 * ||v||_2)

    Properties:
    - Measures the angle between vectors, independent of magnitude (text length).
    - Range: [-1.0, 1.0] (typically [0.0, 1.0] for text embeddings).
    - Higher is better (1.0 = identical angle).
    """
    dot_products = np.dot(corpus_matrix, query_vec)
    corpus_norms = np.linalg.norm(corpus_matrix, axis=1)
    query_norm = np.linalg.norm(query_vec)

    # 1e-10 epsilon prevents division by zero
    return dot_products / (corpus_norms * query_norm + 1e-10)


def euclidean_distance(query_vec: np.ndarray, corpus_matrix: np.ndarray) -> np.ndarray:
    """
    Computes Euclidean Distance (L2 norm) between a 1D query vector and a 2D matrix of corpus vectors:
        Euclidean_Dist(u, v) = sqrt(sum((u_i - v_i)^2))

    Properties:
    - Measures the straight-line physical distance in Euclidean space.
    - Range: [0.0, infinity).
    - Lower is better (0.0 = identical position).
    - On normalized vectors (||u|| = 1), Euclidean distance squared = 2 - 2 * Cosine_Similarity.
    """
    diffs = corpus_matrix - query_vec
    return np.linalg.norm(diffs, axis=1)
