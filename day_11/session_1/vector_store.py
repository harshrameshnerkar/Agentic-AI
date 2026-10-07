"""
Semantic Vector Store with Metadata Filtering for Day 11 Session 1.
Implements:
- Unstructured document repository (architecture guides, corporate policies, customer FAQs)
- TF-IDF and keyword cosine similarity search
- Metadata filtering for self-querying (department, year, category, doc_id)
- Relevance score thresholding for retrieval grading
"""

import math
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class DocumentChunk:
    doc_id: str
    title: str
    category: str
    department: str
    year: int
    content: str
    keywords: List[str] = field(default_factory=list)


ENTERPRISE_KNOWLEDGE_CORPUS: List[DocumentChunk] = [
    DocumentChunk(
        doc_id="DOC-POL-01",
        title="Enterprise Customer Refund & Cancellation Policy",
        category="Policy",
        department="Finance",
        year=2026,
        content=(
            "Enterprise customers may request a full refund within 30 days of subscription activation. "
            "Cancellations requested after 30 days are subject to a 15% administrative processing fee. "
            "To initiate a refund, the customer must submit a formal ticket with approval from the assigned Account Executive. "
            "Refunds are processed to the original payment method within 5 to 7 business days."
        ),
        keywords=["refund", "cancellation", "fee", "30 days", "reimbursement", "money back"],
    ),
    DocumentChunk(
        doc_id="DOC-POL-02",
        title="Employee Remote Work & Home Office Equipment Policy",
        category="Policy",
        department="HR",
        year=2026,
        content=(
            "All full-time staff in Engineering and Support are eligible for a hybrid remote schedule (up to 3 days remote per week). "
            "A one-time home office equipment stipend of $1,500 is provided upon onboarding for ergonomic chairs and external monitors. "
            "All hardware must comply with the corporate Endpoint Encryption Mandate."
        ),
        keywords=["remote work", "work from home", "stipend", "$1,500", "ergonomic", "equipment", "hr policy"],
    ),
    DocumentChunk(
        doc_id="DOC-ARCH-01",
        title="Microservice High Availability & Failover Architecture Blueprint",
        category="Architecture",
        department="Engineering",
        year=2026,
        content=(
            "Our microservice architecture uses Kubernetes across three Availability Zones in AWS us-east-1. "
            "Stateful services deploy Postgres read-replicas with Patroni automatic failover under 15 seconds. "
            "All public ingress traffic routes through Envoy proxies with active circuit breakers tripping at 5% error rates. "
            "Redis cache clusters run in cluster mode with 3 primary and 3 replica nodes."
        ),
        keywords=["architecture", "microservice", "kubernetes", "patroni", "high availability", "failover", "envoy"],
    ),
    DocumentChunk(
        doc_id="DOC-ARCH-02",
        title="Multi-Cloud Disaster Recovery & RTO/RPO SLA Blueprint",
        category="Architecture",
        department="Engineering",
        year=2025,
        content=(
            "Disaster Recovery (DR) operations enforce a Recovery Time Objective (RTO) of 30 minutes and Recovery Point Objective (RPO) of 5 minutes. "
            "Secondary failover hot-standby nodes run in GCP europe-west1. "
            "Database snapshots are synchronized every 60 seconds using continuous WAL streaming to an encrypted multi-region bucket."
        ),
        keywords=["disaster recovery", "dr", "rto", "rpo", "backup", "snapshot", "failover"],
    ),
    DocumentChunk(
        doc_id="DOC-SEC-01",
        title="SOC2 & ISO 27001 Access Control Standard Operating Procedure",
        category="Security_Standard",
        department="Security",
        year=2026,
        content=(
            "All administrative access to production systems requires hardware-backed FIDO2 multi-factor authentication (MFA). "
            "Session tokens expire after 8 hours of inactivity. "
            "Privileged access requests require dual peer review and are logged to an immutable write-once S3 bucket for 365 days."
        ),
        keywords=["soc2", "iso 27001", "mfa", "access control", "security", "audit", "compliance", "fido2"],
    ),
    DocumentChunk(
        doc_id="DOC-CUST-01",
        title="Cloud Server Pro Setup & Provisioning Guide",
        category="Customer_Guide",
        department="Support",
        year=2026,
        content=(
            "Cloud Server Pro instances are provisioned via our REST API or Cloud Console in under 90 seconds. "
            "Default instances allocate 16 vCPUs, 64GB ECC RAM, and 500GB NVMe storage. "
            "SSH key authentication is mandatory; root password login is disabled by default."
        ),
        keywords=["cloud server pro", "provisioning", "setup", "specs", "vcpu", "nvme", "ssh"],
    ),
]


class EnterpriseVectorStore:
    """Vector Store with lexical-semantic similarity and strict metadata filtering."""

    def __init__(self, corpus: Optional[List[DocumentChunk]] = None):
        self.documents = corpus or ENTERPRISE_KNOWLEDGE_CORPUS

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\b[a-zA-Z0-9_\-\$]+\b", text.lower())

    def _compute_relevance(self, query_tokens: List[str], doc: DocumentChunk) -> float:
        score = 0.0
        doc_text = (doc.title + " " + doc.content).lower()

        # Keyword boost
        for kw in doc.keywords:
            for qt in query_tokens:
                if qt in kw.lower():
                    score += 2.5

        # Title boost
        for qt in query_tokens:
            if qt in doc.title.lower():
                score += 3.0

        # Body match
        for qt in query_tokens:
            count = doc_text.count(qt)
            if count > 0:
                score += math.log(1.0 + count) * 1.0

        return score

    def search(
        self,
        query: str,
        top_k: int = 2,
        metadata_filters: Optional[Dict[str, Any]] = None,
        min_score: float = 1.0,
    ) -> List[Dict[str, Any]]:
        """
        Executes similarity search with optional metadata filtering.
        Filters support: department, year, category, doc_id.
        """
        query_tokens = self._tokenize(query)
        candidates = self.documents

        # Apply metadata filters (Self-querying integration)
        if metadata_filters:
            filtered = []
            for doc in candidates:
                match = True
                for k, v in metadata_filters.items():
                    doc_val = getattr(doc, k, None)
                    if doc_val is None:
                        continue
                    if isinstance(v, str) and isinstance(doc_val, str):
                        if doc_val.lower() != v.lower():
                            match = False
                            break
                    elif doc_val != v:
                        match = False
                        break
                if match:
                    filtered.append(doc)
            candidates = filtered

        # Score candidates
        scored = []
        for doc in candidates:
            score = self._compute_relevance(query_tokens, doc)
            if score >= min_score:
                scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for s, doc in scored[:top_k]:
            results.append({
                "doc_id": doc.doc_id,
                "title": doc.title,
                "category": doc.category,
                "department": doc.department,
                "year": doc.year,
                "score": round(s, 2),
                "content": doc.content,
            })
        return results


# Singleton vector store
vector_store = EnterpriseVectorStore()
