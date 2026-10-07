"""
embedder.py
===========
Embedding Generation Module (Day 3 - Session 2)

Utilizes Google Gemini's gemini-embedding-001 model via the OpenAI-compatible endpoint.
Features:
- Batch processing to minimize HTTP roundtrips
- Rate-limit pacing (sleep intervals between batches)
- Vector L2-normalization for fast cosine distance via dot product
- In-memory / disk caching to avoid redundant API consumption
"""

import os
import time
import json
from pathlib import Path
from typing import List
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")

CACHE_DIR = Path(__file__).parent / ".cache"
CACHE_DIR.mkdir(exist_ok=True)


class Embedder:
    """
    Handles batched embedding requests with rate-limiting and vector normalization.
    """
    def __init__(self, model: str = MODEL_NAME, batch_size: int = 6, pacing_seconds: float = 2.0):
        self.model = model
        self.batch_size = batch_size
        self.pacing_seconds = pacing_seconds
        self.client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

    def embed_texts(self, texts: List[str], cache_key: str = None) -> np.ndarray:
        """
        Embeds a list of text strings in paced batches.

        Args:
            texts: List of text snippets to embed.
            cache_key: Optional string identifier to cache/load from disk.

        Returns:
            np.ndarray of shape (len(texts), 3072), L2-normalized.
        """
        # Check disk cache if key provided
        if cache_key:
            cache_file = CACHE_DIR / f"{cache_key}.npy"
            if cache_file.exists():
                print(f"  [Cache Hit] Loaded embeddings from {cache_file.name}")
                return np.load(str(cache_file))

        all_vectors = []
        total_texts = len(texts)

        for i in range(0, total_texts, self.batch_size):
            batch = texts[i : i + self.batch_size]
            print(f"  [Embedding] Batch {i // self.batch_size + 1}/{(total_texts + self.batch_size - 1) // self.batch_size} ({len(batch)} items)...")

            # Call API
            response = self.client.embeddings.create(
                model=self.model,
                input=batch,
            )

            # Gemini endpoint returns embeddings in input order
            for item in response.data:
                vec = np.array(item.embedding, dtype=np.float32)
                # L2 normalize vector for direct dot-product cosine similarity
                norm = np.linalg.norm(vec)
                if norm > 0:
                    vec = vec / norm
                all_vectors.append(vec)

            # Pacing to avoid hitting 15 RPM
            if i + self.batch_size < total_texts:
                time.sleep(self.pacing_seconds)

        matrix = np.array(all_vectors, dtype=np.float32)

        # Save to disk cache if requested
        if cache_key:
            np.save(str(CACHE_DIR / f"{cache_key}.npy"), matrix)

        return matrix

    def embed_query(self, query: str, max_retries: int = 3) -> np.ndarray:
        """
        Embeds a single query string with retry handling and returns a normalized 1D vector.
        """
        for attempt in range(max_retries):
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=[query],
                    timeout=30.0,
                )
                vec = np.array(response.data[0].embedding, dtype=np.float32)
                norm = np.linalg.norm(vec)
                if norm > 0:
                    vec = vec / norm
                return vec
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2.0 * (attempt + 1)
                    print(f"    [Retry Warning] embed_query failed ({e}). Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise e


if __name__ == "__main__":
    embedder = Embedder()
    sample_texts = ["Cloud SLA downtime definition", "Employee travel expense rules"]
    vectors = embedder.embed_texts(sample_texts)
    print("Vectors shape:", vectors.shape)
    print("Vector 0 L2 Norm:", np.linalg.norm(vectors[0]))
