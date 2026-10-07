"""
chroma_manager.py
=================
Chroma Vector Database Management Module (Day 3 - Session 3)

Learning Goals Covered:
1. Persistent Collections vs Ephemeral in-memory instances
2. Idempotent Upsert (insert or update by ID)
3. Advanced Metadata Filtering ($eq, $ne, $gte, $lte, $and, $or, $in)
4. Vector Distance Metrics (Cosine Space via hnsw:space)
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import chromadb
from chromadb.config import Settings
from chunk_provider import ChunkedDocument


class ChromaStore:
    """
    Manages persistent Chroma vector storage, collection lifecycles,
    idempotent upserts, and filtered semantic retrieval.
    """
    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        collection_name: str = "enterprise_knowledge",
        distance_metric: str = "cosine",
    ):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(exist_ok=True)
        self.collection_name = collection_name
        self.distance_metric = distance_metric

        # Initialize Chroma PersistentClient
        # Persists metadata/documents in SQLite and vectors in HNSW index files
        self.client = chromadb.PersistentClient(path=str(self.persist_directory))

        # Get or create collection with designated distance space
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": self.distance_metric},
        )

    def count(self) -> int:
        """Returns total vector count in the collection."""
        return self.collection.count()

    def upsert_chunks(self, chunks: List[ChunkedDocument], embeddings: np.ndarray) -> int:
        """
        Idempotently inserts or updates chunks into the collection.
        If a chunk ID already exists, its document, embedding, and metadata
        are updated in-place without throwing duplicate key errors.

        Args:
            chunks: List of ChunkedDocument objects.
            embeddings: 2D numpy array of shape (N, dimension).

        Returns:
            Number of chunks upserted.
        """
        assert len(chunks) == embeddings.shape[0], "Chunks and embeddings count mismatch!"

        ids: List[str] = []
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []
        embeddings_list: List[List[float]] = []

        for idx, chunk in enumerate(chunks):
            chunk_id = chunk.metadata.get("chunk_id", f"chunk_{idx}")
            ids.append(chunk_id)
            documents.append(chunk.page_content)

            # Chroma metadata values must be str, int, float, or bool
            clean_meta = {}
            for k, v in chunk.metadata.items():
                if isinstance(v, (str, int, float, bool)):
                    clean_meta[k] = v
                else:
                    clean_meta[k] = str(v)
            metadatas.append(clean_meta)

            embeddings_list.append(embeddings[idx].tolist())

        # Execute batched upsert
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings_list,
        )

        return len(ids)

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 3,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Executes similarity search with optional metadata pre-filtering.

        Args:
            query_vector: 1D normalized query vector.
            top_k: Number of nearest neighbors to retrieve.
            where: Chroma metadata filter dictionary ($and, $or, $gte, etc.)

        Returns:
            List of result dictionaries containing id, distance, similarity, document, and metadata.
        """
        query_embedding = [query_vector.tolist()]

        query_kwargs = {
            "query_embeddings": query_embedding,
            "n_results": min(top_k, max(1, self.collection.count())),
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            query_kwargs["where"] = where

        raw_results = self.collection.query(**query_kwargs)

        results = []
        if raw_results and raw_results["ids"] and len(raw_results["ids"][0]) > 0:
            ids = raw_results["ids"][0]
            docs = raw_results["documents"][0]
            metas = raw_results["metadatas"][0]
            dists = raw_results["distances"][0]

            for rank in range(len(ids)):
                # In cosine space, Chroma distance = 1 - cosine_similarity
                # Therefore, similarity = 1 - distance
                distance = dists[rank]
                similarity = 1.0 - distance

                results.append({
                    "rank": rank + 1,
                    "id": ids[rank],
                    "similarity": round(similarity, 4),
                    "distance": round(distance, 4),
                    "document": docs[rank],
                    "metadata": metas[rank],
                })

        return results

    def inspect_sample_metadata(self, limit: int = 3) -> List[Dict[str, Any]]:
        """Returns sample stored metadata records for verification."""
        peek_data = self.collection.peek(limit=limit)
        samples = []
        if peek_data and peek_data["ids"]:
            for i in range(len(peek_data["ids"])):
                samples.append({
                    "id": peek_data["ids"][i],
                    "metadata": peek_data["metadatas"][i],
                })
        return samples


# ---------------------------------------------------------------------------
# EDUCATIONAL CHEATSHEET: CHROMA METADATA FILTER OPERATORS
# ---------------------------------------------------------------------------
METADATA_FILTERING_GUIDE = """
=============================================================================
CHROMA METADATA FILTERING OPERATORS
=============================================================================
1. Exact Match:
   where={"department": "Finance & HR"}

2. Not Equal ($ne):
   where={"department": {"$ne": "Finance & HR"}}

3. Comparison Operators ($gt, $gte, $lt, $lte):
   where={"page": {"$lte": 2}}
   where={"token_count": {"$gte": 250}}

4. Inclusion / Exclusion ($in, $nin):
   where={"department": {"$in": ["Finance & HR", "Cloud Infrastructure"]}}

5. Logical AND ($and):
   where={
       "$and": [
           {"department": "Cloud Infrastructure"},
           {"page": {"$lte": 2}}
       ]
   }

6. Logical OR ($or):
   where={
       "$or": [
           {"department": "Finance & HR"},
           {"access_tier": "Public"}
       ]
   }
=============================================================================
"""


if __name__ == "__main__":
    from chunk_provider import get_enriched_chunks, load_cached_embeddings_if_available
    from embedder import Embedder

    print("Initializing ChromaStore...")
    store = ChromaStore(persist_directory="./chroma_db", collection_name="test_collection")

    chunks = get_enriched_chunks()
    vecs = load_cached_embeddings_if_available(chunks)
    if vecs is None:
        embedder = Embedder()
        texts = [c.page_content for c in chunks]
        vecs = embedder.embed_texts(texts)

    count = store.upsert_chunks(chunks, vecs)
    print(f"Upserted {count} chunks. Collection total count: {store.count()}")

    print("\nRunning test query with exact department filter ('Finance & HR'):")
    q_vec = vecs[0]
    filtered_results = store.search(q_vec, top_k=2, where={"department": "Finance & HR"})
    for r in filtered_results:
        print(f"Rank {r['rank']} | ID: {r['id']} | Dept: {r['metadata']['department']} | Sim: {r['similarity']}")
