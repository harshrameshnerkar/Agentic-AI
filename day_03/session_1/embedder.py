"""
EMBEDDER MODULE: Handles API client setup and batch embedding generation.
"""

import os
import time
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")

if not API_KEY:
    raise ValueError("Missing OPENAI_API_KEY in .env file.")

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)


def get_single_embedding(text: str) -> np.ndarray:
    """
    Embeds a single query string.
    Returns:
        np.ndarray: 1D float32 vector of length d (3072 for gemini-embedding-001).
    """
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[text]
    )
    return np.array(response.data[0].embedding, dtype=np.float32)


def get_embeddings_batch(texts: list[str], batch_size: int = 25) -> np.ndarray:
    """
    Embeds a list of texts in batches to maximize throughput and minimize network roundtrips.
    Returns:
        np.ndarray: 2D matrix of shape (N, d).
    """
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        chunk = texts[i : i + batch_size]
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=chunk
        )
        chunk_embeddings = [item.embedding for item in response.data]
        all_embeddings.extend(chunk_embeddings)

        # Gentle pacing between batches
        if i + batch_size < len(texts):
            time.sleep(2.0)

    return np.array(all_embeddings, dtype=np.float32)
