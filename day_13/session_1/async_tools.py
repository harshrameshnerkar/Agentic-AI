"""
Day 13 - Session 1: Async Capstone Operational Tools
====================================================
Implements:
  1. Synchronous and Asynchronous tool variants for Capstone SRE Copilot
  2. Realistic enterprise I/O latency simulation (Telemetry DB, Vector Search, Cloud Logs)
  3. Safe diagnostic tools and privileged remediation tools
"""

import asyncio
import time
from typing import Dict, List, Any, Optional

# Shared Mock Telemetry and Operational Databases
MOCK_TELEMETRY_DB = {
    "services": [
        {"service_id": "SVC-PAYMENT", "name": "payment-api", "status": "Degraded", "replicas": 4, "error_rate": "4.2%", "latency_p99_ms": 1820},
        {"service_id": "SVC-AUTH", "name": "auth-service", "status": "Healthy", "replicas": 6, "error_rate": "0.01%", "latency_p99_ms": 42},
        {"service_id": "SVC-INGRESS", "name": "nginx-ingress", "status": "Degraded", "replicas": 8, "error_rate": "3.9%", "latency_p99_ms": 940},
        {"service_id": "SVC-POSTGRES", "name": "postgres-primary", "status": "Warning", "connections": 492, "max_connections": 500, "latency_p99_ms": 1150},
        {"service_id": "SVC-REDIS", "name": "redis-shard-01", "status": "Healthy", "memory_usage": "74%", "maxmemory": "32GB", "latency_p99_ms": 5},
    ],
    "incidents": [
        {"ticket_id": "INC-901", "severity": "Sev-1", "title": "Payment gateway latency breach (> 1500ms)", "status": "Open", "service": "payment-api"},
        {"ticket_id": "INC-902", "severity": "Sev-2", "title": "Postgres connection pool nearing 98% saturation", "status": "Investigating", "service": "postgres-primary"},
        {"ticket_id": "INC-903", "severity": "Sev-3", "title": "Nginx 504 Gateway Timeout spike", "status": "Open", "service": "nginx-ingress"},
    ],
}

MOCK_SYSTEM_LOGS = {
    "/var/log/payment-api.log": (
        "2026-10-07T08:00:12Z [ERROR] Failed to acquire connection from pool: timeout 30000ms\n"
        "2026-10-07T08:00:15Z [WARN] Circuit breaker state transitioned to HALF-OPEN for upstream postgres-primary\n"
        "2026-10-07T08:00:22Z [FATAL] Client HTTP 500 response threshold exceeded (> 4.0% error rate)\n"
        "2026-10-07T08:00:30Z [INFO] Active worker threads: 128/128 (pool saturated)"
    ),
    "/var/log/postgres.log": (
        "2026-10-07T07:58:00Z [LOG] connection received: host=10.0.4.12 port=49120\n"
        "2026-10-07T07:59:44Z [FATAL] remaining connection slots are reserved for non-replication superuser connections\n"
        "2026-10-07T08:00:01Z [WARNING] pgbouncer client waiting queue length > 140, max_wait_ms > 35000\n"
        "2026-10-07T08:00:10Z [LOG] idle in transaction session count: 184"
    ),
    "/var/log/nginx-ingress.log": (
        "2026-10-07T07:59:12Z [WARN] upstream payment-api:8080 temporarily marked as unhealthy\n"
        "2026-10-07T08:00:04Z [ERROR] 110: Connection timed out while reading response header from upstream\n"
        "2026-10-07T08:00:18Z [ERROR] HTTP 504 Gateway Time-out emitted to client 198.51.100.24"
    ),
}

