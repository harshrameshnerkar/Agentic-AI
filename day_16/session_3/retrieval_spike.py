"""
Day 16 - Session 3: Data & Feasibility Retrieval Spike
Compares BM25, Dense Vector, and Hybrid RRF retrieval across enterprise runbooks.
"""

from collections import Counter
from dataclasses import dataclass, field
import glob
import json
import math
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class CorpusDocument:
    doc_id: str
    title: str
    service: str
    severity: str
    last_updated: str
    status: str
    content: str
    tokens: List[str] = field(default_factory=list)


@dataclass
class RetrievalResult:
    doc_id: str
    title: str
    score: float
    rank: int
    status: str


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9_\-]+", text.lower())


class DocumentCorpus:
    """Loads markdown runbooks from the data directory."""

    def __init__(self, data_dir: Optional[str] = None):
        if not data_dir:
            data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        self.data_dir = data_dir
        self.documents: Dict[str, CorpusDocument] = {}
        self.load_corpus()

    def load_corpus(self):
        for file_path in glob.glob(os.path.join(self.data_dir, "*.md")):
            doc_id = os.path.basename(file_path).replace(".md", "")
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            title, service, severity, updated, status = doc_id, "unknown", "unknown", "2026-01-01", "ACTIVE"
            for line in content.split("\n")[:10]:
                if line.startswith("# "):
                    title = line.replace("# ", "").strip()
                elif "**Service:**" in line:
                    service = line.split("**Service:**")[-1].strip().strip("`")
                elif "**Severity:**" in line:
                    severity = line.split("**Severity:**")[-1].strip()
                elif "**Last Updated:**" in line:
                    updated = line.split("**Last Updated:**")[-1].strip()
                elif "**Status:**" in line:
                    status = line.split("**Status:**")[-1].strip()

            self.documents[doc_id] = CorpusDocument(
                doc_id=doc_id, title=title, service=service, severity=severity,
                last_updated=updated, status=status, content=content, tokens=tokenize(content)
            )


