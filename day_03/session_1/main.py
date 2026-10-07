"""
DAY 3 - SESSION 1: EMBEDDINGS, VECTOR SIMILARITY & FAILURE MODES
Main entrypoint orchestrating the modular vector search pipeline.
"""

import sys
import time
from dataset import SENTENCES
from embedder import get_embeddings_batch, EMBEDDING_MODEL
from search import search_top_k

# Ensure UTF-8 output on Windows terminal
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")


def print_search_results(query_title: str, query_text: str, results: list[dict]):
    """Pretty prints the top-k search results."""
    print(f"\n[{query_title}]: \"{query_text}\"")
    print("-" * 95)
    for r in results:
        print(f"#{r['index']:<2} | Cosine: {r['cosine_sim']:.4f} | L2: {r['euclidean_dist']:.3f} | {r['text']}")


def main():
    print("=" * 95)
    print(" DAY 3 - SESSION 1: EMBEDDINGS, VECTOR SIMILARITY & INSPECTION")
    print("=" * 95)
    print(f"Embedding Model  : {EMBEDDING_MODEL}")
    print(f"Corpus Size      : {len(SENTENCES)} sentences (Modularized across dataset.py, embedder.py, metrics.py)")
    print("Computing embedding vectors in batches...")

    # Step 1: Compute corpus embeddings
    corpus_matrix = get_embeddings_batch(SENTENCES, batch_size=25)
    dim = corpus_matrix.shape[1]
    print(f"Embeddings Shape : {corpus_matrix.shape} (Dimensions: {dim} coordinates per vector)")
    print("=" * 95)

    # -------------------------------------------------------------
    # EXPERIMENT 1: SEMANTIC SEARCH WITHOUT KEYWORD OVERLAP
    # -------------------------------------------------------------
    query_1 = "healthy eating and nutritious green meals"
    res_1 = search_top_k(query_1, SENTENCES, corpus_matrix, k=5)
    print_search_results("QUERY 1 - SEMANTIC MATCH (No shared keywords)", query_1, res_1)

    time.sleep(2.0)

    # -------------------------------------------------------------
    # EXPERIMENT 2: COSINE SIMILARITY VS. EUCLIDEAN DISTANCE
    # -------------------------------------------------------------
    query_2 = "software engineering with deep neural networks"
    res_2 = search_top_k(query_2, SENTENCES, corpus_matrix, k=5)
    print_search_results("QUERY 2 - COSINE vs. EUCLIDEAN COMPARISON", query_2, res_2)

    time.sleep(2.0)

    # -------------------------------------------------------------
    # EXPERIMENT 3: INSPECTING WHERE EMBEDDINGS GET IT WRONG (NEGATION TRAP)
    # -------------------------------------------------------------
    query_3 = "I do NOT want a phone with a terrible camera"
    res_3 = search_top_k(query_3, SENTENCES, corpus_matrix, k=5)
    print_search_results("QUERY 3 - THE NEGATION FAILURE INSPECTION", query_3, res_3)

    time.sleep(2.0)

    # -------------------------------------------------------------
    # EXPERIMENT 4: ANTONYM / POLARITY CONFUSION
    # -------------------------------------------------------------
    query_4 = "The company suffered insolvency and went out of business"
    res_4 = search_top_k(query_4, SENTENCES, corpus_matrix, k=5)
    print_search_results("QUERY 4 - ANTONYM & FINANCIAL POLARITY TRAP", query_4, res_4)

    # -------------------------------------------------------------
    # EDUCATIONAL SUMMARY & FAILURE ANALYSIS WRITEUP
    # -------------------------------------------------------------
    print("\n" + "=" * 95)
    print(" CRITICAL ANALYSIS: WHERE EMBEDDINGS FAIL & WHY")
    print("=" * 95)
    print("1. Negation Blindness:")
    print("   - Embeddings map texts to semantic topic clusters (e.g. 'smartphones & cameras').")
    print("   - 'I love this phone, great camera' and 'I do NOT like this phone, terrible camera'")
    print("     receive nearly identical cosine scores (~0.75-0.85) because they share 90% of the same topic space.")
    print("   - Cosine similarity measures topical proximity, NOT logical negation or truth polarity.")
    print("\n2. Antonym Confusion:")
    print("   - Antonym pairs like 'steaming hot soup' vs 'freezing cold soup' or 'declared bankruptcy'")
    print("     vs 'avoided bankruptcy' score extremely close together in vector space.")
    print("\n3. How Production RAG Systems Fix This:")
    print("   - Hybrid Search: Combine Vector embeddings with Lexical BM25 (exact keyword matching).")
    print("   - Cross-Encoder Rerankers: A secondary model (like BGE-Reranker or Cohere Rerank)")
    print("     reads (query, passage) together through cross-attention to catch negations and subtle qualifiers.")
    print("=" * 95)
    print("Session 1 task completed successfully!")
    print("=" * 95)


if __name__ == "__main__":
    main()
