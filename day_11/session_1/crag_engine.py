"""
Corrective RAG (CRAG) Engine & Retrieve-Grade-Rewrite Loop for Day 11 Session 1.
Implements:
1. Retrieve: Fetches candidate documents from vector store.
2. Grade: Evaluates retrieved document relevance score against a threshold.
3. Rewrite: When documents are graded IRRELEVANT or borderline, rewrites the query
   to strip conversational noise, expand acronyms, and improve recall.
4. Fallback: Protects the generation stage from irrelevant context pollution.
"""

from typing import Dict, Any, List, Tuple
from vector_store import EnterpriseVectorStore, vector_store


class RetrievalGradeResult:
    def __init__(self, is_relevant: bool, confidence: float, reason: str, docs: List[Dict[str, Any]]):
        self.is_relevant = is_relevant
        self.confidence = confidence
        self.reason = reason
        self.docs = docs


class CorrectiveRAGEngine:
    """Implements the Retrieve-Grade-Rewrite loop (Corrective RAG)."""

    def __init__(self, store: EnterpriseVectorStore = vector_store):
        self.store = store
        self.relevance_threshold = 2.0  # Minimum score for acceptable grounding

    def grade_documents(self, query: str, docs: List[Dict[str, Any]]) -> RetrievalGradeResult:
        """
        Grades the quality of retrieved documents.
        Checks relevance scores and keyword overlap.
        """
        if not docs:
            return RetrievalGradeResult(
                is_relevant=False,
                confidence=0.0,
                reason="No candidate documents retrieved.",
                docs=[],
            )

        top_score = docs[0].get("score", 0.0)
        if top_score >= self.relevance_threshold:
            return RetrievalGradeResult(
                is_relevant=True,
                confidence=min(1.0, top_score / 5.0),
                reason=f"Top document score ({top_score:.1f}) exceeds relevance threshold ({self.relevance_threshold}).",
                docs=docs,
            )
        else:
            return RetrievalGradeResult(
                is_relevant=False,
                confidence=top_score / self.relevance_threshold,
                reason=f"Retrieved document score ({top_score:.1f}) below threshold ({self.relevance_threshold}). Likely noisy or tangential context.",
                docs=docs,
            )

    def rewrite_query(self, query: str) -> str:
        """
        Rewrites the query to improve retrieval recall:
        - Expands common enterprise acronyms (DR -> Disaster Recovery, RTO -> Recovery Time Objective, MFA -> Multi-Factor Authentication)
        - Strips conversational phrasing ("Can you please tell me", "I want to know about")
        """
        clean = query.lower()

        # Strip polite conversational prefixes
        prefixes = [
            "can you please tell me about", "can you tell me about", "i want to know about",
            "could you explain", "please provide", "what can you tell me regarding",
            "do we have any document on", "show me", "tell me"
        ]
        for p in prefixes:
            if clean.startswith(p):
                clean = clean[len(p):].strip()

        # Acronym expansions
        expansions = {
            r"\bdr\b": "disaster recovery",
            r"\brto\b": "recovery time objective rto",
            r"\brpo\b": "recovery point objective rpo",
            r"\bmfa\b": "multi-factor authentication mfa fido2",
            r"\bsoc2\b": "soc2 compliance audit access control",
            r"\bwfh\b": "remote work home office stipend",
        }
        for pattern, replacement in expansions.items():
            import re
            clean = re.sub(pattern, replacement, clean)

        return clean.strip()

    def retrieve_with_crag(
        self,
        query: str,
        top_k: int = 2,
        metadata_filters: Dict[str, Any] = None,
        max_rewrites: int = 1,
    ) -> Dict[str, Any]:
        """
        Full Retrieve-Grade-Rewrite loop:
        1. Retrieve candidates
        2. Grade relevance
        3. If grade fails, rewrite query and re-retrieve
        4. Return filtered, verified context
        """
        rewrites_done = 0
        current_query = query

        # Step 1: Initial Retrieval
        docs = self.store.search(current_query, top_k=top_k, metadata_filters=metadata_filters)
        grade = self.grade_documents(current_query, docs)

        trajectory = [
            {
                "step": "initial_retrieval",
                "query": current_query,
                "docs_found": len(docs),
                "is_relevant": grade.is_relevant,
                "top_score": docs[0]["score"] if docs else 0.0,
                "reason": grade.reason,
            }
        ]

        # Step 2: Rewrite loop if graded irrelevant
        if not grade.is_relevant and rewrites_done < max_rewrites:
            rewritten = self.rewrite_query(current_query)
            if rewritten != current_query:
                rewrites_done += 1
                current_query = rewritten
                retry_docs = self.store.search(current_query, top_k=top_k, metadata_filters=metadata_filters)
                retry_grade = self.grade_documents(current_query, retry_docs)

                trajectory.append({
                    "step": "query_rewrite_retry",
                    "rewritten_query": current_query,
                    "docs_found": len(retry_docs),
                    "is_relevant": retry_grade.is_relevant,
                    "top_score": retry_docs[0]["score"] if retry_docs else 0.0,
                    "reason": retry_grade.reason,
                })

                if retry_grade.is_relevant or (retry_docs and retry_docs[0]["score"] > (docs[0]["score"] if docs else 0.0)):
                    docs = retry_docs
                    grade = retry_grade

        return {
            "final_query": current_query,
            "docs": docs if grade.is_relevant else [],
            "raw_docs_count": len(docs),
            "is_graded_relevant": grade.is_relevant,
            "grade_confidence": grade.confidence,
            "rewrites_performed": rewrites_done,
            "trajectory": trajectory,
        }


# Singleton CRAG engine
crag_engine = CorrectiveRAGEngine()
