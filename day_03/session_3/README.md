# Day 3 — Session 3: Vector Databases

A modular, production-grade guide and reference implementation covering **Chroma**, **FAISS**, vector collections, idempotent upserts, metadata pre-filtering, disk persistence, and a high-level comparison of index algorithms (**Flat vs. IVF vs. HNSW**).

---

## 🎯 Learning Objectives

1. **Vector Database Landscape**:
   - FAISS vs. Chroma vs. Qdrant vs. Pinecone.
   - When to use an in-process library vs. an embedded store vs. a managed distributed database.
2. **Collections & Namespaces**:
   - Purpose of collections (schema isolation, per-tenant/per-domain segmentation).
   - Distance metric configuration (`cosine`, `l2`, `ip`).
3. **Idempotent Upsert**:
   - `add()` vs. `upsert()`: Preventing duplicate key collisions and allowing clean re-runs.
4. **Metadata Filtering**:
   - Exact matching, inequality (`$ne`), numerical range comparisons (`$gte`, `$lte`), and compound logic (`$and`, `$or`, `$in`).
   - Why **pre-filtering** inside the vector engine avoids the critical failure modes of **naive post-filtering**.
5. **Persistence**:
   - How Chroma persists state to disk (SQLite for metadata/records + Parquet/HNSW files for vectors).
6. **Vector Index Algorithms**:
   - **IndexFlat**: Exact brute-force ($O(N)$), 100% recall baseline.
   - **IndexIVF**: Inverted File Index (Voronoi clustering and centroid routing).
   - **IndexHNSW**: Hierarchical Navigable Small World graphs ($O(\log N)$ sub-linear graph traversal).

---

## 🏗️ Modular Architecture

```
day_03/session_3/
├── .env                       # API credentials & model configurations
├── requirements.txt           # chromadb, faiss-cpu, openai, numpy, python-dotenv
├── chroma_db/                 # Auto-generated persistent Chroma on-disk database
│   ├── chroma.sqlite3         # SQLite relational catalog for metadata & documents
│   └── [uuid]/                # HNSW graph indexes and vectors
├── chunk_provider.py          # Enriches Session 2 chunks with multi-tier governance metadata
├── embedder.py                # Gemini gemini-embedding-001 with retry logic & caching
├── chroma_manager.py          # Persistent ChromaStore, collections, and upsert engine
├── filter_benchmark.py        # Filtered similarity search & pre- vs. post-filtering benchmarks
├── faiss_benchmark.py         # Empirical comparison of Flat, IVF, and HNSW indexes
├── vector_db_comparisons.py   # Detailed comparison matrix across the 4 major engines
├── main.py                    # Master orchestration and terminal reporting
└── README.md                  # Comprehensive technical documentation
```

---

## 📊 Vector Database Architectural Matrix

| Dimension | **FAISS** (Meta) | **Chroma** (ChromaDB) | **Qdrant** (Rust Engine) | **Pinecone** (SaaS) |
| :--- | :--- | :--- | :--- | :--- |
| **Primary Nature** | C++ Algorithm Library | Embedded / Local Vector Store | Standalone Rust Service | Fully Managed SaaS |
| **Hosting Model** | In-Process (Python / C++) | Embedded in-process or Docker | Self-hosted Docker/K8s or Cloud | Serverless Cloud Only (AWS/GCP) |
| **Metadata Engine** | Minimal / None natively | First-class SQLite JSON | Rich dynamic payload schema | First-class key-value metadata |
| **Filtering Mechanism** | Manual Post-Filtering or IDScan | Pre-filtering via `where` | Payload-Aware HNSW Graph | Managed Pre-Filtering |
| **Persistence** | Manual (`faiss.write_index`) | Automatic SQLite + Parquet | Memory-mapped files (mmap) + WAL | Managed Cloud Storage |
| **Clustering & Sharding**| None (Single machine) | Prototyping / Single-node | Distributed Multi-Node (Raft) | Infinite Auto-Sharding |
| **Primary Index** | Flat, IVF, HNSW, PQ | HNSW (`hnswlib`) | Payload-Filterable HNSW | Proprietary Multi-Tenant ANN |
| **Best For** | Raw math, edge inference, research | Local development, desktop RAG | High-throughput enterprise RAG | Zero-DevOps turn-key enterprise |

---

## ⚡ Index Types at a High Level

```
1. IndexFlat (Brute Force):
   Query ──► [Vector 1] ──► [Vector 2] ──► ... ──► [Vector N]
   - Compares query against EVERY vector in the database.
   - Complexity: O(N) distance calculations.
   - 100% exact recall, but too slow for millions of vectors.

2. IndexIVF (Inverted File / Centroid Clustering):
   Query ──► Find nearest Centroids ──► Search only vectors in those Voronoi cells
   - Complexity: O(N / nlist * nprobe).
   - Fast, but requires k-means training; vectors near cell boundaries can be missed.

3. IndexHNSW (Hierarchical Navigable Small World Graph):
   Layer 2:  (Entry) ──────────────► (Skip Node)
                │                         │
   Layer 1:  (Node) ──────► (Node) ──────► (Node) ──────► (Node)
                │              │              │              │
   Layer 0:  [ Dense Graph Connecting All Nearest Neighbors ]
   - Multi-layer graph analogous to a skip-list.
   - Complexity: Sub-linear O(log N).
   - State-of-the-art speed/recall trade-off; default algorithm in Chroma & Qdrant.
```

---

## 🔍 Chroma Metadata Filter Cheatsheet

```python
# 1. Exact Match
where={"department": "Finance & HR"}

# 2. Not Equal
where={"doc_type": {"$ne": "SLA"}}

# 3. Numerical Comparison ($gt, $gte, $lt, $lte)
where={"page": {"$lte": 2}}

# 4. Inclusion List ($in, $nin)
where={"department": {"$in": ["Finance & HR", "Cloud Infrastructure"]}}

# 5. Compound AND ($and)
where={
    "$and": [
        {"department": "Cloud Infrastructure"},
        {"page": {"$lte": 2}}
    ]
}

# 6. Compound OR ($or)
where={
    "$or": [
        {"department": "Finance & HR"},
        {"access_tier": "Public"}
    ]
}
```

---

## ⚠️ Pre-Filtering vs. Naive Post-Filtering

* **The Problem with Post-Filtering**:
  If you ask a question like *"SLA downtime calculations"* but add a Python filter `access_tier == "Confidential"`, standard Top-3 search will return 3 Public Cloud SLA chunks. If you filter them in Python afterwards, **you get 0 results**, even though valid Confidential chunks exist further down!
* **The Chroma Solution (Pre-Filtering)**:
  By passing `where={"access_tier": "Confidential"}`, Chroma restricts candidate evaluation *during* the graph search, guaranteeing that all Top-3 results strictly conform to the security tier.

---

## 🚀 Execution

```bash
# Run the entire Day 3 Session 3 pipeline
python main.py

# Or test individual modules in isolation:
python chroma_manager.py      # Test collection creation & upsert
python filter_benchmark.py    # Test metadata filter experiments
python faiss_benchmark.py     # Test Flat vs IVF vs HNSW indexes
python vector_db_comparisons.py # Print vector database comparison matrix
```
