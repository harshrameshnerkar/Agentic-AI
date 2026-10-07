"""
reranker.py
===========
STAGE 3 OF RAG: CROSS-ENCODER RERANKER (Day 3 - Session 4)

Responsibilities:
1. Joint Cross-Attention: Feeds [CLS] Query [SEP] Passage [SEP] to CrossEncoder.
2. Accurate Relevance Scoring: Computes logit scores and sigmoid probabilities.
3. Candidate Re-Ordering: Re-ranks passages so the most relevant chunk is at Rank #1.
"""

from typing import List, Dict, Any, Union
import re
import numpy as np

DEFAULT_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# Safe import: never crash if sentence-transformers is missing in active environment
try:
    from sentence_transformers import CrossEncoder
    HAS_CROSS_ENCODER = True
except (ImportError, Exception):
    CrossEncoder = None
    HAS_CROSS_ENCODER = False


class RerankedPassage:
    """
    Structured passage representation enriched with Cross-Encoder scoring.
    Defined independently of external ML libraries so downstream imports never fail.
    """
    def __init__(
        self,
        chunk_id: str,
        content: str,
        source: str,
        page: int,
        bi_encoder_rank: int,
        reranker_rank: int,
        similarity: float,
        rerank_score: float,
        relevance_prob: float,
        metadata: Dict[str, Any],
    ):
        self.chunk_id = chunk_id
        self.content = content
        self.source = source
        self.page = page
        self.bi_encoder_rank = bi_encoder_rank
        self.reranker_rank = reranker_rank
        self.similarity = similarity
        self.rerank_score = rerank_score
        self.relevance_prob = relevance_prob
        self.metadata = metadata

    def __repr__(self) -> str:
        return (
            f"<Reranked #{self.reranker_rank} (was #{self.bi_encoder_rank}) "
            f"[{self.source}:P{self.page}] logit={self.rerank_score:+.2f} prob={self.relevance_prob*100:.1f}%>"
        )


