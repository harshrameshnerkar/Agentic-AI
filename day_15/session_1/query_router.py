"""
Semantic Query Router & Advanced Runbook Retriever for OpsSentinel Enterprise.
Performs sub-millisecond intent triage, safety guardrailing, and tenant-scoped SOP retrieval.
"""

import re
import math
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field

class RouteCategory(str):
    INFO_SOP = "INFO_SOP"
    DIAGNOSTIC_READ = "DIAGNOSTIC_READ"
    DESTRUCTIVE_WRITE = "DESTRUCTIVE_WRITE"
    ADVERSARIAL_ATTACK = "ADVERSARIAL_ATTACK"
    GENERAL_SRE = "GENERAL_SRE"

class RoutingDecision(BaseModel):
    query: str
    category: str
    confidence: float
    target_service: Optional[str] = None
    action_type: Optional[str] = None
    requires_hitl: bool = False
    is_blocked: bool = False
    rationale: str
    extracted_params: Dict[str, Any] = Field(default_factory=dict)

class RunbookDocument(BaseModel):
    runbook_id: str
    title: str
    service: str
    severity: str
    category: str
    content: str
    remediation_steps: List[str]
    keywords: List[str]

# Pre-loaded Enterprise SRE Runbook Repository
ENTERPRISE_RUNBOOKS: List[RunbookDocument] = [
    RunbookDocument(
        runbook_id="SOP-AUTH-001",
        title="Auth Service Token Validation Degradation & Outage",
        service="auth-service",
        severity="P1",
        category="AUTHENTICATION",
        content="When auth-service latency exceeds 500ms or 5xx error rate spikes > 2%, inspect Redis token cache and DB connection pools. Do not restart without confirming replica health.",
        remediation_steps=[
            "Execute fetch_service_metrics for auth-service",
            "Execute fetch_cluster_logs with severity ERROR",
            "If Redis pool exhausted, trigger clear_cache (Tier 2)",
            "If unresponsive, request human authorization to restart_service (Tier 3)"
        ],
        keywords=["auth", "authentication", "token", "jwt", "session", "500", "redis", "login"]
    ),
    RunbookDocument(
        runbook_id="SOP-PAY-002",
        title="Payment Gateway Stripe/Adyen Webhook Timeout",
        service="payment-api",
        severity="P0",
        category="BILLING",
        content="Payment webhook queues backing up due to downstream TLS handshake slowdowns. Inspect egress network throughput and circuit breaker states.",
        remediation_steps=[
            "Check endpoint health for payment-api and stripe-connector",
            "Fetch telemetry metrics for throughput and p95 latency",
            "If circuit breaker half-open, throttle ingress traffic",
            "If persistent deadlocks, request rollback_deployment (Tier 3)"
        ],
        keywords=["payment", "stripe", "adyen", "checkout", "webhook", "billing", "card"]
    ),
    RunbookDocument(
        runbook_id="SOP-ORDER-003",
        title="Order Processing Service High Memory & OOM Kills",
        service="order-service",
        severity="P2",
        category="COMMERCE",
        content="Order microservice encountering JVM / heap memory exhaustion under flash sale load. Pods entering CrashLoopBackOff.",
        remediation_steps=[
            "Fetch cluster logs for OOMKilled events",
            "Check pod status across cluster nodes",
            "Scale replica count from 4 to 8 via scale_deployment with SRE approval",
            "Capture memory dump for postmortem analysis"
        ],
        keywords=["order", "checkout", "cart", "oom", "memory", "crashloop", "scale", "heap"]
    ),
    RunbookDocument(
        runbook_id="SOP-SEC-004",
        title="SSL / TLS Certificate Rotation & Mutual TLS Ingress",
        service="ingress-gateway",
        severity="P2",
        category="SECURITY",
        content="Standard procedure for updating ingress wildcard certificates and renewing Let's Encrypt / Vault automated rotation secrets.",
        remediation_steps=[
            "Verify current certificate expiry date via check_endpoint_health",
            "Rotate secret in Vault staging namespace",
            "Perform zero-downtime Envoy gateway config reload"
        ],
        keywords=["ssl", "tls", "certificate", "ingress", "cert", "vault", "https", "expiry"]
    ),
    RunbookDocument(
        runbook_id="SOP-DB-005",
        title="PostgreSQL Primary Connection Pool Starvation",
        service="db-primary",
        severity="P1",
        category="DATABASE",
        content="Database connection count approaching max_connections (500). Idle-in-transaction queries blocking schema locks.",
        remediation_steps=[
            "Execute fetch_service_metrics for db-primary",
            "Identify longest running locks and blocked queries",
            "Request human approval to execute drop_stale_connections (Tier 3)",
            "Engage DBA on-call if replication lag exceeds 30s"
        ],
        keywords=["database", "postgres", "db", "sql", "pool", "connections", "idle", "lock", "starvation"]
    ),
]