MOCK_RUNBOOKS = {
    "RUNBOOK-01": {
        "title": "Postgres Connection Pool Exhaustion & PgBouncer Remediation",
        "category": "DATABASE",
        "steps": ["Query telemetry database for active connections", "Inspect postgres logs for idle transactions", "Restart pgbouncer or drain stale connections", "Notify DBA channel"],
        "safe": False,
        "requires_approval": True,
    },
    "RUNBOOK-02": {
        "title": "Payment API Gateway Timeout & Latency Spike",
        "category": "APPLICATION",
        "steps": ["Read payment-api container logs", "Check upstream database latency", "Scale replicas or perform rolling restart", "Notify on-call payment lead"],
        "safe": False,
        "requires_approval": True,
    },
    "RUNBOOK-03": {
        "title": "Nginx Ingress 504 Gateway Timeout Investigation",
        "category": "NETWORK_INGRESS",
        "steps": ["Inspect ingress access and error logs", "Verify backend pod endpoint readiness", "Restart ingress proxy pods"],
        "safe": True,
        "requires_approval": False,
    },
}


# =====================================================================
# 1. SYNCHRONOUS TOOLS (For Baseline Sequential Execution)
# =====================================================================

def sync_query_telemetry_db(table: str, filter_service: Optional[str] = None) -> Dict[str, Any]:
    """Synchronously queries telemetry database. Simulates 120ms network I/O."""
    time.sleep(0.12)
    tbl = table.lower().strip()
    if tbl not in MOCK_TELEMETRY_DB:
        return {"status": "ERROR", "error": f"Table '{table}' not found in telemetry DB."}
    data = MOCK_TELEMETRY_DB[tbl]
    if filter_service:
        data = [r for r in data if r.get("name") == filter_service or r.get("service") == filter_service]
    return {"status": "SUCCESS", "tool": "query_telemetry_db", "data": data, "latency_ms": 120.0}


def sync_read_system_logs(path: str, max_lines: int = 5) -> Dict[str, Any]:
    """Synchronously reads container logs. Simulates 150ms remote disk I/O."""
    time.sleep(0.15)
    p = path.strip()
    if p in MOCK_SYSTEM_LOGS:
        lines = MOCK_SYSTEM_LOGS[p].strip().split("\n")[:max_lines]
        return {"status": "SUCCESS", "tool": "read_system_logs", "path": p, "content": "\n".join(lines), "latency_ms": 150.0}
    return {"status": "ERROR", "error": f"Log path '{path}' not found.", "latency_ms": 150.0}


def sync_search_runbooks(query: str) -> Dict[str, Any]:
    """Synchronously performs vector semantic search across runbooks. Simulates 180ms vector DB I/O."""
    time.sleep(0.18)
    q_lower = query.lower()
    matches = []
    for r_id, rb in MOCK_RUNBOOKS.items():
        if any(w in rb["title"].lower() or w in rb["category"].lower() for w in q_lower.split()):
            matches.append({"runbook_id": r_id, **rb})
    if not matches:
        matches = [{"runbook_id": "RUNBOOK-01", **MOCK_RUNBOOKS["RUNBOOK-01"]}]
    return {"status": "SUCCESS", "tool": "search_runbooks", "matches": matches, "latency_ms": 180.0}


def sync_calculate_metrics(expression: str) -> Dict[str, Any]:
    """Synchronously computes operational SLA metrics. Simulates 25ms CPU/async time."""
    time.sleep(0.025)
    clean = expression.replace("%", "/100").replace(",", "").replace("$", "")
    try:
        val = eval(clean, {"__builtins__": None}, {})
        return {"status": "SUCCESS", "tool": "calculate_metrics", "result": round(float(val), 4), "latency_ms": 25.0}
    except Exception as e:
        return {"status": "ERROR", "error": str(e), "latency_ms": 25.0}


def sync_restart_service(service: str, approval_token: str) -> Dict[str, Any]:
    """Synchronously executes container restart. Simulates 200ms Kubernetes API I/O."""
    time.sleep(0.20)
    if not approval_token.startswith("AUTH-"):
        return {"status": "REJECTED", "error": "Invalid approval token", "latency_ms": 200.0}
    return {"status": "SUCCESS", "tool": "restart_service", "service": service, "latency_ms": 200.0}


# =====================================================================
# 2. ASYNCHRONOUS TOOLS (For Parallel Concurrent Execution)
# =====================================================================

