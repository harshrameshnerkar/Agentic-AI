"""
Tools for Day 8 Session 3 (Context Engineering).
Provides both:
1. Baseline Tools: Raw, unpruned dictionaries and noisy logs (demonstrating context pollution).
2. Context-Engineered Tools: Structured pruning, metric distillation, and Sub-Agent Context Isolation.
"""

import json
from typing import Any, Dict, List
from raw_data import RAW_CONTAINER_LOGS, RAW_INCIDENT_PAYLOAD, RAW_TELEMETRY_SERIES


# ==============================================================================
# 1. BASELINE UNPRUNED TOOLS (Heavy payloads, noisy dumps)
# ==============================================================================

def baseline_get_incident(incident_id: str) -> Dict[str, Any]:
    """Returns raw, complete incident payload with all infrastructure metadata."""
    return RAW_INCIDENT_PAYLOAD


def baseline_get_telemetry(service_name: str) -> List[Dict[str, Any]]:
    """Returns entire raw multi-column telemetry table with 20+ columns per timestamp."""
    return RAW_TELEMETRY_SERIES


def baseline_get_logs(pod_name: str) -> str:
    """Returns raw 40+ line container logs with Netty headers, trace dumps, and stack traces."""
    return RAW_CONTAINER_LOGS


BASELINE_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "baseline_get_incident",
            "description": "Fetch complete raw incident report and cluster infrastructure state.",
            "parameters": {
                "type": "object",
                "properties": {
                    "incident_id": {"type": "string", "description": "The incident ID, e.g. 'INC-8821'"}
                },
                "required": ["incident_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "baseline_get_telemetry",
            "description": "Fetch all multi-metric telemetry samples for the service.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_name": {"type": "string", "description": "Name of service"}
                },
                "required": ["service_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "baseline_get_logs",
            "description": "Fetch raw unpruned stdout/stderr container logs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pod_name": {"type": "string", "description": "Target pod name"}
                },
                "required": ["pod_name"]
            }
        }
    }
]

BASELINE_TOOL_REGISTRY = {
    "baseline_get_incident": baseline_get_incident,
    "baseline_get_telemetry": baseline_get_telemetry,
    "baseline_get_logs": baseline_get_logs,
}


# ==============================================================================
# 2. CONTEXT-ENGINEERED TOOLS (Pruned, High-Entropy, Sub-Agent Isolated)
# ==============================================================================

def optimized_get_incident_summary(incident_id: str) -> Dict[str, Any]:
    """
    Context Engineering Principle: Strip non-actionable infrastructure metadata.
    Drops VPC IDs, CNI versions, security groups, and internal routing tags.
    """
    raw = RAW_INCIDENT_PAYLOAD
    return {
        "incident_id": raw["incident_id"],
        "service": raw["service_name"],
        "severity": raw["severity"],
        "reported_symptom": raw["reported_symptom"],
        "pod_health": f"{raw['active_pods']}/{raw['desired_pods']} active",
    }


def optimized_get_telemetry_anomalies(service_name: str) -> Dict[str, Any]:
    """
    Context Engineering Principle: Pre-filter metrics deterministically.
    Instead of dumping 20 normal columns, returns only metrics breaching 2-sigma thresholds.
    """
    anomalies = []
    for sample in RAW_TELEMETRY_SERIES:
        ts = sample["timestamp"]
        # Check metaspace threshold (>95%)
        metaspace_pct = (sample["metaspace_used_mb"] / sample["metaspace_max_mb"]) * 100
        if metaspace_pct > 95.0:
            anomalies.append({
                "metric": "Metaspace Utilization",
                "value": f"{sample['metaspace_used_mb']}MB / {sample['metaspace_max_mb']}MB ({metaspace_pct:.1f}%)",
                "severity": "CRITICAL_SATURATION",
                "timestamp": ts,
            })
        # Check GC pause (>1000ms)
        if sample["gc_pause_time_ms"] > 1000:
            anomalies.append({
                "metric": "JVM Garbage Collection Pause",
                "value": f"{sample['gc_pause_time_ms']}ms (Stop-The-World pause)",
                "severity": "CRITICAL_FREEZE",
                "timestamp": ts,
            })
        # Check CPU (>80%)
        if sample["cpu_usage_pct"] > 80.0:
            anomalies.append({
                "metric": "CPU Saturation",
                "value": f"{sample['cpu_usage_pct']}%",
                "severity": "HIGH",
                "timestamp": ts,
            })

    return {
        "service": service_name,
        "critical_anomalies": anomalies,
        "normal_metrics_filtered": 16,
    }


def isolated_log_analyzer_subagent(pod_name: str) -> Dict[str, Any]:
    """
    Context Engineering Principle: Sub-Agent Context Isolation.
    Instead of dumping 40+ lines of raw stack traces and Netty byte traces into the main agent context,
    a specialized isolated sub-routine parses the log stream and extracts the single high-entropy root cause.
    """
    # Deterministic log parser isolating the critical root cause
    fatal_lines = []
    culprit_component = "Unknown"
    root_cause = "Unknown"

    for line in RAW_CONTAINER_LOGS.splitlines():
        if "OutOfMemoryError: Metaspace" in line:
            root_cause = "java.lang.OutOfMemoryError: Metaspace"
        if "HotReloadWatcher" in line and ("ERROR" in line or "proxy" in line):
            culprit_component = "HotReloadWatcher (Dynamic ByteBuddy class proxy generation on configmap sync)"

    return {
        "pod": pod_name,
        "root_cause_exception": root_cause,
        "culprit_component": culprit_component,
        "diagnostic_summary": "JVM crashed due to unconstrained class generation in HotReloadWatcher exhausting 256MB Metaspace.",
        "isolated_lines_pruned": len(RAW_CONTAINER_LOGS.splitlines()),
    }


OPTIMIZED_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "optimized_get_incident_summary",
            "description": "Fetch concise, pruned incident summary (service, symptom, pod health).",
            "parameters": {
                "type": "object",
                "properties": {
                    "incident_id": {"type": "string", "description": "The incident ID, e.g. 'INC-8821'"}
                },
                "required": ["incident_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "optimized_get_telemetry_anomalies",
            "description": "Fetch only statistically anomalous metrics (Metaspace, GC freezes, CPU spikes).",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_name": {"type": "string", "description": "Target service"}
                },
                "required": ["service_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "isolated_log_analyzer_subagent",
            "description": "Delegates log parsing to an isolated sub-agent. Returns concise root-cause diagnosis without log dump.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pod_name": {"type": "string", "description": "Target pod name"}
                },
                "required": ["pod_name"]
            }
        }
    }
]

OPTIMIZED_TOOL_REGISTRY = {
    "optimized_get_incident_summary": optimized_get_incident_summary,
    "optimized_get_telemetry_anomalies": optimized_get_telemetry_anomalies,
    "isolated_log_analyzer_subagent": isolated_log_analyzer_subagent,
}
