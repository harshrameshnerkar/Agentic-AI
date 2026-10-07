"""
Operational Tools Subsystem for Capstone OpsSentinel AI.
Defines:
1. Safe Read-Only Diagnostic Tools (Telemetry DB, System Logs, Arithmetic Engine, Runbook Search).
2. Privileged Destructive Action Tools (Service Restart, Deployment Rollback, Emergency Alert).
3. Tool schemas adhering to the function calling standard.
"""

from typing import Any, Dict, List, Optional
from rag_engine import RAGEngine

# Initialize global RAG instance for tool use
_rag_engine = RAGEngine()

# Mock telemetry and operational databases
TELEMETRY_DB = {
    "services": [
        {"service_id": "SVC-PAYMENT", "name": "payment-api", "status": "Degraded", "replicas": 4, "error_rate": "3.8%", "version": "v2.4.1"},
        {"service_id": "SVC-AUTH", "name": "auth-service", "status": "Healthy", "replicas": 6, "error_rate": "0.02%", "version": "v1.9.0"},
        {"service_id": "SVC-INGRESS", "name": "nginx-ingress", "status": "Degraded", "replicas": 8, "error_rate": "4.2%", "version": "v1.8.2"},
        {"service_id": "SVC-DB-POSTGRES", "name": "postgres-primary", "status": "Warning", "connections": 488, "max_connections": 500, "version": "15.4"},
        {"service_id": "SVC-REDIS", "name": "redis-shard-01", "status": "Healthy", "memory_usage": "72%", "maxmemory": "32GB", "version": "7.0"},
    ],
    "incidents": [
        {"ticket_id": "INC-801", "severity": "Sev-1", "title": "Payment gateway latency spike > 35s", "status": "Open", "assigned_to": "alice@ops.internal"},
        {"ticket_id": "INC-802", "severity": "Sev-2", "title": "Postgres connection pool nearing 98% saturation", "status": "Investigating", "assigned_to": "bob@sre.internal"},
        {"ticket_id": "INC-803", "severity": "Sev-3", "title": "Canary build v2.4.1 showing elevated 5xx rate", "status": "Open", "assigned_to": "charlie@devops.internal"},
        {"ticket_id": "INC-804", "severity": "Sev-4", "title": "Routine SSL certificate renewal notice", "status": "Resolved", "assigned_to": "security-bot"},
    ],
    "clusters": [
        {"cluster_id": "K8S-PROD-US-EAST", "nodes": 24, "cpu_alloc": "84%", "memory_alloc": "89%", "region": "us-east-1"},
        {"cluster_id": "K8S-PROD-EU-WEST", "nodes": 18, "cpu_alloc": "61%", "memory_alloc": "64%", "region": "eu-west-1"},
    ],
}

VIRTUAL_FILESYSTEM = {
    "/var/log/k8s/ingress.log": (
        "2026-10-06T06:10:01Z [WARN] upstream server temporarily disabled while connecting\n"
        "2026-10-06T06:12:44Z [ERROR] 104: Connection reset by peer while reading response header from upstream\n"
        "2026-10-06T06:14:12Z [ERROR] upstream timed out (110: Connection timed out) while reading response from payment-api:8080\n"
        "2026-10-06T06:15:30Z [INFO] Active ingress connections: 4230, upstream 504 count: 182"
    ),
    "/var/log/postgres.log": (
        "2026-10-06T06:05:00Z [LOG] checkpoint starting: time\n"
        "2026-10-06T06:11:18Z [FATAL] remaining connection slots are reserved for non-replication superuser connections\n"
        "2026-10-06T06:12:00Z [WARNING] pgbouncer client queue length > 120, wait time > 32000ms\n"
        "2026-10-06T06:14:55Z [LOG] statement: SELECT pg_terminate_backend(pid) executed by admin"
    ),
    "/var/log/auth.log": (
        "2026-10-06T05:00:10Z [INFO] Accepted publickey for deploy-user from 10.0.1.42 port 52310\n"
        "2026-10-06T05:30:22Z [WARN] Failed password for root from 192.168.1.100 port 39122\n"
        "2026-10-06T05:30:24Z [ALERT] PAM 2 more authentication failures; logname= uid=0 euid=0 tty=ssh"
    ),
}


# ===========================================================================
# 1. READ-ONLY SAFE TOOL IMPLEMENTATIONS
# ===========================================================================

def tool_query_telemetry_db(table: str, filter_column: Optional[str] = None, filter_value: Optional[str] = None) -> Dict[str, Any]:
    """Queries telemetry database tables: 'services', 'incidents', 'clusters'."""
    tbl = table.lower().strip()
    if tbl not in TELEMETRY_DB:
        return {"status": "ERROR", "error": f"Table '{table}' not found in telemetry database."}

    rows = TELEMETRY_DB[tbl]
    if filter_column and filter_value:
        filtered = [
            r for r in rows
            if str(r.get(filter_column, "")).lower() == str(filter_value).lower()
        ]
        return {"status": "SUCCESS", "table": tbl, "count": len(filtered), "data": filtered}

    return {"status": "SUCCESS", "table": tbl, "count": len(rows), "data": rows}


def tool_read_system_logs(path: str, max_lines: int = 10) -> Dict[str, Any]:
    """Reads system and container log files from filesystem."""
    p = path.strip()
    if p in VIRTUAL_FILESYSTEM:
        lines = VIRTUAL_FILESYSTEM[p].strip().split("\n")
        return {
            "status": "SUCCESS",
            "filepath": p,
            "total_lines": len(lines),
            "content": "\n".join(lines[:max_lines]),
        }
    return {"status": "ERROR", "error": f"Log file '{path}' not found or inaccessible."}


