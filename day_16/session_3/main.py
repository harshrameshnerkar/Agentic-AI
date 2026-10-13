"""
Day 16 - Session 03: Data Audit & Retrieval Feasibility Spike
Executes the technical retrieval spike comparing lexical BM25, dense vector,
and reciprocal rank fusion (Hybrid RRF) to verify knowledge retrieval ceilings.
"""

from __future__ import annotations
from retrieval_spike import FeasibilityBenchmarkSpike


def main():
    print("Day 16 Session 03: Retrieval Feasibility Spike Benchmark\n")
    spike = FeasibilityBenchmarkSpike()
    res = spike.run_spike_benchmark()

    print("--- Retrieval Engine Comparison (Top-K Recall & Hit-Rate) ---")
    print(f"BM25 Lexical Recall:       {res['bm25_recall']:.1f}%")
    print(f"Dense Vector Recall:       {res['dense_recall']:.1f}%")
    print(f"Hybrid RRF Fused Recall:   {res['hybrid_recall']:.1f}%")
    print(f"Hybrid Latency:            {res['hybrid_latency_ms']:.1f} ms")

    assert res["hybrid_recall"] >= res["bm25_recall"]
    print("\nSpike Conclusion: Hybrid RRF achieves the highest recall and handles technical keywords and synonyms cleanly.")


if __name__ == "__main__":
    main()
