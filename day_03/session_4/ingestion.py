"""
ingestion.py
============
STAGE 1 OF RAG: INGESTION PIPELINE (Day 3 - Session 4)

Responsibilities:
1. Document Loading: Ingests PDFs page-by-page preserving metadata (source, page, char_count).
2. Text Chunking: Recursively splits documents into token-bounded chunks (300 tokens, 50 overlap).
3. Vector Embedding: Computes embeddings via gemini-embedding-001 with disk caching.
4. Storage: Persists chunks, vectors, and metadata into Chroma vector store.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import chromadb
from openai import OpenAI
from dotenv import load_dotenv

from pdf_loader import load_all_pdfs, Document
from chunker import chunk_documents, ChunkedDocument

import os
load_dotenv()

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
API_KEY = os.getenv("GEMINI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
EMBEDDING_MODEL = "gemini-embedding-001"

CACHE_DIR = Path(__file__).parent / ".cache"
CACHE_DIR.mkdir(exist_ok=True)


class IngestionPipeline:
    """
    Executes the complete document ingestion lifecycle:
    PDF Loading -> Chunking -> Vector Embedding -> Chroma Persistence.
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

    def embed_texts(self, texts: List[str], batch_size: int = 6) -> np.ndarray:
        """Embeds text chunks in paced batches."""
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

    def run(self, docs_directory: Path) -> int:
        """
        Runs the full ingestion pipeline:
        1. Loads PDFs
        2. Chunks text
        3. Obtains embeddings (cached or fresh)
        4. Upserts to Chroma collection
        """
        print("\n--- [INGESTION PIPELINE] Starting Document Ingestion ---")
        raw_docs = load_all_pdfs(docs_directory)
        print(f"  • Ingested {len(raw_docs)} pages from {docs_directory.name}")

        chunks = chunk_documents(raw_docs, chunk_size_tokens=300, chunk_overlap_tokens=50)
        print(f"  • Chunking produced {len(chunks)} token-bounded chunks")

        # Check for precomputed cache
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
                    print(f"  • [Cache Hit] Loaded {len(chunks)} precomputed embeddings from {loc.parent.parent.name}")
                    embeddings = loaded
                    break

        if embeddings is None:
            print(f"  • Computing fresh embeddings via {EMBEDDING_MODEL}...")
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
        print(f"  • Successfully upserted {len(ids)} chunks into Chroma collection '{self.collection.name}'")
        return len(ids)


if __name__ == "__main__":
    pipeline = IngestionPipeline()
    docs_dir = Path(__file__).parent / "docs"
    count = pipeline.run(docs_dir)
    print(f"Ingestion complete. Total vectors in collection: {count}")