def tool_calculate_metrics(expression: str) -> Dict[str, Any]:
    """Performs arithmetic computations for SLA, error rates, and operational percentages."""
    clean = expression.replace("%", "/100").replace(",", "").replace("$", "")
    try:
        val = eval(clean, {"__builtins__": None}, {})
        return {"status": "SUCCESS", "expression": expression, "result": round(float(val), 4)}
    except Exception as e:
        return {"status": "ERROR", "error": f"Invalid arithmetic expression: {str(e)}"}


def tool_search_runbooks(query: str, top_k: int = 2) -> Dict[str, Any]:
    """Searches corporate technical SOPs, runbooks, and disaster recovery playbooks."""
    matches = _rag_engine.search(query, top_k=top_k)
    return {"status": "SUCCESS", "query": query, "matches_count": len(matches), "results": matches}


# ===========================================================================
# 2. PRIVILEGED / DESTRUCTIVE ACTION TOOLS (BLAST RADIUS CONTROLLED)
# ===========================================================================

def tool_restart_service(service_name: str, approval_token: str, reason: str) -> Dict[str, Any]:
    """
    Privileged tool: Restarts microservice pods.
    Requires valid approval token and operational justification.
    """
    if approval_token != "AUTH-OPS-APPROVE-2026":
        return {
            "status": "PERMISSION_DENIED",
            "error": "Destructive action blocked: Invalid or missing approval token for service restart.",
            "service": service_name,
        }
    return {
        "status": "SUCCESS",
        "action": "restart_service",
        "service": service_name,
        "message": f"Service '{service_name}' rolling restart dispatched successfully. Grace period: 30s.",
        "reason": reason,
    }


def tool_rollback_deployment(service_name: str, target_version: str, approval_token: str) -> Dict[str, Any]:
    """
    Privileged tool: Rolls back canary or production deployment to previous stable version.
    Requires valid approval token.
    """
    if approval_token != "AUTH-OPS-APPROVE-2026":
        return {
            "status": "PERMISSION_DENIED",
            "error": "Destructive action blocked: Rollback requires authenticated Admin approval token.",
            "service": service_name,
        }
    return {
        "status": "SUCCESS",
        "action": "rollback_deployment",
        "service": service_name,
        "target_version": target_version,
        "message": f"Deployment for '{service_name}' successfully rolled back to target version '{target_version}'. Active connections draining over 45s.",
    }


def tool_dispatch_emergency_alert(severity: str, channel: str, message: str) -> Dict[str, Any]:
    """Broadcasts Sev-1 or Sev-2 incident alert to Slack / PagerDuty war room."""
    return {
        "status": "SUCCESS",
        "action": "dispatch_emergency_alert",
        "severity": severity.upper(),
        "channel": channel,
        "message": message,
        "broadcast_status": "DELIVERED_TO_ONCALL",
    }


# ===========================================================================
# 3. CAPSTONE TOOL SCHEMAS FOR FUNCTION CALLING
# ===========================================================================

CAPSTONE_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "query_telemetry_db",
            "description": "Query operational telemetry tables: 'services', 'incidents', or 'clusters'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "table": {"type": "string", "enum": ["services", "incidents", "clusters"]},
                    "filter_column": {"type": "string", "description": "Optional column name to filter on"},
                    "filter_value": {"type": "string", "description": "Value to match for the filter column"},
                },
                "required": ["table"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_system_logs",
            "description": "Read container and host log files (e.g., /var/log/k8s/ingress.log, /var/log/postgres.log).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute filesystem path to log file"},
                    "max_lines": {"type": "integer", "description": "Maximum lines to read (default 10)"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_metrics",
            "description": "Evaluate arithmetic expressions for SLAs, error percentages, and latency metrics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Mathematical formula to evaluate"},
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_runbooks",
            "description": "Search corporate SOP runbooks and disaster recovery playbooks for technical procedures.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Technical search query"},
                    "top_k": {"type": "integer", "description": "Number of results to return (default 2)"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "restart_service",
            "description": "Privileged destructive tool to trigger rolling restart of a microservice. Requires approval token.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_name": {"type": "string", "description": "Name of microservice to restart"},
                    "approval_token": {"type": "string", "description": "Mandatory security approval token"},
                    "reason": {"type": "string", "description": "Operational reason for restart"},
                },
                "required": ["service_name", "approval_token", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rollback_deployment",
            "description": "Privileged destructive tool to roll back service deployment to previous image tag. Requires approval token.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_name": {"type": "string", "description": "Name of service to rollback"},
                    "target_version": {"type": "string", "description": "Stable target image version (e.g. v2.4.0)"},
                    "approval_token": {"type": "string", "description": "Mandatory security approval token"},
                },
                "required": ["service_name", "target_version", "approval_token"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "dispatch_emergency_alert",
            "description": "Dispatch incident alert to PagerDuty or Slack channel for on-call war room notification.",
            "parameters": {
                "type": "object",
                "properties": {
                    "severity": {"type": "string", "enum": ["Sev-1", "Sev-2", "Sev-3", "Sev-4"]},
                    "channel": {"type": "string", "description": "Destination channel or room"},
                    "message": {"type": "string", "description": "Incident alert summary"},
                },
                "required": ["severity", "channel", "message"],
            },
        },
    },
]
