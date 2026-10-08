"""Day 16 - Session 3: Unit & Integration Tests for Retrieval Spike & Feasibility Note."""

import os
import unittest

try:
    from .retrieval_spike import (
        DocumentCorpus,
        BM25Retriever,
        DenseVectorRetriever,
        HybridRRFRetriever,
        FeasibilityBenchmarkSpike,
    )
except ImportError:
    from retrieval_spike import (
        DocumentCorpus,
        BM25Retriever,
        DenseVectorRetriever,
        HybridRRFRetriever,
        FeasibilityBenchmarkSpike,
    )


class TestDay16Session3RetrievalSpike(unittest.TestCase):
    """Test suite validating enterprise data audit, retrieval spike, and feasibility metrics."""

    def setUp(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.corpus = DocumentCorpus(os.path.join(self.base_dir, "data"))
        self.bm25 = BM25Retriever(self.corpus)
        self.dense = DenseVectorRetriever(self.corpus)
        self.hybrid = HybridRRFRetriever(self.bm25, self.dense)

    def test_corpus_loading(self):
        """Verifies that all enterprise SOPs and post-mortems are loaded with valid metadata."""
        self.assertGreaterEqual(len(self.corpus.documents), 6)
        expected_docs = [
            "sop_oom_kill_auth_service",
            "sop_database_connection_pool_starvation",
            "sop_504_gateway_timeout_ingress",
            "sop_redis_cache_eviction_storm",
            "sop_stale_legacy_v1_auth",
            "rca_inc_2026_089_deadlock",
        ]
        for doc_id in expected_docs:
            self.assertIn(doc_id, self.corpus.documents)
            doc = self.corpus.documents[doc_id]
            self.assertGreater(len(doc.tokens), 20)
            self.assertTrue(doc.title)

    def test_bm25_retrieval(self):
        """Verifies lexical keyword retrieval accuracy on targeted queries."""
        query = "HikariPool connection timeout postgresql pg_stat_activity"
        results = self.bm25.search(query, top_k=3)
        self.assertGreater(len(results), 0)
        top_doc_id = results[0].doc_id
        self.assertEqual(top_doc_id, "sop_database_connection_pool_starvation")

    def test_dense_vector_retrieval(self):
        """Verifies semantic cosine similarity vector search."""
        query = "process running out of ram memory leak exit code 137"
        results = self.dense.search(query, top_k=3)
        self.assertGreater(len(results), 0)
        top_doc_id = results[0].doc_id
        self.assertEqual(top_doc_id, "sop_oom_kill_auth_service")

    def test_hybrid_rrf_and_stale_penalty(self):
        """Verifies that Hybrid RRF penalizes deprecated documents and ranks active SOPs first."""
        query = "auth-service canary deployment memory leak crash recovery"
        results = self.hybrid.search(query, top_k=3)
        self.assertGreater(len(results), 0)
        # Active modern SOP must rank above deprecated legacy document
        top_doc_id = results[0].doc_id
        self.assertEqual(top_doc_id, "sop_oom_kill_auth_service")
        self.assertNotEqual(top_doc_id, "sop_stale_legacy_v1_auth")

    def test_benchmark_spike_execution(self):
        """Verifies 30-case benchmark evaluation hits ceiling requirements."""
        spike = FeasibilityBenchmarkSpike(os.path.join(self.base_dir, "data"))
        res = spike.run_full_spike()

        comp = res["comparative_metrics"]
        hybrid = comp["Hybrid_RRF"]
        self.assertGreaterEqual(hybrid["hit_at_3_pct"], 90.0)
        self.assertGreaterEqual(hybrid["hit_at_1_pct"], 85.0)
        self.assertGreaterEqual(hybrid["mean_reciprocal_rank_mrr"], 0.90)

        fc = res["feasibility_conclusion"]
        self.assertTrue(fc["is_answer_retrievable"])
        self.assertEqual(fc["best_method"], "Hybrid_RRF")

    def test_feasibility_note_artifact(self):
        """Verifies presence and depth of the official FEASIBILITY_NOTE.md artifact."""
        note_path = os.path.join(self.base_dir, "FEASIBILITY_NOTE.md")
        self.assertTrue(os.path.isfile(note_path))

        with open(note_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertGreater(len(content), 1500)
            self.assertIn("Audit of Existing Enterprise Systems", content)
            self.assertIn("2-Hour Timeboxed Retrieval Spike", content)
            self.assertIn("Is the Answer Retrievable", content)
            self.assertIn("What is the Ceiling", content)
            self.assertIn("Architectural Recommendation", content)


if __name__ == "__main__":
    unittest.main()
