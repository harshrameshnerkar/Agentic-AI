"""Feature Freeze Policy Auditor.

Enforces zero-new-feature invariant during Day 19 Hardening, Documentation & Handover.
Validates commit messages, task classifications, and baseline freeze tags.
"""

from dataclasses import dataclass
import hashlib
import json
import os
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class FreezePolicy:
    """Encapsulates the signed-off freeze policy parameters."""
    release_tag: str
    baseline_commit: str
    effective_timestamp: str
    policy_status: str
    allowed_prefixes: List[str]
    disallowed_prefixes: List[str]
    zero_new_features: bool
    approved_backlog: List[Dict[str, Any]]


class FeatureFreezeAuditor:
    """Enforces and validates the feature freeze policy."""

    def __init__(self, policy_path: Optional[str] = None):
        if policy_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            policy_path = os.path.join(base_dir, "FREEZE_POLICY.json")
        self.policy_path = policy_path
        self.policy = self._load_policy()

    def _load_policy(self) -> FreezePolicy:
        """Load policy JSON from disk."""
        if not os.path.exists(self.policy_path):
            raise FileNotFoundError(f"Freeze policy file missing at: {self.policy_path}")

        with open(self.policy_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return FreezePolicy(
            release_tag=data.get("release_tag", "v1.0.0-rc1"),
            baseline_commit=data.get("baseline_commit", "728b238"),
            effective_timestamp=data.get("effective_timestamp", ""),
            policy_status=data.get("policy_status", "ACTIVE_FREEZE"),
            allowed_prefixes=data.get("allowed_commit_prefixes", []),
            disallowed_prefixes=data.get("disallowed_commit_prefixes", []),
            zero_new_features=data.get("rules", {}).get("zero_new_features", True),
            approved_backlog=data.get("approved_backlog", []),
        )

    def is_commit_allowed(self, commit_message: str) -> Tuple[bool, str]:
        """Validate if a proposed commit message complies with the freeze policy."""
        msg_clean = commit_message.strip().lower()

        # Check explicitly disallowed prefixes
        for prefix in self.policy.disallowed_prefixes:
            if msg_clean.startswith(prefix):
                return False, f"REJECTED: Prefix '{prefix}' introduces new functionality during feature freeze."

        # Check for feature keywords even without strict prefix
        forbidden_keywords = ["add feature", "implement feature", "new endpoint", "new api"]
        for kw in forbidden_keywords:
            if kw in msg_clean:
                return False, f"REJECTED: Commit mentions '{kw}', violating zero-new-feature rule."

        # Check against allowed prefixes
        matched_prefix = any(msg_clean.startswith(pref) for pref in self.policy.allowed_prefixes)
        if matched_prefix:
            return True, f"ALLOWED: Complies with freeze policy ({commit_message.split(':')[0]})."

        # Default fallback: reject unknown prefixes
        return False, f"REJECTED: Prefix must be one of {self.policy.allowed_prefixes} during feature freeze."

    def is_task_allowed(self, task_category: str) -> Tuple[bool, str]:
        """Validate if a task category is allowed during Day 19."""
        allowed_categories = {"FIX", "DOCS", "TEST", "HARDENING", "CHORE", "REFACTOR"}
        normalized = task_category.strip().upper()

        if normalized in allowed_categories:
            return True, f"ALLOWED: Task category '{normalized}' complies with fix-and-document freeze."
        return False, f"REJECTED: Task category '{normalized}' disallowed during feature freeze."

    def compute_policy_fingerprint(self) -> str:
        """Compute SHA-256 fingerprint of the current freeze policy."""
        with open(self.policy_path, "rb") as f:
            content = f.read()
        return hashlib.sha256(content).hexdigest()

    def audit_system_state(self) -> Dict[str, Any]:
        """Produce full audit status summary."""
        fingerprint = self.compute_policy_fingerprint()
        return {
            "policy_status": self.policy.policy_status,
            "release_tag": self.policy.release_tag,
            "baseline_commit": self.policy.baseline_commit,
            "zero_new_features_enforced": self.policy.zero_new_features,
            "policy_sha256": fingerprint,
            "approved_backlog_items": len(self.policy.approved_backlog),
            "allowed_categories": ["FIX", "DOCS", "TEST", "HARDENING", "CHORE", "REFACTOR"],
        }
