"""
Day 18 - Session 2: Integration & Safety
Safety Guardrails: PII redaction engine, Blast Radius classifier, and HMAC-SHA256 approval gateway.
"""

import re
import hmac
import hashlib
import time
from typing import Dict, Any, List, Tuple


class PIISanitizer:
    """Detects and masks sensitive data (PII, credentials, tokens) before LLM or log exposure."""

    PATTERNS = [
        # SSN (XXX-XX-XXXX)
        (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_SSN]"),
        # Credit Card (13-16 digits with hyphens or spaces)
        (re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"), "[REDACTED_CREDIT_CARD]"),
        # Email address
        (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "[REDACTED_EMAIL]"),
        # JWT Token (eyJ...)
        (re.compile(r"\beyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\b"), "[REDACTED_JWT_TOKEN]"),
        # Generic API Secret / Password (password=..., secret=..., key=...)
        (re.compile(r"(?i)(password|secret|api_key|token)\s*[:=]\s*['\"]?([A-Za-z0-9\-_+=]{8,})['\"]?"), r"\1=[REDACTED_SECRET]")
    ]

    @classmethod
    def sanitize(cls, text: str) -> Tuple[str, int]:
        """Redacts all matching PII patterns and returns sanitized text plus redaction count."""
        sanitized = text
        redaction_count = 0
        for pattern, replacement in cls.PATTERNS:
            matches = len(pattern.findall(sanitized))
            if matches > 0:
                redaction_count += matches
                sanitized = pattern.sub(replacement, sanitized)
        return sanitized, redaction_count


class CryptographicHITLGateway:
    """
    Enforces cryptographic Human-In-The-Loop approval for Tier 3 consequential remediation actions.
    Uses HMAC-SHA256 signature verification with timestamp replay protection.
    """

    SECRET_KEY = b"enterprise-sre-hitl-secret-key-2026"
    MAX_CLOCK_SKEW_SEC = 300  # 5 minutes

    @classmethod
    def generate_approval_signature(cls, incident_id: str, action_command: str, approver_email: str, timestamp_epoch: int) -> str:
        """Generates an authentic HMAC-SHA256 signature for an authorized human SRE."""
        payload = f"{incident_id}:{action_command}:{approver_email}:{timestamp_epoch}".encode("utf-8")
        return hmac.new(cls.SECRET_KEY, payload, hashlib.sha256).hexdigest()

    @classmethod
    def verify_approval(
        cls,
        incident_id: str,
        action_command: str,
        approver_email: str,
        timestamp_epoch: int,
        provided_signature: str
    ) -> Tuple[bool, str]:
        """Verifies HMAC signature and protects against expiration/replay attacks."""
        current_epoch = int(time.time())
        if abs(current_epoch - timestamp_epoch) > cls.MAX_CLOCK_SKEW_SEC:
            return False, f"Signature expired or invalid timestamp (clock skew > {cls.MAX_CLOCK_SKEW_SEC}s)."

        expected_sig = cls.generate_approval_signature(incident_id, action_command, approver_email, timestamp_epoch)
        if not hmac.compare_digest(expected_sig, provided_signature):
            return False, "Cryptographic HMAC verification failed (unauthorized or tampered payload)."

        return True, "Signature verified successfully. Action authorized."


class BlastRadiusClassifier:
    """Classifies actions into Tier 1 (Read-Only), Tier 2 (Scoped Safe), Tier 3 (Consequential)."""

    TIER_3_KEYWORDS = [
        "rollback", "scale deployment", "kill query", "kill", "restart pod",
        "patch configmap", "revert corefile", "delete", "drop", "terminate"
    ]

    TIER_2_KEYWORDS = [
        "clean up /tmp", "flush cache", "resend", "logrotate", "trigger external secrets sync"
    ]

    @classmethod
    def classify_action(cls, action_text: str) -> str:
        act_lower = action_text.lower()
        for kw in cls.TIER_3_KEYWORDS:
            if kw in act_lower:
                return "Tier 3 (Consequential - HITL Required)"
        for kw in cls.TIER_2_KEYWORDS:
            if kw in act_lower:
                return "Tier 2 (Scoped Safe - Automated)"
        return "Tier 1 (Read-Only - Informational)"
