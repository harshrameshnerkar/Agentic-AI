"""
retrieval.py
============
STAGE 2 OF RAG: CANDIDATE RETRIEVAL (Day 3 - Session 4)

Responsibilities:
1. Query Embedding: Embeds the user query using gemini-embedding-001.
2. Vector Similarity Search: Performs fast Bi-Encoder nearest neighbor retrieval in Chroma.
3. Candidate Assembly: Returns structured CandidatePassage objects with similarity telemetry.
"""

from typing import List, Dict, Any
import numpy as np
import chromadb
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
API_KEY = os.getenv("GEMINI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
EMBEDDING_MODEL = "gemini-embedding-001"


class CandidatePassage:
    """
    Structured representation of a candidate passage retrieved from the vector index.
    """
    def __init__(
        self,
        chunk_id: str,
        content: str,
        source: str,
        page: int,
        bi_encoder_rank: int,
        similarity: float,
        metadata: Dict[str, Any],
    ):
        self.chunk_id = chunk_id
        self.content = content
        self.source = source
        self.page = page
        self.bi_encoder_rank = bi_encoder_rank
        self.similarity = similarity
        self.metadata = metadata

    def __repr__(self) -> str:
        return f"<Candidate #{self.bi_encoder_rank} [{self.source}:P{self.page}] sim={self.similarity:.4f}>"


class Retriever:
    """
    Handles candidate retrieval over persistent Chroma collections.
    """
    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        collection_name: str = "rag_enterprise_docs",
    ):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self.openai_client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

    def embed_query(self, query: str) -> np.ndarray:
        resp = self.openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=[query],
            timeout=30.0,
        )
        v = np.array(resp.data[0].embedding, dtype=np.float32)
        norm = np.linalg.norm(v)
        if norm > 0:
            v = v / norm
        return v

    def retrieve(self, query: str, top_k: int = 6) -> List[CandidatePassage]:
        """
        Executes Bi-Encoder vector retrieval in Chroma.
        Returns Top-K CandidatePassage objects sorted descending by similarity.
        """
        q_vec = self.embed_query(query)
        total_docs = max(1, self.collection.count())
        results = self.collection.query(
            query_embeddings=[q_vec.tolist()],
            n_results=min(top_k, total_docs),
            include=["documents", "metadatas", "distances"],
        )

        candidates: List[CandidatePassage] = []
        if results and results["ids"] and len(results["ids"][0]) > 0:
            ids = results["ids"][0]
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            dists = results["distances"][0]

            for rank in range(len(ids)):
                sim = 1.0 - dists[rank]
                candidates.append(
                    CandidatePassage(
                        chunk_id=ids[rank],
                        content=docs[rank],
                        source=metas[rank].get("source", "unknown"),
                        page=metas[rank].get("page", 1),
                        bi_encoder_rank=rank + 1,
                        similarity=round(float(sim), 4),
                        metadata=metas[rank],
                    )
                )

        return candidates


if __name__ == "__main__":
    retriever = Retriever()
    sample_query = "What is the maximum nightly hotel rate in NYC?"
    top_candidates = retriever.retrieve(sample_query, top_k=3)
    print(f"Retrieved {len(top_candidates)} candidates for query: '{sample_query}'")
    for c in top_candidates:
        print(f"  {c}")
