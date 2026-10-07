"""
vector_store.py
===============
Vector Storage and Bi-Encoder Retrieval Module (Day 3 - Session 4)

Manages Chroma persistent collection for the 3 domain PDFs:
1. Ingests ~300-token chunks with metadata (source, page, doc_type, department).
2. Performs fast Bi-Encoder vector retrieval using gemini-embedding-001.
3. Returns Top-K candidate passages for downstream Cross-Encoder reranking.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import chromadb
from openai import OpenAI
from dotenv import load_dotenv

from pdf_loader import load_all_pdfs
from chunker import chunk_documents, ChunkedDocument

import os
load_dotenv()

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
API_KEY = os.getenv("GEMINI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
EMBEDDING_MODEL = "gemini-embedding-001"

CACHE_DIR = Path(__file__).parent / ".cache"
CACHE_DIR.mkdir(exist_ok=True)


class VectorStore:
    """
    Manages persistent vector collection in Chroma and Bi-Encoder candidate retrieval.
    """
    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        collection_name: str = "rag_enterprise_docs",
    ):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(self.persist_directory))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self.openai_client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

    def count(self) -> int:
        return self.collection.count()

    def embed_texts(self, texts: List[str], batch_size: int = 6) -> np.ndarray:
        """Embeds text snippets with Gemini embedding API."""
        all_vecs = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            resp = self.openai_client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=batch,
                timeout=30.0,
            )
            for item in resp.data:
                v = np.array(item.embedding, dtype=np.float32)
                norm = np.linalg.norm(v)
                if norm > 0:
                    v = v / norm
                all_vecs.append(v)
        return np.array(all_vecs, dtype=np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        """Embeds a single query vector."""
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

    def ingest_documents(self, docs_directory: Path) -> int:
        """
        Loads PDFs from docs directory, chunks them, computes/loads embeddings,
        and upserts them into Chroma.
        """
        raw_docs = load_all_pdfs(docs_directory)
        chunks = chunk_documents(raw_docs, chunk_size_tokens=300, chunk_overlap_tokens=50)

        # Check for cached embeddings from session_2 or session_3
        cache_locations = [
            CACHE_DIR / "chunks_300_embeddings.npy",
            Path(__file__).resolve().parent.parent / "session_2" / ".cache" / "chunks_300_embeddings.npy",
            Path(__file__).resolve().parent.parent / "session_3" / ".cache" / "chunks_300_embeddings.npy",
        ]
        embeddings = None
        for loc in cache_locations:
            if loc.exists():
                loaded = np.load(str(loc))
                if loaded.shape[0] == len(chunks):
                    print(f"  [Cache Hit] Loaded {len(chunks)} precomputed embeddings from {loc.parent.parent.name}.")
                    embeddings = loaded
                    break

        if embeddings is None:
            print(f"  [Embedding] Computing embeddings for {len(chunks)} chunks via {EMBEDDING_MODEL}...")
            texts = [c.page_content for c in chunks]
            embeddings = self.embed_texts(texts)
            np.save(str(CACHE_DIR / "chunks_300_embeddings.npy"), embeddings)

        ids = [c.metadata.get("chunk_id", f"chunk_{i}") for i, c in enumerate(chunks)]
        docs = [c.page_content for c in chunks]
        metas = [c.metadata for c in chunks]

        self.collection.upsert(
            ids=ids,
            documents=docs,
            metadatas=metas,
            embeddings=embeddings.tolist(),
        )

        return len(ids)

    def retrieve_candidates(self, query: str, top_k: int = 6) -> List[Dict[str, Any]]:
        """
        Stage 1 (Bi-Encoder Retrieval):
        Returns top_k nearest neighbors based on vector cosine similarity.
        """
        q_vec = self.embed_query(query)
        results = self.collection.query(
            query_embeddings=[q_vec.tolist()],
            n_results=min(top_k, max(1, self.collection.count())),
            include=["documents", "metadatas", "distances"],
        )

        candidates: List[Dict[str, Any]] = []
        if results and results["ids"] and len(results["ids"][0]) > 0:
            ids = results["ids"][0]
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            dists = results["distances"][0]

            for rank in range(len(ids)):
                distance = dists[rank]
                similarity = 1.0 - distance
                candidates.append({
                    "bi_encoder_rank": rank + 1,
                    "id": ids[rank],
                    "content": docs[rank],
                    "source": metas[rank].get("source", "unknown"),
                    "page": metas[rank].get("page", 1),
                    "token_count": metas[rank].get("token_count", 0),
                    "similarity": round(float(similarity), 4),
                    "distance": round(float(distance), 4),
                    "metadata": metas[rank],
                })

        return candidates


if __name__ == "__main__":
    store = VectorStore()
    docs_dir = Path(__file__).parent / "docs"
    count = store.ingest_documents(docs_dir)
    print(f"Store initialized with {count} documents.")
    top = store.retrieve_candidates("What are the hotel lodging rate limits in NYC?", top_k=3)
    for c in top:
        print(f"Rank {c['bi_encoder_rank']} | {c['source']}:P{c['page']} | Sim: {c['similarity']}")
