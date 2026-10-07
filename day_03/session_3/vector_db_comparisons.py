"""
vector_db_comparisons.py
========================
Vector Database Architecture & Technology Comparison (Day 3 - Session 3)

Provides an in-depth, production-oriented comparison of:
- FAISS (Meta)
- Chroma (ChromaDB Inc.)
- Qdrant (Qdrant GmbH)
- Pinecone (Pinecone Systems)
"""

from typing import List, Dict, Any


VECTOR_DB_COMPARISON_MATRIX: List[Dict[str, Any]] = [
    {
        "name": "FAISS",
        "developer": "Meta AI Research",
        "architecture": "C++ Library with Python bindings (In-Process / Library)",
        "deployment": "Embedded in application process; no server daemon required",
        "storage_engine": "RAM-primary; manual disk serialization via faiss.write_index()",
        "metadata_support": "Limited / None natively. Maps integer ID to vector. Requires external SQLite/Dict for payload.",
        "filtering_approach": "Post-filtering manually, or IDSelector (flat scans). No native JSON filtering engine.",
        "index_algorithms": "IndexFlat, IndexIVFFlat, IndexHNSW, Product Quantization (PQ), OPQ, ScaNN",
        "scalability": "Single node (GPU / Multi-core CPU). Scales to billions on a single high-memory box.",
        "best_for": "Ultra-low-latency raw vector math, offline similarity search, mobile/edge device inference, research.",
        "cost_model": "Open Source (Apache 2.0). Free; pay only for compute/RAM.",
    },
    {
        "name": "Chroma",
        "developer": "ChromaDB",
        "architecture": "Embedded or Client-Server Vector Store (Python / Rust core)",
        "deployment": "Embedded directly in Python (`chromadb.PersistentClient`) or Docker microservice",
        "storage_engine": "SQLite for metadata + Parquet & HNSW index files on disk",
        "metadata_support": "First-class native JSON metadata dictionaries ($eq, $ne, $and, $or, $in, $gte, etc.)",
        "filtering_approach": "Pre-filtering supported directly inside query() via where parameter",
        "index_algorithms": "HNSW (Hierarchical Navigable Small World) via hnswlib",
        "scalability": "Ideal for single-node / local prototyping, small to medium datasets (<5 million vectors)",
        "best_for": "Local development, agentic workflows, embedded desktop tools, educational prototypes.",
        "cost_model": "Open Source (Apache 2.0). Cloud managed offering available.",
    },
    {
        "name": "Qdrant",
        "developer": "Qdrant",
        "architecture": "Stand-alone Vector Search Engine written in Rust",
        "deployment": "Self-hosted Docker / Kubernetes cluster or Qdrant Cloud managed service",
        "storage_engine": "On-disk memory-mapped files (mmap) with WAL (Write-Ahead Logging) and RocksDB",
        "metadata_support": "Rich payload storage with dynamic JSON schemas and geo/text/numerical indexing",
        "filtering_approach": "Advanced Filterable HNSW (builds graph links taking payload constraints into account)",
        "index_algorithms": "Custom HNSW graph with payload-aware traversals and vector quantization (scalar/product)",
        "scalability": "High horizontal scalability; multi-node distributed sharding with consensus (Raft)",
        "best_for": "Production enterprise RAG requiring complex payload filters, hybrid search, self-hosting in VPC.",
        "cost_model": "Open Source (Apache 2.0) with managed SaaS cloud tier.",
    },
    {
        "name": "Pinecone",
        "developer": "Pinecone Systems",
        "architecture": "Fully Managed, Serverless / Pod-based Cloud-Native Vector Database",
        "deployment": "SaaS only (AWS, GCP, Azure); no local/embedded installation",
        "storage_engine": "Proprietary multi-tenant cloud storage decoupled into compute and blob tiers",
        "metadata_support": "Native key-value metadata attached to vector IDs with boolean/range queries",
        "filtering_approach": "Pre-filtering across metadata indexes during approximate nearest neighbor search",
        "index_algorithms": "Proprietary ANN graph algorithms optimized for serverless multi-tenancy",
        "scalability": "Virtually infinite serverless scale; automated partition management and replication",
        "best_for": "Zero-DevOps enterprise production, turn-key deployment, large multi-tenant SaaS apps.",
        "cost_model": "Commercial SaaS (pay-as-you-go per read/write unit and storage tier).",
    },
]


def print_comparison_matrix():
    """Prints a structured technical comparison between all 4 vector engines."""
    print("=" * 95)
    print(" VECTOR DATABASE COMPARISON: FAISS vs. CHROMA vs. QDRANT vs. PINECONE")
    print("=" * 95)

    headers = ["Feature", "FAISS", "Chroma", "Qdrant", "Pinecone"]
    print(f"\n{'Attribute':<20} | {'FAISS':<16} | {'Chroma':<18} | {'Qdrant':<18} | {'Pinecone'}")
    print("-" * 95)

    fields = [
        ("Architecture", "C++ Library", "Embedded Store", "Rust Microservice", "Cloud Serverless"),
        ("Deployment", "In-Process lib", "Local / Docker", "Docker / K8s", "Managed SaaS"),
        ("Metadata Filtering", "Minimal / External", "Native (SQLite)", "Rich Payload Graph", "Native Metadata"),
        ("Persistence", "Manual file save", "Automatic SQLite", "Mmap + WAL", "Cloud Managed"),
        ("Primary Algorithm", "Flat, IVF, HNSW", "HNSW", "Payload-Aware HNSW", "Proprietary ANN"),
        ("Horizontal Scale", "Single-Node", "Single-Node", "Distributed Cluster", "Serverless Scale"),
        ("DevOps Overhead", "Zero (Code only)", "Zero (Embedded)", "Low to Moderate", "Zero (Fully managed)"),
        ("License / Cost", "Open Source (Free)", "Open Source (Free)", "Open Source / Cloud", "Commercial SaaS"),
    ]

    for label, faiss_val, chroma_val, qdrant_val, pinecone_val in fields:
        print(f"{label:<20} | {faiss_val:<16} | {chroma_val:<18} | {qdrant_val:<18} | {pinecone_val}")

    print("-" * 95)


if __name__ == "__main__":
    print_comparison_matrix()