async def async_query_telemetry_db(table: str, filter_service: Optional[str] = None) -> Dict[str, Any]:
    """Asynchronously queries telemetry database. Non-blocking 120ms I/O."""
    await asyncio.sleep(0.12)
    tbl = table.lower().strip()
    if tbl not in MOCK_TELEMETRY_DB:
        return {"status": "ERROR", "error": f"Table '{table}' not found in telemetry DB."}
    data = MOCK_TELEMETRY_DB[tbl]
    if filter_service:
        data = [r for r in data if r.get("name") == filter_service or r.get("service") == filter_service]
    return {"status": "SUCCESS", "tool": "query_telemetry_db", "data": data, "latency_ms": 120.0}


async def async_read_system_logs(path: str, max_lines: int = 5) -> Dict[str, Any]:
    """Asynchronously reads remote container logs. Non-blocking 150ms I/O."""
    await asyncio.sleep(0.15)
    p = path.strip()
    if p in MOCK_SYSTEM_LOGS:
        lines = MOCK_SYSTEM_LOGS[p].strip().split("\n")[:max_lines]
        return {"status": "SUCCESS", "tool": "read_system_logs", "path": p, "content": "\n".join(lines), "latency_ms": 150.0}
    return {"status": "ERROR", "error": f"Log path '{path}' not found.", "latency_ms": 150.0}


async def async_search_runbooks(query: str) -> Dict[str, Any]:
    """Asynchronously queries vector embedding database. Non-blocking 180ms I/O."""
    await asyncio.sleep(0.18)
    q_lower = query.lower()
    matches = []
    for r_id, rb in MOCK_RUNBOOKS.items():
        if any(w in rb["title"].lower() or w in rb["category"].lower() for w in q_lower.split()):
            matches.append({"runbook_id": r_id, **rb})
    if not matches:
        matches = [{"runbook_id": "RUNBOOK-01", **MOCK_RUNBOOKS["RUNBOOK-01"]}]
    return {"status": "SUCCESS", "tool": "search_runbooks", "matches": matches, "latency_ms": 180.0}


async def async_calculate_metrics(expression: str) -> Dict[str, Any]:
    """Asynchronously evaluates metrics. Non-blocking 25ms I/O."""
    await asyncio.sleep(0.025)
    clean = expression.replace("%", "/100").replace(",", "").replace("$", "")
    try:
        val = eval(clean, {"__builtins__": None}, {})
        return {"status": "SUCCESS", "tool": "calculate_metrics", "result": round(float(val), 4), "latency_ms": 25.0}
    except Exception as e:
        return {"status": "ERROR", "error": str(e), "latency_ms": 25.0}


async def async_restart_service(service: str, approval_token: str) -> Dict[str, Any]:
    """Asynchronously restarts container via K8s API. Non-blocking 200ms I/O."""
    await asyncio.sleep(0.20)
    if not approval_token.startswith("AUTH-"):
        return {"status": "REJECTED", "error": "Invalid approval token", "latency_ms": 200.0}
    return {"status": "SUCCESS", "tool": "restart_service", "service": service, "latency_ms": 200.0}


async def async_rollback_deployment(service: str, target_version: str, approval_token: str) -> Dict[str, Any]:
    """Asynchronously triggers GitOps rollback. Non-blocking 250ms I/O."""
    await asyncio.sleep(0.25)
    if not approval_token.startswith("AUTH-"):
        return {"status": "REJECTED", "error": "Invalid approval token", "latency_ms": 250.0}
    return {"status": "SUCCESS", "tool": "rollback_deployment", "service": service, "target_version": target_version, "latency_ms": 250.0}


async def async_dispatch_emergency_alert(channel: str, message: str) -> Dict[str, Any]:
    """Asynchronously dispatches PagerDuty / Slack alerts. Non-blocking 80ms I/O."""
    await asyncio.sleep(0.08)
    return {"status": "SUCCESS", "tool": "dispatch_emergency_alert", "channel": channel, "message": message, "latency_ms": 80.0}