class CrossEncoderReranker:
    """
    Reranks candidate passages using token-level Cross-Encoder self-attention.
    Provides robust fallback to semantic/lexical hybrid scoring if sentence-transformers
    is not installed in the running Python environment.
    """
    def __init__(self, model_name: str = DEFAULT_MODEL_NAME):
        self.model_name = model_name
        self.model = None

        if HAS_CROSS_ENCODER:
            try:
                self.model = CrossEncoder(model_name)
            except Exception as e:
                print(f"  [Reranker] Notice: Could not load CrossEncoder model '{model_name}': {e}")
                print("  [Reranker] Falling back to semantic-lexical hybrid reranker.")
                self.model = None
        else:
            print("  [Reranker Notice] 'sentence-transformers' not found in active Python environment.")
            print("  [Reranker Notice] Operating in semantic-lexical hybrid fallback mode.")
            print("  [Reranker Notice] (To activate neural Cross-Encoder: pip install sentence-transformers)")

    def _fallback_score(self, query: str, content: str, bi_sim: float) -> float:
        """
        Computes a resilient hybrid score when neural Cross-Encoder is unavailable:
        Blends Bi-Encoder cosine similarity with query keyword term-overlap.
        """
        q_words = set(re.findall(r"\w+", query.lower())) if "re" in globals() else set(query.lower().split())
        c_words = set(re.findall(r"\w+", content.lower())) if "re" in globals() else set(content.lower().split())
        
        overlap = len(q_words & c_words) / max(1, len(q_words))
        # Logit scale roughly between -3.0 and +5.0
        logit = (bi_sim * 4.0) + (overlap * 3.5) - 2.0
        return float(logit)

    def rerank(
        self,
        query: str,
        candidates: List[Any],
        top_n: int = 3,
    ) -> List[RerankedPassage]:
        """
        Reranks a list of candidate passages.
        Accepts either CandidatePassage objects or candidate dicts.
        """
        if not candidates:
            return []

        # Prepare pairs and content
        pairs = []
        contents = []
        for c in candidates:
            text = c.content if hasattr(c, "content") else c.get("content", "")
            pairs.append((query, text))
            contents.append(text)

        # Compute scores (Neural Cross-Encoder or Hybrid Fallback)
        if self.model is not None:
            raw_scores = self.model.predict(pairs)
        else:
            raw_scores = []
            for idx, c in enumerate(candidates):
                sim = c.similarity if hasattr(c, "similarity") else c.get("similarity", 0.5)
                raw_scores.append(self._fallback_score(query, contents[idx], sim))

        # Build scored list
        scored = []
        for idx, c in enumerate(candidates):
            raw_score = float(raw_scores[idx])
            prob = 1.0 / (1.0 + np.exp(-raw_score))

            chunk_id = c.chunk_id if hasattr(c, "chunk_id") else c.get("id", f"c_{idx}")
            content = contents[idx]
            source = c.source if hasattr(c, "source") else c.get("source", "unknown")
            page = c.page if hasattr(c, "page") else c.get("page", 1)
            bi_rank = c.bi_encoder_rank if hasattr(c, "bi_encoder_rank") else c.get("bi_encoder_rank", idx + 1)
            similarity = c.similarity if hasattr(c, "similarity") else c.get("similarity", 0.0)
            metadata = c.metadata if hasattr(c, "metadata") else c.get("metadata", {})

            scored.append({
                "chunk_id": chunk_id,
                "content": content,
                "source": source,
                "page": page,
                "bi_encoder_rank": bi_rank,
                "similarity": similarity,
                "rerank_score": round(raw_score, 4),
                "relevance_prob": round(float(prob), 4),
                "metadata": metadata,
            })

        # Sort descending by reranking score
        scored.sort(key=lambda x: x["rerank_score"], reverse=True)

        # Assemble top_n RerankedPassages
        reranked_results: List[RerankedPassage] = []
        for new_rank, item in enumerate(scored[:top_n], start=1):
            reranked_results.append(
                RerankedPassage(
                    chunk_id=item["chunk_id"],
                    content=item["content"],
                    source=item["source"],
                    page=item["page"],
                    bi_encoder_rank=item["bi_encoder_rank"],
                    reranker_rank=new_rank,
                    similarity=item["similarity"],
                    rerank_score=item["rerank_score"],
                    relevance_prob=item["relevance_prob"],
                    metadata=item["metadata"],
                )
            )

        return reranked_results


if __name__ == "__main__":
    print("--- [STAGE 3: RERANKER STANDALONE VERIFICATION] ---")
    reranker = CrossEncoderReranker()
    sample_query = "What is the maximum nightly hotel rate in NYC?"
    sample_candidates = [
        {
            "id": "c1",
            "content": "International business travel requires passports to have at least six months validity.",
            "source": "employee_travel_policy.pdf",
            "page": 1,
            "bi_encoder_rank": 1,
            "similarity": 0.58,
        },
        {
            "id": "c2",
            "content": "Tier 1 high-cost cities (New York City, San Francisco, London) have a lodging cap of $250.00 USD per night.",
            "source": "employee_travel_policy.pdf",
            "page": 2,
            "bi_encoder_rank": 2,
            "similarity": 0.55,
        },
        {
            "id": "c3",
            "content": "Database migrations require taking a full schema snapshot 24 hours prior to production cutover.",
            "source": "database_migration_guide.pdf",
            "page": 2,
            "bi_encoder_rank": 3,
            "similarity": 0.32,
        },
    ]

    results = reranker.rerank(sample_query, sample_candidates, top_n=2)
    print(f"\nReranked Top {len(results)} candidate passages for query: '{sample_query}':")
    for r in results:
        print(f"  • Rank #{r.reranker_rank} (Bi-Encoder was #{r.bi_encoder_rank}): [{r.source}:P{r.page}] (score={r.rerank_score:+.2f}, prob={r.relevance_prob*100:.1f}%)")
        print(f"    Content: {r.content}")

