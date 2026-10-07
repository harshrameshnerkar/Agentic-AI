"""
Day 6 - Session 3: Multi-Step Tool Use
Module: schemas.py

Defines OpenAI-compliant JSON schemas and Pydantic validation models
for the 4-step incident resolution tool chain.
"""

from __future__ import annotations
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class LookupIncidentTicketArgs(BaseModel):
    ticket_id: str = Field(
        ...,
        description="The unique incident ticket identifier, e.g., 'INC-8042'."
    )


class FetchServicePolicyArgs(BaseModel):
    tier: str = Field(
        ...,
        description="The SLA customer tier discovered from incident lookup, e.g., 'Enterprise Platinum' or 'Enterprise Gold'."
    )
    service: str = Field(
        ...,
        description="The impacted service name discovered from incident lookup, e.g., 'Cloud Storage Gateway'."
    )


class ComputeFinancialAdjustmentArgs(BaseModel):
    downtime_minutes: int = Field(
        ...,
        ge=0,
        description="Total duration of service disruption in minutes from incident ticket."
    )
    sla_threshold_mins: int = Field(
        ...,
        ge=0,
        description="Allowable downtime threshold before penalty begins, from service policy."
    )
    rate_per_min: float = Field(
        ...,
        gt=0.0,
        description="Agreed penalty dollar credit per minute of excess downtime, from service policy."
    )
    max_cap: float = Field(
        ...,
        gt=0.0,
        description="Contractual maximum allowable penalty credit cap in USD, from service policy."
    )


class RecordCreditMemoArgs(BaseModel):
    idempotency_key: str = Field(
        ...,
        description="Unique deterministic key to prevent duplicate financial credits on retries, e.g., 'IDEM-INC-8042-CUST-901'."
    )
    customer_id: str = Field(
        ...,
        description="The customer account identifier, e.g., 'CUST-901'."
    )
    ticket_id: str = Field(
        ...,
        description="The incident ticket ID associated with this credit memo, e.g., 'INC-8042'."
    )
    net_credit_usd: float = Field(
        ...,
        gt=0.0,
        description="The audited net approved penalty credit amount computed by compute_financial_adjustment."
    )
    manager_email: str = Field(
        ...,
        description="The designated customer manager or billing recipient email."
    )


def get_incident_resolution_tools() -> List[Dict[str, Any]]:
    """
    Returns the 4 sequential tools in OpenAI schema format with model-facing guidance.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "lookup_incident_ticket",
                "description": (
                    "Step 1 in incident remediation. Retrieves customer account profile, SLA tier, "
                    "affected service, downtime minutes, and incident severity from internal database. "
                    "Must be called first to discover the customer tier and service name."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticket_id": {
                            "type": "string",
                            "description": "Unique incident ticket ID, e.g., 'INC-8042'."
                        }
                    },
                    "required": ["ticket_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "fetch_service_policy",
                "description": (
                    "Step 2 in incident remediation. Queries live SLA policy rules for a specific tier "
                    "and service. Returns SLA grace threshold in minutes, penalty rate per minute, and maximum credit cap. "
                    "Call this after retrieving customer SLA tier and service from lookup_incident_ticket."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tier": {
                            "type": "string",
                            "description": "Customer SLA tier, e.g., 'Enterprise Platinum'."
                        },
                        "service": {
                            "type": "string",
                            "description": "Impacted service name, e.g., 'Cloud Storage Gateway'."
                        }
                    },
                    "required": ["tier", "service"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "compute_financial_adjustment",
                "description": (
                    "Step 3 in incident remediation. Computes exact mathematical penalty credits with audit hash. "
                    "Takes downtime minutes, SLA grace threshold, penalty rate per min, and max cap. "
                    "Always use this tool rather than performing mental arithmetic to guarantee compliance."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "downtime_minutes": {
                            "type": "integer",
                            "description": "Total disruption minutes from incident record."
                        },
                        "sla_threshold_mins": {
                            "type": "integer",
                            "description": "Grace minutes before penalty kicks in, from policy."
                        },
                        "rate_per_min": {
                            "type": "number",
                            "description": "Dollar penalty per excess minute, from policy."
                        },
                        "max_cap": {
                            "type": "number",
                            "description": "Maximum contractual cap in USD, from policy."
                        }
                    },
                    "required": ["downtime_minutes", "sla_threshold_mins", "rate_per_min", "max_cap"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "record_credit_memo",
                "description": (
                    "Step 4 in incident remediation. Persists financial credit memo to customer ledger and updates balance. "
                    "CRITICAL: Requires an 'idempotency_key' (e.g. 'IDEM-INC-8042-CUST-901'). If the call is retried or replayed, "
                    "the idempotency key guarantees the customer will NOT be credited twice."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "idempotency_key": {
                            "type": "string",
                            "description": "Deterministic unique idempotency key, e.g. 'IDEM-INC-8042-CUST-901'."
                        },
                        "customer_id": {
                            "type": "string",
                            "description": "Customer ID, e.g. 'CUST-901'."
                        },
                        "ticket_id": {
                            "type": "string",
                            "description": "Incident ticket ID, e.g. 'INC-8042'."
                        },
                        "net_credit_usd": {
                            "type": "number",
                            "description": "Net approved credit calculated in Step 3."
                        },
                        "manager_email": {
                            "type": "string",
                            "description": "Account manager or billing email from incident record."
                        }
                    },
                    "required": ["idempotency_key", "customer_id", "ticket_id", "net_credit_usd", "manager_email"]
                }
            }
        }
    ]
