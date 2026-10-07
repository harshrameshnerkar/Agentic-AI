"""
RAG Engine (Retrieval-Augmented Generation) for Capstone OpsSentinel AI.
Stores technical SOPs, disaster recovery playbooks, and incident runbooks.
Provides keyword and semantic chunk retrieval with relevance scoring and citations.
"""

import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    chunk_id: str
    doc_id: str
    title: str
    category: str
    content: str
    keywords: List[str] = Field(default_factory=list)


OPS_RUNBOOKS: List[Dict[str, Any]] = [
    {
        "doc_id": "RUNBOOK-01",
        "title": "Postgres Database Connection Pool Exhaustion SOP",
        "category": "Database_Reliability",
        "content": (
            "When PostgreSQL connections reach the max pool threshold (max_connections=500), "
            "PGBouncer enters queuing mode. Symptoms include query latency spikes >30s and error 'connection pool exhausted'. "
            "Resolution steps: 1) Identify idle-in-transaction queries via pg_stat_activity. "
            "2) Terminate leaking connections using pg_terminate_backend(pid). "
            "3) Do NOT restart PostgreSQL directly without SRE approval. "
            "4) Scale PgBouncer pool size to 800 if sustained traffic is verified."
        ),
        "keywords": ["postgres", "postgresql", "connection", "pool", "pgbouncer", "database", "exhausted", "latency"],
    },
    {
        "doc_id": "RUNBOOK-02",
        "title": "Kubernetes Ingress 502/504 Gateway Timeout Triage",
        "category": "Kubernetes_Networking",
        "content": (
            "HTTP 502/504 gateway errors occur when NGINX Ingress upstream pods fail to respond within proxy-read-timeout (60s). "
            "Root causes: 1) Upstream container OOMKilled or restarting. 2) CoreDNS resolution degradation. "
            "Diagnosis: Inspect /var/log/k8s/ingress.log for upstream timed out errors. "
            "Remediation: Scale pod deployment replicas by +2, or restart unresponsive backend pods with valid approval token. "
            "Default health probe grace period is 30 seconds."
        ),
        "keywords": ["kubernetes", "ingress", "502", "504", "gateway", "timeout", "nginx", "oomkilled", "pods"],
    },
    {
        "doc_id": "RUNBOOK-03",
        "title": "Redis Cache Cluster Failover & Eviction Playbook",
        "category": "Caching_Infrastructure",
        "content": (
            "Redis cluster nodes employ volatile-lru eviction policy with maxmemory set to 32GB per shard. "
            "If memory consumption exceeds 95%, cluster triggers memory pressure alerts. "
            "Resolution: 1) Flush expired keys using safe active-expire cycle. "
            "2) If cluster failover is needed, verify Sentinel quorum (at least 2 of 3 votes). "
            "3) Destructive action FLUSHDB requires Level-3 Admin approval and temporary maintenance window."
        ),
        "keywords": ["redis", "cache", "cluster", "failover", "eviction", "memory", "sentinel", "flushdb"],
    },
    {
        "doc_id": "RUNBOOK-04",
        "title": "Sev-1 Emergency Incident Escalation Protocol",
        "category": "Incident_Response",
        "content": (
            "Sev-1 (Critical Outage) criteria: Customer-facing degradation affecting >5% of active transactions. "
            "Escalation SLA: Primary On-Call must acknowledge incident within 15 minutes. "
            "Protocol: 1) Automatically open PagerDuty incident and create Slack channel #incident-YYYYMMDD. "
            "2) Assign Incident Commander (IC) and Communications Lead. "
            "3) Post public status update to status.enterprise.io within 20 minutes."
        ),
        "keywords": ["sev-1", "incident", "escalation", "on-call", "pagerduty", "sla", "outage", "emergency"],
    },
    {
        "doc_id": "RUNBOOK-05",
        "title": "Microservice Deployment Rollback & Canary Abort Procedure",
        "category": "Deployment_Operations",
        "content": (
            "If a canary release shows HTTP 5xx error rate >1.5% over a 5-minute rolling window, automatically abort. "
            "Rollback command: Execute rollback_deployment with previous stable image tag (e.g. v2.4.1 -> v2.4.0). "
            "Rollbacks drain active HTTP connections over 45 seconds before terminating pods. "
            "Rollback actions are classified as destructive/high-blast-radius and require Engineer or Admin role."
        ),
        "keywords": ["rollback", "deployment", "canary", "abort", "5xx", "helm", "release", "blast-radius"],
    },
    {
        "doc_id": "RUNBOOK-06",
        "title": "API Gateway Rate Limiting & Quota Management Policy",
        "category": "API_Security",
        "content": (
            "Our API Gateway enforces Token Bucket rate limiting: "
            "Standard API tier is capped at 100 requests/second with burst allowance of 150. "
            "Enterprise tier is capped at 2,000 requests/second with burst allowance of 3,000. "
            "Clients exceeding limits receive HTTP 429 Too Many Requests with Retry-After header. "
            "Exemption requests require Approval from API Architecture Board."
        ),
        "keywords": ["rate", "limit", "quota", "api", "gateway", "429", "standard", "enterprise", "burst"],
    },
]


class RAGEngine:
    """Manages knowledge retrieval over technical runbooks and SOP documents."""

    def __init__(self, runbooks: Optional[List[Dict[str, Any]]] = None):
        raw = runbooks or OPS_RUNBOOKS
        self.chunks: List[DocumentChunk] = []
        for r in raw:
            chunk = DocumentChunk(
                chunk_id=f"{r['doc_id']}-C1",
                doc_id=r["doc_id"],
                title=r["title"],
                category=r["category"],
                content=r["content"],
                keywords=r.get("keywords", []),
            )
            self.chunks.append(chunk)

    def search(self, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """
        Retrieves top-k relevant runbook chunks based on term overlap and keyword relevance.
        Returns ranked list of matching chunks with similarity score and citation.
        """
        words = set(re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", query.lower()))
        stop_words = {"what", "is", "our", "the", "for", "and", "in", "of", "to", "how", "tell", "me", "show", "procedure"}
        query_terms = {w for w in words if w not in stop_words}
        if not query_terms:
            query_terms = words

        scored_chunks = []
        for ch in self.chunks:
            # Score against content words and explicit keywords
            content_words = set(re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", ch.content.lower()))
            kw_set = set(k.lower() for k in ch.keywords)
            title_words = set(re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", ch.title.lower()))

            score = 0.0
            # Term matches in content
            content_overlap = len(query_terms.intersection(content_words))
            score += content_overlap * 1.0

            # Matches in curated keywords (higher weight)
            kw_overlap = len(query_terms.intersection(kw_set))
            score += kw_overlap * 2.5

            # Matches in title (highest weight)
            title_overlap = len(query_terms.intersection(title_words))
            score += title_overlap * 3.0

            if score > 0:
                scored_chunks.append((score, ch))

        # Sort descending by score
        scored_chunks.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, ch in scored_chunks[:top_k]:
            results.append({
                "doc_id": ch.doc_id,
                "title": ch.title,
                "category": ch.category,
                "score": round(score, 2),
                "citation": f"[{ch.doc_id}: {ch.title}]",
                "content": ch.content,
            })
        return results