class QueryRouter:
    """Sub-millisecond intent router with regex guardrailing and semantic triage."""

    ADVERSARIAL_PATTERNS = [
        r"(?i)(ignore (all )?previous instructions|disregard system prompt)",
        r"(?i)(drop table|rm -rf|truncate database|format disk)",
        r"(?i)(give me (the )?admin (password|token|secret|key))",
        r"(?i)(reveal (the )?system prompt|bypass (the )?guardrail)",
        r"(?i)(you are now in DAN mode|act as an unrestricted AI)",
    ]

    DESTRUCTIVE_PATTERNS = [
        r"(?i)\b(restart|reboot|bounce)\b.*?\b(pod|service|deployment|container|node)\b",
        r"(?i)\b(rollback|revert)\b.*?\b(deployment|release|version|commit)\b",
        r"(?i)\b(scale|resize)\b.*?\b(deployment|replicas|workload|cluster)\b",
        r"(?i)\b(drop|kill|terminate)\b.*?\b(connections?|processes?|sessions?)\b",
        r"(?i)\b(drain|cordon)\b.*?\b(node|host|server)\b",
    ]

    DIAGNOSTIC_PATTERNS = [
        r"(?i)\b(check|inspect|verify|diagnose|status|health)\b",
        r"(?i)\b(metrics|cpu|memory|latency|throughput|error rate)\b",
        r"(?i)\b(logs|log stream|stacktrace|exceptions?|errors?)\b",
        r"(?i)\b(topology|dependencies|nodes|replicas)\b",
    ]

    KNOWN_SERVICES = ["auth-service", "payment-api", "order-service", "ingress-gateway", "db-primary", "notification-worker"]

    def route_query(self, query: str) -> RoutingDecision:
        cleaned_query = query.strip()

        # 1. Layer 0 Security Triage: Check for adversarial attacks
        for pattern in self.ADVERSARIAL_PATTERNS:
            if re.search(pattern, cleaned_query):
                return RoutingDecision(
                    query=cleaned_query,
                    category=RouteCategory.ADVERSARIAL_ATTACK,
                    confidence=0.99,
                    requires_hitl=False,
                    is_blocked=True,
                    rationale=f"Security guardrail triggered by adversarial pattern: '{pattern}'",
                )

        # Extract target service if referenced
        detected_service = None
        for svc in self.KNOWN_SERVICES:
            if svc in cleaned_query.lower() or svc.replace("-", " ") in cleaned_query.lower():
                detected_service = svc
                break
        if not detected_service:
            # Check generic words
            if "auth" in cleaned_query.lower():
                detected_service = "auth-service"
            elif "payment" in cleaned_query.lower():
                detected_service = "payment-api"
            elif "order" in cleaned_query.lower():
                detected_service = "order-service"
            elif "db" in cleaned_query.lower() or "database" in cleaned_query.lower():
                detected_service = "db-primary"
            elif "ingress" in cleaned_query.lower() or "gateway" in cleaned_query.lower():
                detected_service = "ingress-gateway"

        # 2. Check for Destructive Remediation (Tier 3 - HITL Required)
        for pattern in self.DESTRUCTIVE_PATTERNS:
            if re.search(pattern, cleaned_query):
                action_name = "remediation_action"
                if "restart" in cleaned_query.lower():
                    action_name = "restart_service"
                elif "rollback" in cleaned_query.lower():
                    action_name = "rollback_deployment"
                elif "scale" in cleaned_query.lower():
                    action_name = "scale_deployment"
                elif "drop" in cleaned_query.lower() or "kill" in cleaned_query.lower():
                    action_name = "drop_stale_connections"

                return RoutingDecision(
                    query=cleaned_query,
                    category=RouteCategory.DESTRUCTIVE_WRITE,
                    confidence=0.95,
                    target_service=detected_service or "unknown-service",
                    action_type=action_name,
                    requires_hitl=True,
                    is_blocked=False,
                    rationale=f"Destructive action detected ({action_name}) affecting {detected_service}. Human SRE approval mandatory.",
                    extracted_params={"service": detected_service, "action": action_name}
                )

        # 3. Check for Diagnostic Read Queries
        for pattern in self.DIAGNOSTIC_PATTERNS:
            if re.search(pattern, cleaned_query):
                return RoutingDecision(
                    query=cleaned_query,
                    category=RouteCategory.DIAGNOSTIC_READ,
                    confidence=0.92,
                    target_service=detected_service,
                    action_type="parallel_diagnostic",
                    requires_hitl=False,
                    is_blocked=False,
                    rationale=f"Diagnostic inspection query for {detected_service or 'infrastructure'}. Dispatching read tools.",
                    extracted_params={"service": detected_service}
                )

        # 4. Check for SOP / Runbook informational query
        if any(w in cleaned_query.lower() for w in ["how to", "procedure", "runbook", "sop", "steps", "guide", "protocol", "policy"]):
            return RoutingDecision(
                query=cleaned_query,
                category=RouteCategory.INFO_SOP,
                confidence=0.90,
                target_service=detected_service,
                action_type="runbook_retrieval",
                requires_hitl=False,
                is_blocked=False,
                rationale="Informational inquiry matched to standard operating runbook procedure.",
                extracted_params={"service": detected_service}
            )

        # 5. Default General SRE
        return RoutingDecision(
            query=cleaned_query,
            category=RouteCategory.GENERAL_SRE,
            confidence=0.75,
            target_service=detected_service,
            action_type="general_investigation",
            requires_hitl=False,
            is_blocked=False,
            rationale="General SRE query routed to multi-stage investigation pipeline.",
            extracted_params={"service": detected_service}
        )

