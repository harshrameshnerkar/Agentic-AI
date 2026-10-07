"""
Day 7 - Session 3: Memory
Module: tools.py

Defines tools for:
1. save_user_preference: Explicitly saves long-term user preferences to persistent storage.
2. get_cluster_metrics: Simulates system performance telemetry to test user formatting preferences.
"""

from __future__ import annotations
import json
from typing import Any, Dict
from pathlib import Path

# Tool Schemas for the OpenAI-compatible endpoint
MEMORY_AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "save_user_preference",
            "description": (
                "Saves a user preference or constraint into persistent long-term memory across sessions. "
                "Call this whenever the user expresses a rule, preference, role, or preferred format."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Short descriptive preference key, e.g. 'output_format', 'latency_unit', 'timezone', 'role'"
                    },
                    "value": {
                        "type": "string",
                        "description": "The exact preference value, e.g. 'concise bullet points', 'milliseconds', 'UTC'"
                    },
                    "category": {
                        "type": "string",
                        "description": "Category: 'formatting', 'technical', 'identity', or 'general'"
                    }
                },
                "required": ["key", "value"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_cluster_metrics",
            "description": "Retrieves live cluster telemetry and operational performance metrics for a named service.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "description": "Name of service to inspect, e.g. 'Storage Gateway' or 'API Gateway'"
                    }
                },
                "required": ["service_name"]
            }
        }
    }
]


def execute_get_cluster_metrics(service_name: str) -> Dict[str, Any]:
    """Simulates realistic cluster health and telemetry."""
    clean = service_name.lower()
    return {
        "service": service_name,
        "status": "HEALTHY",
        "active_instances": 8,
        "cpu_utilization_pct": 38.5,
        "memory_utilization_pct": 52.1,
        "p95_latency_raw_seconds": 0.042,
        "p99_latency_raw_seconds": 0.089,
        "timestamp_raw_iso": "2026-10-05T19:10:00Z",
        "uptime_days": 42
    }
