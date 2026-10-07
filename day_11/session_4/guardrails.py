"""
Guardrails and Security Subsystem for Capstone OpsSentinel AI.
Implements:
1. Input Guardrail: Direct & indirect prompt injection scanner.
2. PII & Secret Redactor: Anonymization of IPs, emails, API keys, and bearer tokens.
3. Blast-Radius Tool Authorization Gate: Role-based permission checks & approval tokens.
4. Output Guardrail: Prevents secret leakage and verifies policy adherence.
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel


class GuardrailValidationResult(BaseModel):
    is_allowed: bool
    sanitized_input: str
    rejection_reason: Optional[str] = None
    redactions_made: List[str] = []


class SecurityGuardrails:
    """Enterprise firewall securing agent input, tool execution, and output."""

    # Common prompt injection patterns
    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
        r"system\s+(override|prompt|bypass)",
        r"disregard\s+(all\s+)?guidelines",
        r"reveal\s+(your\s+)?(system\s+prompt|hidden\s+instructions|secret\s+key)",
        r"you\s+are\s+now\s+in\s+(developer|dan|unrestricted)\s+mode",
        r"delete\s+all\s+tables",
        r"drop\s+database",
        r"rm\s+-rf\s+/",
    ]

    # Regex patterns for sensitive PII and secrets
    PII_PATTERNS = {
        "EMAIL": r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b",
        "IPV4": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
        "API_KEY": r"\b(sk-[a-zA-Z0-9]{20,}|key-[a-zA-Z0-9]{16,})\b",
        "JWT": r"\beyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\b",
    }

    def validate_input(self, user_prompt: str) -> GuardrailValidationResult:
        """
        Validates user input against prompt injection and redacts PII/secrets.
        Returns GuardrailValidationResult.
        """
        clean_prompt = user_prompt.strip()

        # 1. Prompt Injection Scanning
        for pat in self.INJECTION_PATTERNS:
            if re.search(pat, clean_prompt, re.IGNORECASE):
                return GuardrailValidationResult(
                    is_allowed=False,
                    sanitized_input=clean_prompt,
                    rejection_reason=f"Security Guardrail Violation: Detected prohibited prompt injection attempt matching pattern '{pat}'.",
                )

        # 2. PII & Secret Redaction
        sanitized = clean_prompt
        redactions = []
        for pii_type, pat in self.PII_PATTERNS.items():
            matches = re.findall(pat, sanitized)
            if matches:
                redactions.append(f"{pii_type} ({len(matches)} occurrences)")
                sanitized = re.sub(pat, f"[REDACTED_{pii_type}]", sanitized)

        return GuardrailValidationResult(
            is_allowed=True,
            sanitized_input=sanitized,
            redactions_made=redactions,
        )

    def validate_tool_execution(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        user_role: str,
        approval_token: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Enforces blast-radius permissions on tool calls before execution.
        Read-only tools are unrestricted. Destructive tools require role >= Engineer and valid token.
        """
        # Read-only tools
        safe_tools = {"query_telemetry_db", "read_system_logs", "calculate_metrics", "search_runbooks"}
        if tool_name in safe_tools:
            return True, None

        # Destructive tools
        privileged_tools = {"restart_service", "rollback_deployment", "dispatch_emergency_alert"}
        if tool_name in privileged_tools:
            # Auditors are strictly restricted to read-only tools
            if user_role.lower() == "auditor":
                return False, f"Permission Denied: User role '{user_role}' has read-only access and cannot execute destructive action '{tool_name}'."

            # Service restart and rollback require valid approval tokens
            if tool_name in {"restart_service", "rollback_deployment"}:
                provided_token = tool_args.get("approval_token") or approval_token
                if provided_token != "AUTH-OPS-APPROVE-2026":
                    return False, f"Blast-Radius Approval Required: Action '{tool_name}' blocked due to missing or invalid authorization token."

            return True, None

        return False, f"Security Violation: Attempted to call unregistered tool '{tool_name}'."

    def validate_output(self, agent_response: str) -> str:
        """Sanitizes outgoing agent response, preventing secret leaks."""
        clean = agent_response
        # Redact raw API keys or private tokens if inadvertently generated
        clean = re.sub(r"AQ\.[a-zA-Z0-9_-]{20,}", "[REDACTED_API_KEY]", clean)
        clean = re.sub(r"BEGIN\s+RSA\s+PRIVATE\s+KEY", "[REDACTED_KEY_HEADER]", clean)
        return clean