class AdvancedRunbookRetriever:
    """Hierarchical hybrid retriever with keyword token scoring and metadata filtering."""

    def __init__(self, runbooks: Optional[List[RunbookDocument]] = None):
        self.runbooks = runbooks or ENTERPRISE_RUNBOOKS

    def search(
        self,
        query: str,
        service_filter: Optional[str] = None,
        min_score: float = 0.15,
        top_k: int = 3
    ) -> List[Tuple[RunbookDocument, float]]:
        query_tokens = set(re.findall(r"\w+", query.lower()))
        scored_results: List[Tuple[RunbookDocument, float]] = []

        for rb in self.runbooks:
            # Metadata filter
            if service_filter and rb.service != service_filter:
                continue

            # Calculate token overlap & keyword matching
            keyword_score = 0.0
            for kw in rb.keywords:
                if kw in query_tokens:
                    keyword_score += 1.5
                elif any(kw in q for q in query_tokens):
                    keyword_score += 0.5

            content_tokens = set(re.findall(r"\w+", rb.content.lower()))
            overlap = len(query_tokens.intersection(content_tokens))
            content_score = overlap * 0.2

            # Title weight
            title_tokens = set(re.findall(r"\w+", rb.title.lower()))
            title_score = len(query_tokens.intersection(title_tokens)) * 0.8

            raw_score = keyword_score + content_score + title_score
            normalized_score = min(1.0, raw_score / (len(query_tokens) + 1.0))

            if normalized_score >= min_score:
                scored_results.append((rb, round(normalized_score, 4)))

        # Sort descending by score
        scored_results.sort(key=lambda x: x[1], reverse=True)
        return scored_results[:top_k]
