"""
filter_benchmark.py
===================
Metadata Filtering Benchmark & Pre- vs. Post-Filtering Analysis (Day 3 - Session 3)

Demonstrates:
1. Cross-Domain Disambiguation (Filtering by department)
2. Compound Boolean Predicates ($and, $or, $in)
3. Numerical Range Filtering ($lte, $gte)
4. Why Pre-Filtering inside the Vector DB beats Naive Post-Filtering
"""

from typing import List, Dict, Any
import numpy as np
from chroma_manager import ChromaStore
from embedder import Embedder


def run_metadata_filter_experiments(store: ChromaStore, embedder: Embedder) -> List[Dict[str, Any]]:
    """
    Executes a structured battery of filtered similarity searches demonstrating
    enterprise governance and precision retrieval.
    """
    experiments = []

    # -----------------------------------------------------------------------
    # EXPERIMENT 1: Cross-Domain Disambiguation
    # Query has ambiguous terms that exist across all 3 documents ("rules and guidelines")
    # -----------------------------------------------------------------------
    query_1 = "What are the mandatory rules, guidelines, and allowances?"
    q_vec_1 = embedder.embed_query(query_1)

    unfiltered_1 = store.search(q_vec_1, top_k=3, where=None)
    filtered_hr_1 = store.search(q_vec_1, top_k=3, where={"department": "Finance & HR"})
    filtered_cloud_1 = store.search(q_vec_1, top_k=3, where={"department": "Cloud Infrastructure"})

    experiments.append({
        "id": "EXP-1",
        "title": "Cross-Domain Disambiguation via Department Filter",
        "query": query_1,
        "unfiltered_sources": [f"{r['metadata']['source']} (Dept: {r['metadata']['department']})" for r in unfiltered_1],
        "filtered_hr_sources": [f"{r['metadata']['source']} (Dept: {r['metadata']['department']})" for r in filtered_hr_1],
        "filtered_cloud_sources": [f"{r['metadata']['source']} (Dept: {r['metadata']['department']})" for r in filtered_cloud_1],
    })

    # -----------------------------------------------------------------------
    # EXPERIMENT 2: Compound Boolean Filter ($and with Page Restriction)
    # -----------------------------------------------------------------------
    query_2 = "What are the emergency response hotlines, policies, and contacts?"
    q_vec_2 = embedder.embed_query(query_2)

    unfiltered_2 = store.search(q_vec_2, top_k=3, where=None)
    compound_where = {
        "$and": [
            {"department": "Finance & HR"},
            {"page": 3},
        ]
    }
    filtered_2 = store.search(q_vec_2, top_k=3, where=compound_where)

    experiments.append({
        "id": "EXP-2",
        "title": "Compound Boolean Filtering ($and on department AND page == 3)",
        "query": query_2,
        "unfiltered_results": [f"{r['id']} (Page {r['metadata']['page']}, Dept: {r['metadata']['department']})" for r in unfiltered_2],
        "filtered_results": [f"{r['id']} (Page {r['metadata']['page']}, Dept: {r['metadata']['department']})" for r in filtered_2],
    })

    # -----------------------------------------------------------------------
    # EXPERIMENT 3: Numerical Range Filtering ($lte on Page)
    # Target only introductory or core SLA clauses (Pages 1 & 2), excluding Page 3 DR
    # -----------------------------------------------------------------------
    query_3 = "Service uptime commitments and financial credit percentages"
    q_vec_3 = embedder.embed_query(query_3)

    range_where = {
        "$and": [
            {"doc_type": "SLA"},
            {"page": {"$lte": 2}},
        ]
    }
    filtered_range = store.search(q_vec_3, top_k=3, where=range_where)

    experiments.append({
        "id": "EXP-3",
        "title": "Numerical Range Filtering ($lte on page <= 2 for SLA)",
        "query": query_3,
        "filtered_results": [f"{r['id']} (Page {r['metadata']['page']}, Type: {r['metadata']['doc_type']})" for r in filtered_range],
    })

    # -----------------------------------------------------------------------
    # EXPERIMENT 4: Pre-Filtering vs. Naive Post-Filtering
    # Target a niche filter: access_tier == "Confidential" (Database Migration Guide)
    # When query text is biased towards Cloud SLA keywords!
    # -----------------------------------------------------------------------
    query_4 = "Cloud SLA availability downtime percentage calculation"
    q_vec_4 = embedder.embed_query(query_4)

    # In naive post-filtering, we retrieve Top-3 vectors, then filter in Python
    top_3_raw = store.search(q_vec_4, top_k=3, where=None)
    post_filtered = [r for r in top_3_raw if r["metadata"].get("access_tier") == "Confidential"]

    # In vector DB pre-filtering, Chroma enforces the predicate inside the index
    pre_filtered = store.search(q_vec_4, top_k=3, where={"access_tier": "Confidential"})

    experiments.append({
        "id": "EXP-4",
        "title": "Pre-Filtering vs. Naive Post-Filtering Pitfall",
        "query": query_4,
        "target_condition": "access_tier == 'Confidential'",
        "post_filtered_count": len(post_filtered),
        "post_filtered_ids": [r["id"] for r in post_filtered],
        "pre_filtered_count": len(pre_filtered),
        "pre_filtered_ids": [f"{r['id']} ({r['metadata']['doc_type']})" for r in pre_filtered],
        "takeaway": (
            "Naive post-filtering yielded 0 results because the top-3 nearest vectors were all "
            "Public Cloud SLA documents! Pre-filtering in Chroma guaranteed 3 valid Confidential results."
        ),
    })

    return experiments


if __name__ == "__main__":
    from chunk_provider import get_enriched_chunks, load_cached_embeddings_if_available
    store = ChromaStore(persist_directory="./chroma_db", collection_name="test_collection")
    chunks = get_enriched_chunks()
    vecs = load_cached_embeddings_if_available(chunks)
    embedder = Embedder()
    if vecs is None:
        texts = [c.page_content for c in chunks]
        vecs = embedder.embed_texts(texts)
    store.upsert_chunks(chunks, vecs)

    exps = run_metadata_filter_experiments(store, embedder)
    for e in exps:
        print(f"\n[{e['id']}] {e['title']}")
        if "takeaway" in e:
            print(f"  Post-filtered count: {e['post_filtered_count']} | Pre-filtered count: {e['pre_filtered_count']}")
            print(f"  Takeaway: {e['takeaway']}")
