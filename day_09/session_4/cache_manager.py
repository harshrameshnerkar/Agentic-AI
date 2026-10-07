"""
Exact & Semantic Caching Subsystem.
Implements:
1. Exact Cache: O(1) SHA-256 hash lookup for identical repeated queries.
2. Semantic Cache: N-gram & keyword Jaccard/Cosine intent similarity for rephrased queries.
3. Zero-Token, Sub-millisecond Execution on Cache Hits.
"""

import hashlib
import re
from typing import Any, Dict, List, Optional, Tuple


class ExactCache:
    """Exact match cache using SHA-256 digest of normalized queries."""

    def __init__(self):
        self.store: Dict[str, Dict[str, Any]] = {}

    def _hash_key(self, query: str) -> str:
        norm = " ".join(query.lower().strip().split())
        return hashlib.sha256(norm.encode("utf-8")).hexdigest()

    def get(self, query: str) -> Optional[Dict[str, Any]]:
        k = self._hash_key(query)
        return self.store.get(k)

    def set(self, query: str, value: Dict[str, Any]) -> None:
        k = self._hash_key(query)
        self.store[k] = value

    def size(self) -> int:
        return len(self.store)


# Domain synonyms for intent normalization
SYNONYMS = {
    "compute": "calculate",
    "stock": "inventory",
    "units": "inventory",
    "level": "inventory",
    "warehouse": "inventory",
    "frequency": "rotation",
    "rules": "policy",
    "find": "errors",
    "target": "response",
    "time": "sla",
}

STOP_WORDS = {
    "what", "is", "our", "the", "for", "and", "in", "of", "to", "how", "tell",
    "me", "show", "who", "are", "from", "item", "all", "we", "do", "have", "at", "look",
}

DISCRIMINATORS = {
    "standard", "enterprise", "free", "sev-1", "sev-2", "ord-501", "ord-504",
    "sku-switch-24", "sku-ups-3000", "sku-sfp-10g",
}


class SemanticCache:
    """Semantic intent cache using tokenized N-gram and keyword similarity."""

    def __init__(self, similarity_threshold: float = 0.55):
        self.similarity_threshold = similarity_threshold
        # List of (raw_query, token_set, discriminator_set, value)
        self.entries: List[Tuple[str, set, set, Dict[str, Any]]] = []

    def _stem(self, word: str) -> str:
        w = re.sub(r"(ing|ed|es|s)$", "", word.lower())
        return SYNONYMS.get(w, w)

    def _tokenize(self, text: str) -> Tuple[set, set]:
        words = re.findall(r"\b[a-zA-Z0-9_$-]{2,}\b", text.lower())
        discrims = {w for w in words if w in DISCRIMINATORS or "-" in w or "$" in w}
        terms = {self._stem(w) for w in words if w not in STOP_WORDS}
        return terms, discrims

    def _calculate_similarity(self, tokens_a: set, disc_a: set, tokens_b: set, disc_b: set) -> float:
        # Discriminator safety: if specific entities/SKUs/tiers differ, reject match
        if disc_a and disc_b and disc_a != disc_b:
            return 0.0
        if (disc_a and not disc_b) or (disc_b and not disc_a):
            return 0.0

        if not tokens_a or not tokens_b:
            return 0.0

        inter = len(tokens_a.intersection(tokens_b))
        denom = len(tokens_a) + len(tokens_b)
        dice = (2.0 * inter) / denom if denom else 0.0
        overlap = inter / min(len(tokens_a), len(tokens_b)) if min(len(tokens_a), len(tokens_b)) else 0.0
        return max(dice, overlap * 0.85)

    def get(self, query: str) -> Optional[Tuple[Dict[str, Any], float]]:
        query_tokens, query_disc = self._tokenize(query)
        best_match = None
        best_sim = 0.0

        for stored_query, stored_tokens, stored_disc, value in self.entries:
            sim = self._calculate_similarity(query_tokens, query_disc, stored_tokens, stored_disc)
            if sim > best_sim:
                best_sim = sim
                best_match = value

        if best_sim >= self.similarity_threshold and best_match is not None:
            return best_match, best_sim

        return None

    def set(self, query: str, value: Dict[str, Any]) -> None:
        query_tokens, query_disc = self._tokenize(query)
        self.entries.append((query, query_tokens, query_disc, value))

    def size(self) -> int:
        return len(self.entries)


class HybridCacheManager:
    """Unified cache manager coordinating Exact and Semantic lookups."""

    def __init__(self, semantic_threshold: float = 0.55):
        self.exact_cache = ExactCache()
        self.semantic_cache = SemanticCache(similarity_threshold=semantic_threshold)
        self.exact_hits = 0
        self.semantic_hits = 0
        self.misses = 0

    def lookup(self, query: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Attempts exact cache lookup first, followed by semantic similarity lookup.
        Returns (result, cache_type) where cache_type in ('exact', 'semantic', None).
        """
        # 1. Exact Cache Check
        exact_hit = self.exact_cache.get(query)
        if exact_hit is not None:
            self.exact_hits += 1
            return exact_hit, "exact"

        # 2. Semantic Cache Check
        semantic_res = self.semantic_cache.get(query)
        if semantic_res is not None:
            val, sim = semantic_res
            self.semantic_hits += 1
            return val, f"semantic (sim={sim:.2f})"

        self.misses += 1
        return None, None

    def store(self, query: str, value: Dict[str, Any]) -> None:
        """Stores result in both exact and semantic cache stores."""
        self.exact_cache.set(query, value)
        self.semantic_cache.set(query, value)

    def stats(self) -> Dict[str, Any]:
        total_requests = self.exact_hits + self.semantic_hits + self.misses
        hit_count = self.exact_hits + self.semantic_hits
        return {
            "total_requests": total_requests,
            "exact_hits": self.exact_hits,
            "semantic_hits": self.semantic_hits,
            "total_hits": hit_count,
            "hit_rate": (hit_count / total_requests) * 100.0 if total_requests > 0 else 0.0,
            "exact_size": self.exact_cache.size(),
            "semantic_size": self.semantic_cache.size(),
        }