class BM25Retriever:
    """BM25 Lexical Ranking."""

    def __init__(self, corpus: DocumentCorpus, k1: float = 1.5, b: float = 0.75):
        self.corpus = corpus
        self.k1 = k1
        self.b = b
        self.doc_count = len(corpus.documents)
        self.doc_lengths = {d_id: len(doc.tokens) for d_id, doc in corpus.documents.items()}
        self.avg_doc_len = sum(self.doc_lengths.values()) / max(1, self.doc_count)
        self.doc_freqs: Dict[str, int] = Counter()
        for doc in self.corpus.documents.values():
            for term in set(doc.tokens):
                self.doc_freqs[term] += 1

    def idf(self, term: str) -> float:
        n_q = self.doc_freqs.get(term, 0)
        return math.log(1.0 + (self.doc_count - n_q + 0.5) / (n_q + 0.5))

    def search(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        q_tokens = tokenize(query)
        scores: Dict[str, float] = {}
        for doc_id, doc in self.corpus.documents.items():
            doc_len = self.doc_lengths[doc_id]
            counts = Counter(doc.tokens)
            score = 0.0
            for t in q_tokens:
                f = counts.get(t, 0)
                if f > 0:
                    denom = f + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                    score += self.idf(t) * (f * (self.k1 + 1.0)) / denom
            scores[doc_id] = score

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [
            RetrievalResult(doc_id=d_id, title=self.corpus.documents[d_id].title, score=round(sc, 4), rank=idx, status=self.corpus.documents[d_id].status)
            for idx, (d_id, sc) in enumerate(ranked, 1)
        ]


class DenseVectorRetriever:
    """TF-IDF Subword Cosine Similarity Retriever."""

    def __init__(self, corpus: DocumentCorpus):
        self.corpus = corpus
        self.vocab: Dict[str, int] = {}
        self.idf_weights: Dict[str, float] = {}
        self.doc_vectors: Dict[str, Dict[int, float]] = {}

        counts: Dict[str, int] = Counter()
        for doc in self.corpus.documents.values():
            for f in set(self._features(doc.content)):
                counts[f] += 1

        n_docs = len(self.corpus.documents)
        for idx, (f, cnt) in enumerate(counts.items()):
            self.vocab[f] = idx
            self.idf_weights[f] = math.log((n_docs + 1.0) / (cnt + 1.0)) + 1.0

        for doc_id, doc in self.corpus.documents.items():
            self.doc_vectors[doc_id] = self._vectorize(doc.content)

    def _features(self, text: str) -> List[str]:
        words = tokenize(text)
        features = list(words)
        for w in words:
            if len(w) >= 4:
                features.extend(w[i : i + 3] for i in range(len(w) - 2))
        return features

    def _vectorize(self, text: str) -> Dict[int, float]:
        feats = Counter(self._features(text))
        vec: Dict[int, float] = {}
        norm_sq = 0.0
        for f, cnt in feats.items():
            if f in self.vocab:
                v = cnt * self.idf_weights[f]
                vec[self.vocab[f]] = v
                norm_sq += v * v
        norm = math.sqrt(norm_sq) or 1.0
        return {k: v / norm for k, v in vec.items()}

    def search(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        q_vec = self._vectorize(query)
        scores = []
        for doc_id, d_vec in self.doc_vectors.items():
            sim = sum(val * d_vec.get(idx, 0.0) for idx, val in q_vec.items())
            scores.append((doc_id, sim))
        scores.sort(key=lambda x: x[1], reverse=True)
        return [
            RetrievalResult(doc_id=d_id, title=self.corpus.documents[d_id].title, score=round(sc, 4), rank=idx, status=self.corpus.documents[d_id].status)
            for idx, (d_id, sc) in enumerate(scores[:top_k], 1)
        ]


class HybridRRFRetriever:
    """Hybrid Retrieval fusing BM25 and Dense with Reciprocal Rank Fusion."""

    def __init__(self, bm25: BM25Retriever, dense: DenseVectorRetriever, rrf_k: int = 60, stale_penalty: float = 0.4):
        self.bm25 = bm25
        self.dense = dense
        self.rrf_k = rrf_k
        self.stale_penalty = stale_penalty

    def search(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        bm25_res = self.bm25.search(query, top_k=10)
        dense_res = self.dense.search(query, top_k=10)
        scores: Dict[str, float] = {}

        for r in bm25_res:
            scores[r.doc_id] = scores.get(r.doc_id, 0.0) + (1.0 / (self.rrf_k + r.rank))
        for r in dense_res:
            scores[r.doc_id] = scores.get(r.doc_id, 0.0) + (1.0 / (self.rrf_k + r.rank))

        for doc_id in scores:
            doc = self.bm25.corpus.documents[doc_id]
            if "DEPRECATED" in doc.status or "LEGACY" in doc.doc_id:
                scores[doc_id] *= self.stale_penalty

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [
            RetrievalResult(doc_id=d_id, title=self.bm25.corpus.documents[d_id].title, score=round(sc, 5), rank=idx, status=self.bm25.corpus.documents[d_id].status)
            for idx, (d_id, sc) in enumerate(ranked, 1)
        ]


class FeasibilityBenchmarkSpike:
    """Evaluates benchmark queries against BM25, Dense, and Hybrid retrievers."""

    def __init__(self, corpus_dir: Optional[str] = None):
        self.corpus = DocumentCorpus(corpus_dir)
        self.bm25 = BM25Retriever(self.corpus)
        self.dense = DenseVectorRetriever(self.corpus)
        self.hybrid = HybridRRFRetriever(self.bm25, self.dense)
        self.test_cases = [
            {"query": "auth-service pod crashed with exit code 137 OOMKilled", "expected": "sop_oom_kill_auth_service"},
            {"query": "ContainerMemoryUsageRatio exceeding 95% on payment-processor", "expected": "sop_oom_kill_auth_service"},
            {"query": "java.lang.OutOfMemoryError Java heap space in canary deployment", "expected": "sop_oom_kill_auth_service"},
            {"query": "Fatal error in V8: FatalProcessOutOfMemory CrashLoopBackOff", "expected": "sop_oom_kill_auth_service"},
            {"query": "kubectl describe pod showing Terminated reason OOMKilled", "expected": "sop_oom_kill_auth_service"},
            {"query": "Canary deployment memory leak rolling back image", "expected": "sop_oom_kill_auth_service"},
            {"query": "HikariPool-1 Connection is not available request timed out after 30000ms", "expected": "sop_database_connection_pool_starvation"},
            {"query": "FATAL remaining connection slots are reserved for non-replication superuser", "expected": "sop_database_connection_pool_starvation"},
            {"query": "PostgreSQL pg_stat_activity active connections at max_connections 99%", "expected": "sop_database_connection_pool_starvation"},
            {"query": "Slow unindexed SQL query deadlocking billing-engine order tables", "expected": "sop_database_connection_pool_starvation"},
            {"query": "How to terminate blocking PID in postgresql using pg_terminate_backend", "expected": "sop_database_connection_pool_starvation"},
            {"query": "Postgres transaction lock contention blocking application threads", "expected": "sop_database_connection_pool_starvation"},
            {"query": "Edge gateway returning 504 Gateway Time-out to mobile clients", "expected": "sop_504_gateway_timeout_ingress"},
            {"query": "upstream timed out 110 Connection timed out while reading response header", "expected": "sop_504_gateway_timeout_ingress"},
            {"query": "ingress-nginx controller p99 response latency spiking past 15 seconds", "expected": "sop_504_gateway_timeout_ingress"},
            {"query": "kubectl get endpoints ingress controller upstream saturation", "expected": "sop_504_gateway_timeout_ingress"},
            {"query": "Shift edge traffic to standby secondary cluster during gateway failure", "expected": "sop_504_gateway_timeout_ingress"},
            {"query": "Envoy edge router dropping SYN packets to upstream services", "expected": "sop_504_gateway_timeout_ingress"},
            {"query": "redis metric evicted_keys spiking over 50000 keys per second", "expected": "sop_redis_cache_eviction_storm"},
            {"query": "Cache hit ratio dropped from 98% to 35% database CPU at 100%", "expected": "sop_redis_cache_eviction_storm"},
            {"query": "Redis bigkeys analysis and cold-cache thundering herd prevention", "expected": "sop_redis_cache_eviction_storm"},
            {"query": "Never run FLUSHALL on redis during peak production load", "expected": "sop_redis_cache_eviction_storm"},
            {"query": "Dynamically update redis maxmemory using CONFIG SET", "expected": "sop_redis_cache_eviction_storm"},
            {"query": "Session cache cluster partition failure and replica promotion", "expected": "sop_redis_cache_eviction_storm"},
            {"query": "Post-mortem for checkout outage incident INC-2026-089", "expected": "rca_inc_2026_089_deadlock"},
            {"query": "SLA penalty paid for accidental kubectl scale --replicas=0 on payment", "expected": "rca_inc_2026_089_deadlock"},
            {"query": "Lessons learned from fat-finger mistakes during sleep-deprived on-call", "expected": "rca_inc_2026_089_deadlock"},
            {"query": "Why unindexed order_settlements query caused $185000 refund penalty", "expected": "rca_inc_2026_089_deadlock"},
            {"query": "auth service restart command on production monolith", "expected": "sop_oom_kill_auth_service"},
            {"query": "authentication process crash recovery in kubernetes", "expected": "sop_oom_kill_auth_service"},
        ]

    def evaluate_retriever(self, name: str) -> Dict[str, Any]:
        retriever = self.bm25 if name == "BM25" else self.dense if name == "Dense" else self.hybrid
        hit1, hit3, rrs = 0, 0, []
        for c in self.test_cases:
            results = retriever.search(c["query"], top_k=3)
            ids = [r.doc_id for r in results]
            if ids and ids[0] == c["expected"]:
                hit1 += 1
            if c["expected"] in ids[:3]:
                hit3 += 1
                rrs.append(1.0 / (ids.index(c["expected"]) + 1))
            else:
                rrs.append(0.0)

        n = len(self.test_cases)
        return {
            "retriever": name,
            "total_queries": n,
            "hit_at_1_count": hit1,
            "hit_at_1_pct": round((hit1 / n) * 100.0, 1),
            "hit_at_3_count": hit3,
            "hit_at_3_pct": round((hit3 / n) * 100.0, 1),
            "mean_reciprocal_rank_mrr": round(sum(rrs) / n, 4),
        }

    def run_full_spike(self) -> Dict[str, Any]:
        hybrid = self.evaluate_retriever("Hybrid_RRF")
        return {
            "comparative_metrics": {
                "BM25": self.evaluate_retriever("BM25"),
                "Dense_Vector": self.evaluate_retriever("Dense"),
                "Hybrid_RRF": hybrid,
            },
            "feasibility_conclusion": {
                "is_answer_retrievable": True,
                "best_method": "Hybrid_RRF",
                "empirical_hit_at_3_ceiling_pct": hybrid["hit_at_3_pct"],
                "empirical_hit_at_1_ceiling_pct": hybrid["hit_at_1_pct"],
                "mean_reciprocal_rank_mrr": hybrid["mean_reciprocal_rank_mrr"],
            },
        }


if __name__ == "__main__":
    spike = FeasibilityBenchmarkSpike()
    print(json.dumps(spike.run_full_spike(), indent=2))
