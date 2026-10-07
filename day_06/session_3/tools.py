"""
Day 6 - Session 3: Multi-Step Tool Use
Module: tools.py

Implements 4 sequential tools that chain data from one step to the next:
1. lookup_incident_ticket: Fetches customer, tier, and downtime from database.
2. fetch_service_policy: Retrieves SLA terms, penalty rate, and cap for that tier/service.
3. compute_financial_adjustment: Performs deterministic financial calculation with audit trail.
4. record_credit_memo: Applies financial adjustment with IDEMPOTENCY KEY protection.
"""

from __future__ import annotations
import sqlite3
import hashlib
import uuid
import datetime
from pathlib import Path
from typing import Any, Dict, Optional

DB_PATH = Path(__file__).resolve().parent / "incident_system.db"


def lookup_incident_ticket(ticket_id: str) -> Dict[str, Any]:
    """
    Retrieves incident ticket details and customer account profile from the database.
    """
    clean_id = (ticket_id or "").strip().upper()
    if not clean_id:
        return {
            "status": "error",
            "error_type": "InvalidInput",
            "message": "ticket_id must not be empty. Example: 'INC-8042'."
        }

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.ticket_id, i.customer_id, c.company_name, c.sla_tier, c.manager_email,
               i.service_name, i.downtime_minutes, i.severity, i.root_cause, i.status
        FROM incidents i
        JOIN customers c ON i.customer_id = c.customer_id
        WHERE i.ticket_id = ?;
    """, (clean_id,))
    row = cursor.fetchone()

    if not row:
        cursor.execute("SELECT ticket_id FROM incidents;")
        available = [r[0] for r in cursor.fetchall()]
        conn.close()
        return {
            "status": "error",
            "error_type": "TicketNotFound",
            "message": f"Incident ticket '{clean_id}' was not found.",
            "available_tickets": available
        }

    conn.close()
    return {
        "status": "success",
        "ticket_id": row[0],
        "customer_id": row[1],
        "company_name": row[2],
        "sla_tier": row[3],
        "manager_email": row[4],
        "service_name": row[5],
        "downtime_minutes": row[6],
        "severity": row[7],
        "root_cause": row[8],
        "incident_status": row[9]
    }


def fetch_service_policy(tier: str, service: str) -> Dict[str, Any]:
    """
    Fetches the live SLA credit policy, threshold, and rates for an account tier and service.
    """
    clean_tier = (tier or "").strip()
    clean_service = (service or "").strip()

    if not clean_tier or not clean_service:
        return {
            "status": "error",
            "error_type": "MissingParameters",
            "message": "Both 'tier' and 'service' are required to resolve SLA policy."
        }

    # Policy database mapping
    policy_catalog = {
        ("Enterprise Platinum", "Cloud Storage Gateway"): {
            "sla_threshold_mins": 60,
            "penalty_rate_per_min_usd": 12.50,
            "max_credit_cap_usd": 2500.00,
            "escalation_contact": "sla-claims@cloudplatform.internal",
            "policy_version": "2026.Q4-v2"
        },
        ("Enterprise Gold", "Realtime Payment Ingress"): {
            "sla_threshold_mins": 30,
            "penalty_rate_per_min_usd": 20.00,
            "max_credit_cap_usd": 3000.00,
            "escalation_contact": "fintech-sla@cloudplatform.internal",
            "policy_version": "2026.Q4-v1"
        },
        ("Standard Business", "Batch Report Dispatcher"): {
            "sla_threshold_mins": 120,
            "penalty_rate_per_min_usd": 5.00,
            "max_credit_cap_usd": 800.00,
            "escalation_contact": "support@cloudplatform.internal",
            "policy_version": "2026.Q3-v4"
        }
    }

    # Normalized lookup
    found_key = None
    for (t, s) in policy_catalog.keys():
        if t.lower() in clean_tier.lower() and s.lower() in clean_service.lower():
            found_key = (t, s)
            break

    if not found_key:
        # Fallback default policy for unlisted enterprise configurations
        return {
            "status": "success",
            "tier": clean_tier,
            "service": clean_service,
            "sla_threshold_mins": 60,
            "penalty_rate_per_min_usd": 10.00,
            "max_credit_cap_usd": 2000.00,
            "escalation_contact": "general-sla@cloudplatform.internal",
            "policy_version": "2026.Q4-default"
        }

    data = policy_catalog[found_key]
    return {
        "status": "success",
        "tier": found_key[0],
        "service": found_key[1],
        "sla_threshold_mins": data["sla_threshold_mins"],
        "penalty_rate_per_min_usd": data["penalty_rate_per_min_usd"],
        "max_credit_cap_usd": data["max_credit_cap_usd"],
        "escalation_contact": data["escalation_contact"],
        "policy_version": data["policy_version"]
    }


def compute_financial_adjustment(
    downtime_minutes: int,
    sla_threshold_mins: int,
    rate_per_min: float,
    max_cap: float
) -> Dict[str, Any]:
    """
    Computes precise financial adjustment without model arithmetic hallucination.
    """
    try:
        dt = int(downtime_minutes)
        thresh = int(sla_threshold_mins)
        rate = float(rate_per_min)
        cap = float(max_cap)
    except (ValueError, TypeError) as ex:
        return {
            "status": "error",
            "error_type": "InvalidNumericArguments",
            "message": f"All calculation inputs must be valid numbers: {ex}"
        }

    excess_minutes = max(0, dt - thresh)
    gross_credit = excess_minutes * rate
    net_credit = min(gross_credit, cap)
    cap_applied = gross_credit > cap

    # Generate cryptographic audit hash of input parameters & result
    audit_payload = f"{dt}:{thresh}:{rate}:{cap}:{net_credit}"
    audit_hash = "SHA256:" + hashlib.sha256(audit_payload.encode()).hexdigest()[:16].upper()

    return {
        "status": "success",
        "downtime_minutes": dt,
        "sla_threshold_mins": thresh,
        "excess_billable_minutes": excess_minutes,
        "rate_per_min_usd": round(rate, 2),
        "gross_credit_usd": round(gross_credit, 2),
        "max_credit_cap_usd": round(cap, 2),
        "cap_applied": cap_applied,
        "net_approved_credit_usd": round(net_credit, 2),
        "audit_verification_hash": audit_hash
    }


def record_credit_memo(
    idempotency_key: str,
    customer_id: str,
    ticket_id: str,
    net_credit_usd: float,
    manager_email: str
) -> Dict[str, Any]:
    """
    Records credit memo in the ledger with strict IDEMPOTENCY KEY protection.
    If the key was already processed, returns the existing record without double-crediting.
    """
    clean_key = (idempotency_key or "").strip()
    if not clean_key:
        clean_key = f"IDEM-{ticket_id}-{customer_id}"

    clean_cust = (customer_id or "").strip()
    clean_ticket = (ticket_id or "").strip()
    amount = float(net_credit_usd)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. IDEMPOTENCY CHECK: Has this exact request already been executed?
    cursor.execute("""
        SELECT idempotency_key, transaction_id, ticket_id, customer_id, amount_usd, manager_email, status, created_at
        FROM credit_ledger
        WHERE idempotency_key = ?;
    """, (clean_key,))
    existing = cursor.fetchone()

    if existing:
        conn.close()
        return {
            "status": "success",
            "idempotent_replay": True,
            "duplicate_prevented": True,
            "message": "Idempotent request recognized. Returning previously processed transaction receipt.",
            "transaction_id": existing[1],
            "ticket_id": existing[2],
            "customer_id": existing[3],
            "amount_credited_usd": existing[4],
            "manager_email": existing[5],
            "ledger_status": existing[6],
            "original_timestamp": existing[7]
        }

    # 2. Fresh Transaction: Generate unique transaction ID and execute atomically
    txn_id = f"TXN-CREDIT-{uuid.uuid4().hex[:8].upper()}"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    try:
        # Insert ledger record
        cursor.execute("""
            INSERT INTO credit_ledger (idempotency_key, transaction_id, ticket_id, customer_id, amount_usd, manager_email, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (clean_key, txn_id, clean_ticket, clean_cust, amount, manager_email, "POSTED", now_iso))

        # Update customer account balance
        cursor.execute("""
            UPDATE customers
            SET credit_balance_usd = credit_balance_usd + ?
            WHERE customer_id = ?;
        """, (amount, clean_cust))

        # Fetch updated customer balance
        cursor.execute("SELECT credit_balance_usd FROM customers WHERE customer_id = ?;", (clean_cust,))
        new_balance_row = cursor.fetchone()
        new_balance = new_balance_row[0] if new_balance_row else amount

        conn.commit()
    except Exception as ex:
        conn.rollback()
        conn.close()
        return {
            "status": "error",
            "error_type": "DatabaseError",
            "message": f"Failed to commit credit memo: {ex}"
        }

    conn.close()
    return {
        "status": "success",
        "idempotent_replay": False,
        "duplicate_prevented": False,
        "transaction_id": txn_id,
        "idempotency_key": clean_key,
        "ticket_id": clean_ticket,
        "customer_id": clean_cust,
        "amount_credited_usd": amount,
        "updated_customer_balance_usd": new_balance,
        "manager_email": manager_email,
        "ledger_status": "POSTED",
        "timestamp": now_iso
    }


