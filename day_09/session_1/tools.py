"""
Tool Registry with Least-Privilege Controls and Allow-Lists.
Demonstrates:
- Naive tool execution vs Hardened Least-Privilege enforcement.
- Strict recipient domain allow-lists for external communications.
- Audit logging of tool access attempts.
"""

from typing import Any, Dict, List
from rag_documents import retrieve_rag_document

ALLOWED_EMAIL_DOMAINS = ["@company.internal", "@corporate.internal"]


def tool_retrieve_documents(query: str) -> Dict[str, Any]:
    """Retrieves authoritative company documentation from the knowledge base."""
    doc = retrieve_rag_document(query, include_injection=True)
    return {
        "status": "SUCCESS",
        "doc_id": doc["doc_id"],
        "title": doc["title"],
        "document_text": doc["content"],
    }


def tool_delete_record_unprotected(table: str, record_id: str) -> Dict[str, Any]:
    """Unprotected destructive tool: Executes deletion without least-privilege checks."""
    return {
        "status": "DELETED",
        "table": table,
        "record_id": record_id,
        "warning": "CRITICAL: Database record was permanently deleted!",
    }


def tool_delete_record_hardened(table: str, record_id: str) -> Dict[str, Any]:
    """Hardened tool: Enforces Least-Privilege boundary. Knowledge QA agents have read-only permissions."""
    return {
        "status": "BLOCKED_BY_POLICY",
        "error": "AccessDenied: Write and delete operations are strictly prohibited for Knowledge QA agents under the Least-Privilege Policy.",
        "table": table,
        "record_id": record_id,
    }


def tool_send_email_unprotected(to: str, subject: str, body: str) -> Dict[str, Any]:
    """Unprotected dispatch: Blindly sends emails to arbitrary third-party addresses."""
    return {
        "status": "EMAIL_SENT",
        "recipient": to,
        "subject": subject,
        "body_preview": body[:80] + "...",
        "warning": "CRITICAL: Email dispatched to external address!",
    }


def tool_send_email_hardened(to: str, subject: str, body: str) -> Dict[str, Any]:
    """Hardened tool: Enforces strict recipient domain allow-lists."""
    is_allowed = any(to.lower().endswith(domain) for domain in ALLOWED_EMAIL_DOMAINS)
    if not is_allowed:
        return {
            "status": "BLOCKED_BY_ALLOWLIST",
            "error": f"Security Violation: Recipient '{to}' is not in the authorized corporate domain allow-list ({ALLOWED_EMAIL_DOMAINS}).",
            "attempted_recipient": to,
        }
    return {
        "status": "EMAIL_SENT",
        "recipient": to,
        "subject": subject,
        "body_preview": body[:80] + "...",
    }


SECURITY_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "retrieve_documents",
            "description": "Search the internal RAG knowledge base for company policies, technical standards, and procedures.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query keywords"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_record",
            "description": "Purge or delete records from internal database tables.",
            "parameters": {
                "type": "object",
                "properties": {
                    "table": {"type": "string", "description": "Target database table"},
                    "record_id": {"type": "string", "description": "Identifier of record to purge"}
                },
                "required": ["table", "record_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Dispatch notification emails to stakeholders or support channels.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "body": {"type": "string", "description": "Email text body"}
                },
                "required": ["to", "subject", "body"],
            },
        },
    },
]
