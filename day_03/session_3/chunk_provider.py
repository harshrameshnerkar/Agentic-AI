"""
chunk_provider.py
=================
Provides structured document chunks enriched with multi-attribute enterprise metadata.

Metadata Dimensions Provided:
- source (str): PDF document filename
- page (int): 1-indexed page number
- department (str): "Cloud Infrastructure", "Finance & HR", "Data Engineering"
- doc_type (str): "SLA", "Policy", "Architecture"
- access_tier (str): "Public", "Internal", "Confidential"
- year (int): 2026
- token_count (int): exact token length
"""

import sys
from pathlib import Path
from typing import List, Dict, Any
import numpy as np

from pdf_loader import load_all_pdfs
from chunker import chunk_documents, ChunkedDocument


# Department and governance mapping per source document
METADATA_ENRICHMENT_MAP = {
    "cloud_platform_sla.pdf": {
        "department": "Cloud Infrastructure",
        "doc_type": "SLA",
        "access_tier": "Public",
        "year": 2026,
    },
    "employee_travel_policy.pdf": {
        "department": "Finance & HR",
        "doc_type": "Policy",
        "access_tier": "Internal",
        "year": 2026,
    },
    "database_migration_guide.pdf": {
        "department": "Data Engineering",
        "doc_type": "Architecture",
        "access_tier": "Confidential",
        "year": 2026,
    },
}


def get_enriched_chunks() -> List[ChunkedDocument]:
    """
    Ingests PDFs from local docs directory, splits into ~300-token chunks,
    and enriches with structured enterprise governance metadata.
    """
    docs_dir = Path(__file__).parent / "docs"
    if not docs_dir.exists() or len(list(docs_dir.glob("*.pdf"))) < 3:
        # Fallback to session_2 docs if available
        alt_docs = Path(__file__).resolve().parent.parent / "session_2" / "docs"
        if alt_docs.exists() and len(list(alt_docs.glob("*.pdf"))) >= 3:
            docs_dir = alt_docs
        else:
            from generate_sample_docs import generate_all_sample_pdfs
            generate_all_sample_pdfs()

    raw_docs = load_all_pdfs(docs_dir)
    chunks = chunk_documents(raw_docs, chunk_size_tokens=300, chunk_overlap_tokens=50)

    # Enrich metadata
    enriched_chunks: List[ChunkedDocument] = []
    for c in chunks:
        src = c.metadata.get("source", "")
        enrichment = METADATA_ENRICHMENT_MAP.get(
            src,
            {
                "department": "General",
                "doc_type": "Documentation",
                "access_tier": "Internal",
                "year": 2026,
            },
        )
        updated_meta = {
            **c.metadata,
            **enrichment,
        }
        enriched_chunks.append(
            ChunkedDocument(page_content=c.page_content, metadata=updated_meta)
        )

    return enriched_chunks


def load_cached_embeddings_if_available(chunks: List[ChunkedDocument]) -> np.ndarray:
    """
    Attempts to load pre-computed 300-token embeddings from cache
    to avoid re-calling Gemini embedding API.
    """
    cache_dirs = [
        Path(__file__).parent / ".cache",
        Path(__file__).resolve().parent.parent / "session_2" / ".cache",
    ]
    for c_dir in cache_dirs:
        cache_file = c_dir / "chunks_300_embeddings.npy"
        if cache_file.exists():
            vecs = np.load(str(cache_file))
            if vecs.shape[0] == len(chunks):
                print(f"  [Cache Hit] Loaded {len(chunks)} precomputed embeddings from {c_dir.parent.name}.")
                return vecs

    return None


if __name__ == "__main__":
    chunks = get_enriched_chunks()
    print(f"Total enriched chunks: {len(chunks)}")
    for c in chunks[:3]:
        print(f"ID: {c.metadata['chunk_id']} | Dept: {c.metadata['department']} | Page: {c.metadata['page']} | Type: {c.metadata['doc_type']}")
