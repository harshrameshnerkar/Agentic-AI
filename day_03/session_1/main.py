"""
Day 03 - Session 01: Embeddings & Vector Similarity
Demonstrates semantic search using cosine similarity and Euclidean distance,
and explores failure modes such as negation traps.
"""

from dataset import SENTENCES
from embedder import get_embeddings_batch, EMBEDDING_MODEL
from search import search_top_k


def print_search_results(title: str, query: str, results: list[dict]):
    print(f"\n{title}: '{query}'")
    for r in results:
        print(f"  #{r['index']} (Cosine: {r['cosine_sim']:.4f}, L2: {r['euclidean_dist']:.3f}): {r['text']}")


def main():
    print(f"Running vector similarity search with {EMBEDDING_MODEL}...")
    corpus_matrix = get_embeddings_batch(SENTENCES, batch_size=25)

    # 1. Semantic search without keyword overlap
    q1 = "healthy eating and nutritious green meals"
    print_search_results("1. Semantic Match (No shared keywords)", q1, search_top_k(q1, SENTENCES, corpus_matrix, k=3))

    # 2. Comparing Cosine vs Euclidean
    q2 = "software engineering with deep neural networks"
    print_search_results("2. Technical Search", q2, search_top_k(q2, SENTENCES, corpus_matrix, k=3))

    # 3. Negation trap: embeddings struggle with 'NOT'
    q3 = "I do NOT want a phone with a terrible camera"
    print_search_results("3. Negation Trap (Vector limitation)", q3, search_top_k(q3, SENTENCES, corpus_matrix, k=3))


if __name__ == "__main__":
    main()
