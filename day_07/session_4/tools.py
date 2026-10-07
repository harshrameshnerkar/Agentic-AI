"""
Tool registry for Day 7 Session 4 (Reliability & Control).
Includes safe diagnostic tools, an intentionally slow tool for timeout testing,
and a critical side-effecting 'send_email' tool requiring mandatory human approval.
"""

import time
from typing import Any, Dict


# Mock incident database
INCIDENT_DATABASE = {
    "INC-4091": {
        "incident_id": "INC-4091",
        "title": "Redis Cache Cluster Memory Exhaustion",
        "severity": "P1 - CRITICAL",
        "affected_service": "Checkout-Payment-Gateway",
        "root_cause": "Unbounded cache key TTL in SessionStore service leading to 99.8% RAM saturation.",
        "mitigation_applied": "Manual key eviction completed; memory stabilized at 41%.",
        "status": "MITIGATED",
        "requires_stakeholder_email": True,
    },
    "INC-2044": {
        "incident_id": "INC-2044",
        "title": "Stale Read Replica Lag in US-East",
        "severity": "P3 - MODERATE",
        "affected_service": "Analytics-Pipeline",
        "root_cause": "Network partition between primary DB and read replica.",
        "mitigation_applied": "Replica resynchronized automatically.",
        "status": "RESOLVED",
        "requires_stakeholder_email": False,
    },
}


def read_system_incident(incident_id: str) -> Dict[str, Any]:
    """Retrieves authoritative incident status and root-cause details."""
    incident = INCIDENT_DATABASE.get(incident_id.strip().upper())
    if not incident:
        return {
            "error": "NotFound",
            "message": f"Incident '{incident_id}' not found in registry.",
            "available_incidents": list(INCIDENT_DATABASE.keys()),
        }
    return incident


def slow_diagnostics_service(service_name: str, simulated_delay_seconds: float = 4.0) -> Dict[str, Any]:
    """
    Simulates a heavy, unresponsive remote telemetry probe that hangs for seconds.
    Used to demonstrate strict wall-clock timeout interception and recovery.
    """
    time.sleep(simulated_delay_seconds)
    return {
        "service": service_name,
        "diagnostics": "Deep packet analysis completed after extensive delay.",
        "status": "HEALTHY",
    }


def send_email(to: str, subject: str, body: str) -> Dict[str, Any]:
    """
    High-consequence external action: Dispatches an official email communication.
    CRITICAL: This tool has a real-world side-effect and MUST NEVER execute without
    prior Human-in-the-Loop approval!
    """
    return {
        "status": "EMAIL_DISPATCHED",
        "recipient": to,
        "subject": subject,
        "body_preview": (body[:120] + "...") if len(body) > 120 else body,
        "dispatched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "read_system_incident",
            "description": "Look up official details, severity, status, and root-cause for a production incident ID (e.g. 'INC-4091').",
            "parameters": {
                "type": "object",
                "properties": {
                    "incident_id": {
                        "type": "string",
                        "description": "The incident identifier, e.g. 'INC-4091'.",
                    }
                },
                "required": ["incident_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "slow_diagnostics_service",
            "description": "Trigger a deep infrastructure network probe. Note: This call may hang or take significant time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "description": "Name of the target microservice to inspect.",
                    },
                    "simulated_delay_seconds": {
                        "type": "number",
                        "description": "Number of seconds the remote service hangs before returning (default 4.0s).",
                    },
                },
                "required": ["service_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send an official notification email to stakeholders or engineers. CRITICAL ACTION: Requires human approval before firing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Recipient email address (e.g. 'devops-alerts@company.com').",
                    },
                    "subject": {
                        "type": "string",
                        "description": "Clear subject line for the email.",
                    },
                    "body": {
                        "type": "string",
                        "description": "Complete text body of the email communication.",
                    },
                },
                "required": ["to", "subject", "body"],
            },
        },
    },
]

TOOL_FUNCTIONS = {
    "read_system_incident": read_system_incident,
    "slow_diagnostics_service": slow_diagnostics_service,
    "send_email": send_email,
}