def dispatch_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Central dispatcher executing tools safely with observation wrapping.
    """
    try:
        if tool_name == "lookup_incident_ticket":
            return lookup_incident_ticket(ticket_id=arguments.get("ticket_id", ""))
        elif tool_name == "fetch_service_policy":
            return fetch_service_policy(
                tier=arguments.get("tier", ""),
                service=arguments.get("service", "")
            )
        elif tool_name == "compute_financial_adjustment":
            return compute_financial_adjustment(
                downtime_minutes=arguments.get("downtime_minutes", 0),
                sla_threshold_mins=arguments.get("sla_threshold_mins", 0),
                rate_per_min=arguments.get("rate_per_min", 0.0),
                max_cap=arguments.get("max_cap", 0.0)
            )
        elif tool_name == "record_credit_memo":
            return record_credit_memo(
                idempotency_key=arguments.get("idempotency_key", ""),
                customer_id=arguments.get("customer_id", ""),
                ticket_id=arguments.get("ticket_id", ""),
                net_credit_usd=arguments.get("net_credit_usd", 0.0),
                manager_email=arguments.get("manager_email", "")
            )
        else:
            return {
                "status": "error",
                "error_type": "UnknownTool",
                "message": f"Tool '{tool_name}' is not recognized. Available tools: ['lookup_incident_ticket', 'fetch_service_policy', 'compute_financial_adjustment', 'record_credit_memo']."
            }
    except Exception as ex:
        return {
            "status": "error",
            "error_type": "ExecutionException",
            "message": f"Unexpected exception in '{tool_name}': {str(ex)}"
        }
