"""
Day 16 - Session 02: Constraints & Signed-Off Success Metrics
Demonstrates:
1. Secret masking and blacklist command enforcement.
2. Blast-radius classification and cryptographic HMAC token approvals.
3. Automated compliance evaluation.
"""

from __future__ import annotations
from constraints_validator import (
    SecretMasker,
    BlacklistEnforcer,
    BlastRadiusClassifier,
    CryptographicHITLGateway,
    ComplianceEvaluator,
)


def main():
    print("Day 16 Session 02: Operational Boundaries & Safety Constraints\n")

    # 1. Masking & Blacklist
    masked = SecretMasker.mask_string("Bearer sk-live-998877665544")
    print(f"Secret Masking: {masked}")
    assert "sk-live" not in masked

    blocked_cmd, reason = BlacklistEnforcer.is_blacklisted("rm -rf /var/log/*")
    print(f"Destructive Command Blocked: {blocked_cmd} ({reason})")
    assert blocked_cmd is True

    # 2. Blast Radius & HMAC
    tier = BlastRadiusClassifier.classify_action("restart_service", {"service": "payment-api"})
    print(f"Action Blast Radius Tier: {tier.value}")

    gateway = CryptographicHITLGateway()
    token = gateway.generate_approval_token("INC-801", "restart_service", "Lead SRE")
    is_valid = gateway.verify_approval_token(token, "INC-801", "restart_service")
    print(f"HMAC Approval Token Valid: {is_valid}")
    assert is_valid is True

    # 3. Compliance
    evaluator = ComplianceEvaluator()
    res = evaluator.run_all_checks()
    print(f"\nCompliance Result: {'100% COMPLIANT' if res['all_passed'] else 'FAILURES'}")


if __name__ == "__main__":
    main()
