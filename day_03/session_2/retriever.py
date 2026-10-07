"""
retriever.py
============
Vector Retrieval Engine (Day 3 - Session 2)

Performs Top-K Cosine Similarity Search over chunk embeddings using NumPy.
Attaches ranking, similarity scores, and document metadata to each retrieved candidate.
"""

from typing import List, Dict, Any
import numpy as np
from chunker import ChunkedDocument


class RetrievalResult:
    """
    Encapsulates a single retrieved chunk with its match score and ranking.
    """
    def __init__(self, rank: int, score: float, chunk: ChunkedDocument):
        self.rank = rank
        self.score = score
        self.chunk = chunk

    @property
    def source(self) -> str:
        return self.chunk.metadata.get("source", "unknown")

    @property
    def page(self) -> int:
        return self.chunk.metadata.get("page", 0)

    @property
    def chunk_id(self) -> str:
        return self.chunk.metadata.get("chunk_id", "")

    @property
    def token_count(self) -> int:
        return self.chunk.token_count

    @property
    def content(self) -> str:
        return self.chunk.page_content

    def __repr__(self) -> str:
        return f"<Result #{self.rank} score={self.score:.4f} [{self.chunk_id}] {self.source}:P{self.page}>"


class VectorRetriever:
    """
    In-memory vector store supporting cosine similarity search over chunk collections.
    """
    def __init__(self, name: str, chunks: List[ChunkedDocument], embeddings: np.ndarray):
        assert len(chunks) == embeddings.shape[0], "Chunks and embeddings count mismatch!"
        self.name = name
        self.chunks = chunks
        self.embeddings = embeddings  # Assumed L2 normalized

    def search(self, query_vector: np.ndarray, top_k: int = 3) -> List[RetrievalResult]:
        """
        Executes Top-K search against indexed chunk vectors.

        Args:
            query_vector: 1D normalized query vector.
            top_k: Number of chunks to retrieve.

        Returns:
            List of RetrievalResult objects sorted descending by similarity.
        """
        # Cosine similarity via dot product of normalized vectors
        scores = np.dot(self.embeddings, query_vector)
        top_indices = np.argsort(scores)[::-1][:top_k]

        results: List[RetrievalResult] = []
        for rank, idx in enumerate(top_indices, start=1):
            results.append(
                RetrievalResult(
                    rank=rank,
                    score=float(scores[idx]),
                    chunk=self.chunks[idx],
                )
            )

        return results
