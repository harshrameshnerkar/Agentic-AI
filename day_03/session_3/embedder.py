"""
embedder.py
===========
Embedding Generation Module (Day 3 - Session 3)

Interfaces with Google Gemini's gemini-embedding-001 model via OpenAI-compatible endpoint.
- L2 vector normalization for cosine similarity
- Resilient retry handling for network timeouts
- Disk-based caching
"""

import os
import time
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
    def __init__(self, model: str = MODEL_NAME, batch_size: int = 6, pacing_seconds: float = 2.0):
        self.model = model
        self.batch_size = batch_size
        self.pacing_seconds = pacing_seconds
        self.client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

    def embed_texts(self, texts: List[str], cache_key: str = None) -> np.ndarray:
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

            for attempt in range(3):
                try:
                    response = self.client.embeddings.create(
                        model=self.model,
                        input=batch,
                        timeout=30.0,
                    )
                    for item in response.data:
                        vec = np.array(item.embedding, dtype=np.float32)
                        norm = np.linalg.norm(vec)
                        if norm > 0:
                            vec = vec / norm
                        all_vectors.append(vec)
                    break
                except Exception as e:
                    if attempt < 2:
                        wait = 2.0 * (attempt + 1)
                        print(f"    [Retry Warning] ({e}). Retrying in {wait}s...")
                        time.sleep(wait)
                    else:
                        raise e

            if i + self.batch_size < total_texts:
                time.sleep(self.pacing_seconds)

        matrix = np.array(all_vectors, dtype=np.float32)
        if cache_key:
            np.save(str(CACHE_DIR / f"{cache_key}.npy"), matrix)

        return matrix

    def embed_query(self, query: str, max_retries: int = 3) -> np.ndarray:
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
                    wait = 2.0 * (attempt + 1)
                    print(f"    [Retry Warning] embed_query failed ({e}). Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    raise e
